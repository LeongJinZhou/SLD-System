"""Google Workspace identity; directory attributes never grant application privileges."""
import base64
import hashlib
import json
import os
import re
import secrets
import urllib.parse
import urllib.request
from datetime import datetime, timezone

DOMAIN = 'qiu.edu.my'


def now():
    return datetime.now(timezone.utc).isoformat()


def configured():
    return bool(os.getenv('GOOGLE_CLIENT_ID') and os.getenv('GOOGLE_CLIENT_SECRET'))


def missing_configuration():
    return [key for key in ('GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET','SLD_ADMIN_EMAILS') if not os.getenv(key)]


def directory_enabled():
    return os.getenv('GOOGLE_DIRECTORY_ENABLED', '').lower() == 'true'


def university_email(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@qiu\.edu\.my", value, re.IGNORECASE))


def begin_login(base_url):
    pending = {'state': secrets.token_urlsafe(32), 'nonce': secrets.token_urlsafe(32), 'verifier': secrets.token_urlsafe(48)}
    challenge = base64.urlsafe_b64encode(hashlib.sha256(pending['verifier'].encode()).digest()).rstrip(b'=').decode()
    scope = 'openid email profile'
    if directory_enabled():
        scope += ' https://www.googleapis.com/auth/directory.readonly'
    query = {'client_id': os.environ['GOOGLE_CLIENT_ID'], 'redirect_uri': base_url + '/auth/callback',
             'response_type': 'code', 'scope': scope, 'state': pending['state'], 'nonce': pending['nonce'],
             'code_challenge': challenge, 'code_challenge_method': 'S256', 'hd': DOMAIN, 'prompt': 'select_account'}
    return 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(query), pending


def search_directory(token, query):
    params = urllib.parse.urlencode({'query': query, 'readMask': 'names,emailAddresses,photos,organizations,externalIds',
                                    'sources': 'DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE', 'pageSize': 30})
    request = urllib.request.Request('https://people.googleapis.com/v1/people:searchDirectoryPeople?' + params,
                                     headers={'Authorization': 'Bearer ' + token})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response).get('people', [])


def list_directory(token):
    """Read all pages before callers replace their stored directory snapshot."""
    people, page_token, seen = [], '', set()
    for _ in range(100):
        params = {'readMask': 'names,emailAddresses,photos,organizations,externalIds',
                  'sources': ['DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE', 'DIRECTORY_SOURCE_TYPE_DOMAIN_CONTACT'], 'pageSize': 1000}
        if page_token:
            params['pageToken'] = page_token
        request = urllib.request.Request('https://people.googleapis.com/v1/people:listDirectoryPeople?' + urllib.parse.urlencode(params, doseq=True),
                                         headers={'Authorization': 'Bearer ' + token})
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.load(response)
        people.extend(result.get('people', []))
        if len(people) > 50000:
            raise ValueError('Directory exceeds the current import limit.')
        page_token = result.get('nextPageToken', '')
        if not page_token:
            return people
        if page_token in seen:
            raise ValueError('Directory returned a repeated pagination token.')
        seen.add(page_token)
    raise ValueError('Directory pagination did not complete.')


def safe_photo(value, preview=False):
    if preview and isinstance(value, str) and re.fullmatch(r'/web/avatars/[a-z]+\.svg', value):
        return value
    if not isinstance(value, str):
        return ''
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme == 'https' and parsed.hostname and (parsed.hostname == 'googleusercontent.com' or parsed.hostname.endswith('.googleusercontent.com')) and not parsed.username:
        return value
    return ''


def student_id_fields(value):
    match = re.fullmatch(r'QIU-(\d{4})(\d{2})-(\d{6})', value or '')
    if not match or not 1 <= int(match[1]) <= 9999 or not 1 <= int(match[2]) <= 12:
        return {'intake_year': None, 'intake_month': None, 'student_id_last4': '', 'student_id_valid': False}
    return {'intake_year': int(match[1]), 'intake_month': int(match[2]), 'student_id_last4': match[3][-4:], 'student_id_valid': True}


def map_person(person, email=None):
    emails = [item.get('value', '').lower() for item in person.get('emailAddresses', [])]
    university = next((v for v in emails if university_email(v)), '')
    names, photos = person.get('names', []), person.get('photos', [])
    organizations = person.get('organizations', [])
    org = next((v for v in organizations if v.get('metadata', {}).get('primary')), organizations[0] if organizations else {})
    external = person.get('externalIds', [])
    uid = next((v.get('value', '') for v in external if student_id_fields(v.get('value',''))['student_id_valid']),
               next((v.get('value', '') for v in external if v.get('type') in ('organization', 'account', 'custom')), ''))
    title = org.get('title', '')
    kind = org.get('jobDescription', '')
    # Only explicit provider classification is captured; programme is not inferred from email/name.
    title_kind = {'student': 'Student', 'qiu student': 'Student', 'staff': 'Staff', 'qiu staff': 'Staff', 'employee': 'Staff'}
    person_type = kind if kind.lower() in ('student', 'staff', 'employee') else title_kind.get(title.strip().lower(), '')
    return {'name': names[0].get('displayName', '') if names else '', 'email': email or university,
            'photo': safe_photo(photos[0].get('url', '')) if photos else '', 'university_id': uid,
            'person_type': person_type, 'programme': org.get('department', '') if person_type.lower() == 'student' else '',
            'department': org.get('department', ''), 'directory_title': title}


def complete_login(code, pending, base_url):
    from google.auth.transport.requests import Request
    from google.oauth2 import id_token
    payload = urllib.parse.urlencode({'code': code, 'client_id': os.environ['GOOGLE_CLIENT_ID'],
                                    'client_secret': os.environ['GOOGLE_CLIENT_SECRET'], 'code_verifier': pending['verifier'],
                                    'redirect_uri': base_url + '/auth/callback', 'grant_type': 'authorization_code'}).encode()
    request = urllib.request.Request('https://oauth2.googleapis.com/token', payload)
    with urllib.request.urlopen(request, timeout=15) as response:
        tokens = json.load(response)
    claims = id_token.verify_oauth2_token(tokens['id_token'], Request(), os.environ['GOOGLE_CLIENT_ID'])
    if (claims.get('nonce') != pending['nonce'] or claims.get('email_verified') is not True
            or claims.get('hd') != DOMAIN or not university_email(claims.get('email'))):
        raise ValueError('A verified QIU Google Workspace account is required.')
    user = {'id': claims['sub'], 'name': claims.get('name', ''), 'email': claims['email'].lower(),
            'photo': safe_photo(claims.get('picture', '')), 'university_id': '', 'person_type': '', 'programme': '', 'department': '',
            'directory_title':'', 'directory_status': 'not_enabled', 'profile_source': 'Google verified identity', 'captured_at': now()}
    token = tokens.get('access_token', '')
    if directory_enabled():
        try:
            matches = search_directory(token, user['email'])
            match = next((v for v in matches if user['email'] in [e.get('value', '').lower() for e in v.get('emailAddresses', [])]), None)
            if match:
                mapped = map_person(match, user['email'])
                user.update({key: value for key, value in mapped.items() if value})
                user.update(directory_status='captured', profile_source='Google verified identity + Workspace directory')
            else:
                user['directory_status'] = 'not_found'
        except Exception:
            user['directory_status'] = 'unavailable'
    admins = {e.strip().lower() for e in os.getenv('SLD_ADMIN_EMAILS', '').split(',') if e.strip()}
    user['role'] = 'sld' if user['email'] in admins else 'student'
    if user['role'] == 'sld' or user.get('person_type', '').lower() in ('staff', 'employee'):
        user['programme'] = ''
    user['preview'] = False
    return user, token


PREVIEW_PEOPLE = [
    {'id': 'preview-student', 'name': 'Demo Student', 'email': 'demo.student@qiu.edu.my', 'university_id': 'DEMO-001', 'person_type': 'Student', 'programme': 'Demo programme', 'role': 'student'},
    {'id': 'preview-advisor', 'name': 'Demo Advisor', 'email': 'demo.advisor@qiu.edu.my', 'university_id': 'DEMO-ADVISOR', 'person_type': 'Staff', 'department': 'Demo faculty', 'role': 'advisor'},
    {'id': 'preview-sld', 'name': 'Demo SLD Officer', 'email': 'demo.sld@qiu.edu.my', 'university_id': 'DEMO-SLD', 'person_type': 'Staff', 'department': 'Student Life Division', 'role': 'sld'},
    {'id': 'preview-vice', 'name': 'Demo Vice President', 'email': 'demo.vice@qiu.edu.my', 'university_id': 'DEMO-002', 'person_type': 'Student', 'role': 'student'},
    {'id': 'preview-secretary', 'name': 'Demo Secretary', 'email': 'demo.secretary@qiu.edu.my', 'university_id': 'DEMO-003', 'person_type': 'Student', 'role': 'student'},
    {'id': 'preview-treasurer', 'name': 'Demo Treasurer', 'email': 'demo.treasurer@qiu.edu.my', 'university_id': 'DEMO-004', 'person_type': 'Student', 'role': 'student'},
    {'id': 'preview-visitor', 'name': 'Demo Student Visitor', 'email': 'demo.visitor@qiu.edu.my', 'university_id': 'DEMO-005', 'person_type': 'Student', 'role': 'student'},
]


def preview_user(persona):
    aliases = {'student': 0, 'president': 0, 'advisor': 1, 'sld': 2, 'vice': 3, 'vice_president': 3, 'secretary': 4, 'treasurer': 5, 'visitor':6, 'ordinary_student':6}
    user = PREVIEW_PEOPLE[aliases[persona]].copy() if persona in aliases else None
    if not user:
        raise ValueError('Unknown preview persona.')
    avatar = ['student','advisor','sld','vice','secretary','treasurer','visitor'][aliases[persona]]
    user.update(preview=True, photo='/web/avatars/' + avatar + '.svg', captured_at=now(), directory_status='preview_fixture', profile_source='Fictional local preview')
    if persona in ('sld', 'advisor'):
        user['programme'] = ''
    return user


for _index, _person in enumerate(PREVIEW_PEOPLE):
    _person['photo'] = '/web/avatars/' + ['student','advisor','sld','vice','secretary','treasurer','visitor'][_index] + '.svg'
    if _person['person_type'] == 'Student':
        _person['university_id'] = 'QIU-202610-' + str(_index + 1).zfill(6)
        _person.setdefault('programme', 'Demo programme')
