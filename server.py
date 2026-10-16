"""Local SLD pilot server. Real deployments require HTTPS reverse proxy and university setup."""
import argparse
import copy
import base64
import json
import hashlib
import io
import mimetypes
import math
import os
from pathlib import Path
import re
import secrets
import sqlite3
import socket
import sys
import threading
import time
import uuid
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, date, time as datetime_time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qs, urlsplit, quote

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '.vendor'))
import auth
import storage
import notifications
import club_reports
import profiles
import withdrawals
import performance
from contextlib import contextmanager
from catalogs import SDGS

PROPOSAL_FIELDS = frozenset(('club_id', 'title', 'summary', 'date', 'end_date', 'start_time', 'end_time',
    'venue', 'mode', 'environment', 'nature', 'nature_other', 'cca_participants', 'cca_committee', 'sdgs',
    'collaboration', 'collaboration_club_ids', 'collaboration_other', 'collaboration_other_enabled', 'funding_source', 'introduction', 'objectives', 'target_count', 'eligibility',
    'activities', 'itinerary', 'ict', 'ict_required', 'logistics', 'logistics_required', 'transport', 'departure_time', 'pickup_point',
    'return_time', 'return_pickup', 'committee', 'revenue', 'expenses', 'conclusion'))
MYT = timezone(timedelta(hours=8))


def event_start(proposal):
    """Planned input is Malaysia local time; recorded submission time is server UTC."""
    if not proposal.get('title', '').strip():
        raise APIError('Enter the event title before submitting.', fields={'title':'Enter the event title.'})
    def planned_date(value):
        if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            raise ValueError()
        return date.fromisoformat(value)
    def planned_time(value):
        if not isinstance(value, str) or not re.fullmatch(r'\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?', value):
            raise ValueError()
        return datetime_time.fromisoformat(value)
    try:
        day = planned_date(proposal.get('date', ''))
        start = datetime.combine(day, planned_time(proposal.get('start_time', '')), MYT)
        end_day = planned_date(proposal['end_date']) if proposal.get('end_date') else day
        if end_day < day:
            raise APIError('Event end date must not precede its start date.')
        if proposal.get('end_time'):
            end = datetime.combine(end_day, planned_time(proposal['end_time']), MYT)
            if end < start:
                raise APIError('Event end must not precede its start.')
        return start
    except ValueError:
        raise APIError('Enter valid event dates (YYYY-MM-DD) and a start time (HH:MM) before submitting.', fields={'date':'Check the event dates.', 'start_time':'Check the event start time.'})


def event_end(proposal, start):
    if not proposal.get('end_time'):
        raise APIError('Enter the event end time before submitting so the approved calendar has a complete schedule.', fields={'end_time':'Enter the event end time.'})
    # event_start validates the optional end fields before this conversion.
    end = datetime.combine(date.fromisoformat(proposal.get('end_date') or proposal['date']),
                           datetime_time.fromisoformat(proposal['end_time']), MYT)
    if end <= start:
        raise APIError('The event must end after its start.')
    return end


def derived_duration(proposal):
    try:
        start = event_start(dict(proposal,title=proposal.get('title') or 'Draft'))
        seconds = int((event_end(proposal,start)-start).total_seconds())
        if seconds <= 0:
            return {'duration':'','duration_seconds':None}
    except (APIError,ValueError,TypeError,AttributeError,KeyError,OverflowError):
        return {'duration':'','duration_seconds':None}
    remainder=seconds
    labels=[]
    for size,label in ((86400,'day'),(3600,'hour'),(60,'minute'),(1,'second')):
        number,remainder=divmod(remainder,size)
        if number:
            labels.append(str(number)+' '+label+('s' if number!=1 else ''))
    return {'duration':' '.join(labels),'duration_seconds':seconds}


class APIError(Exception):
    def __init__(self, message, status=400, code=None, fields=None):
        self.status = status
        self.code = code or {400: 'VALIDATION_ERROR', 401: 'SESSION_EXPIRED', 403: 'ACCESS_DENIED', 404: 'RECORD_NOT_FOUND',
                             409: 'REVISION_CONFLICT', 413: 'REQUEST_TOO_LARGE', 415: 'UNSUPPORTED_CONTENT_TYPE', 503: 'SERVICE_UNAVAILABLE'}.get(status, 'REQUEST_FAILED')
        self.fields = fields or {}
        super().__init__(message)


def validate_sdgs(value):
    if not isinstance(value, list) or any(not isinstance(v, str) or v not in {option['id'] for option in SDGS} for v in value) or len(set(value)) != len(value):
        raise APIError('Select unique Sustainable Development Goals from 1 to 17.', fields={'sdgs': 'Choose unique SDG numbers 1–17.'})
    return value


def proposal_progress(proposal):
    fields = [('title', 'Event title'), ('summary', 'Event summary'), ('venue', 'Venue'), ('introduction', 'Introduction'),
              ('eligibility', 'Target audience'), ('conclusion', 'Conclusion')]
    checklist = [{'field': key, 'label': label, 'complete': isinstance(proposal.get(key), str) and bool(proposal[key].strip())} for key, label in fields]
    objectives = proposal.get('objectives', [])
    if isinstance(objectives, str):
        objectives = [line.strip() for line in objectives.splitlines() if line.strip()]
    checklist.append({'field':'objectives','label':'At least two distinct objectives','complete': isinstance(objectives,list) and len(objectives)>=2 and all(isinstance(value,str) and bool(value.strip()) for value in objectives) and len({value.strip().casefold() for value in objectives}) == len(objectives)})
    for key, label in [('date', 'Event date'), ('start_time', 'Start time'), ('end_time', 'End time')]:
        checklist.append({'field': key, 'label': label, 'complete': bool(proposal.get(key))})
    try:
        start = event_start(dict(proposal, title=proposal.get('title') or 'Draft'))
        event_end(proposal, start)
    except (APIError, ValueError):
        for entry in checklist:
            if entry['field'] in ('date', 'start_time', 'end_time'):
                entry['complete'] = False
    try:
        count_valid = int(str(proposal.get('target_count', ''))) > 0
    except ValueError:
        count_valid = False
    checklist.append({'field': 'target_count', 'label': 'Expected participants', 'complete': count_valid})
    try:
        sdgs_complete = bool(validate_sdgs(proposal.get('sdgs', [])))
    except APIError:
        sdgs_complete = False
    checklist.append({'field': 'sdgs', 'label': 'Sustainable Development Goals (optional)', 'required': False, 'complete': sdgs_complete})
    for key, label, required in [('activities', 'Planned activities', ('name', 'description')), ('itinerary', 'Programme itinerary', ('start','end','agenda')),
                                  ('committee', 'Organising responsibilities', ('email','name','role','responsibility'))]:
        rows = proposal.get(key, [])
        complete = isinstance(rows, list) and bool(rows) and all(isinstance(row, dict) and all(isinstance(row.get(field), str) and bool(row[field].strip()) for field in required) for row in rows)
        checklist.append({'field': key, 'label': label, 'complete': complete})
    if any(str(value).casefold()=='others' for value in proposal.get('nature',[]) if isinstance(value,str)):
        checklist.append({'field':'nature_other','label':'Other event nature','complete':bool(str(proposal.get('nature_other','')).strip())})
    if proposal.get('collaboration_other_enabled'):
        checklist.append({'field':'collaboration_other','label':'Other collaboration','complete':bool(str(proposal.get('collaboration_other','')).strip())})
    if str(proposal.get('mode','Physical')).casefold()!='virtual':
        if proposal.get('logistics_required',True):
            checklist.append({'field':'logistics','label':'Logistics requirements','complete':bool(str(proposal.get('logistics','')).strip())})
    if proposal.get('ict_required',True):
        checklist.append({'field':'ict','label':'ICT requirements','complete':bool(str(proposal.get('ict','')).strip())})
    for field,label in [('revenue','Revenue rows'),('expenses','Expense rows')]:
        rows=proposal.get(field,[])
        if rows:
            complete=isinstance(rows,list)
            for row in rows if isinstance(rows,list) else []:
                try:
                    price,quantity=Decimal(str(row.get('price',''))),Decimal(str(row.get('quantity','')))
                    complete=complete and isinstance(row.get('description'),str) and bool(row['description'].strip()) and price.is_finite() and quantity.is_finite() and price>=0 and quantity>0
                except (AttributeError,InvalidOperation,TypeError,ValueError):
                    complete=False
            checklist.append({'field':field,'label':label,'complete':bool(complete)})
    for entry in checklist:
        entry['step']=1 if entry['field'] in ('activities','itinerary','committee','ict','logistics') else (2 if entry['field'] in ('conclusion','revenue','expenses') else 0)
    required = [entry for entry in checklist if entry.get('required', True)]
    completed = sum(entry['complete'] for entry in required)
    return {'completed': completed, 'total': len(required), 'percent': round(completed / len(required) * 100), 'checklist': checklist}


def image(value, required=False, signature=False):
    if not value and not required:
        return ''
    if not isinstance(value, str) or len(value) > 2_800_000:
        raise APIError('Image must be under 2 MB.')
    match = re.fullmatch(r'data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)', value)
    if not match or (signature and match[1] != 'png'):
        raise APIError('Upload a PNG, JPEG or WebP image; signatures must be PNG.')
    try:
        raw = base64.b64decode(match[2], validate=True)
    except ValueError:
        raise APIError('Invalid image encoding.')
    valid = {'png': raw.startswith(b'\x89PNG\r\n\x1a\n'), 'jpeg': raw.startswith(b'\xff\xd8\xff'),
             'webp': raw.startswith(b'RIFF') and raw[8:12] == b'WEBP'}
    if len(raw) > 2 * 1024 * 1024 or not valid[match[1]]:
        raise APIError('Image content or size is invalid.')
    if signature:
        try:
            from PIL import Image
            with Image.open(io.BytesIO(raw)) as drawing:
                if drawing.format!='PNG' or drawing.width*drawing.height>4_000_000 or drawing.width<8 or drawing.height<8:
                    raise ValueError()
                drawing.load()
                rgba=drawing.convert('RGBA')
                white=Image.new('RGBA',rgba.size,'white')
                white.alpha_composite(rgba)
                sample=white.convert('L');sample.thumbnail((256,256))
                if sum(count for shade,count in enumerate(sample.histogram()) if shade<245)<10:
                    raise ValueError()
        except Exception:
            raise APIError('Draw a visible signature in a valid PNG image.',fields={'signature':'Draw your signature before signing.'})
    return value


def text(value, limit=5000):
    if not isinstance(value, str) or len(value) > limit:
        raise APIError('Text field is invalid or too long.')
    return value.strip()


def bounded(value, depth=0):
    if depth > 6:
        raise APIError('Form structure is too deep.')
    if isinstance(value, dict):
        if len(value) > 80 or any(not isinstance(k, str) or len(k) > 100 for k in value):
            raise APIError('Too many form fields.')
        return {k: bounded(v, depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        if len(value) > 100:
            raise APIError('At most 100 rows are supported per section.')
        return [bounded(v, depth + 1) for v in value]
    if isinstance(value, str):
        return text(value, 20000)
    if isinstance(value, float) and not math.isfinite(value):
        raise APIError('Numeric fields must be finite.')
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise APIError('Invalid field value.')


def validate_club(data, submit=False):
    if not isinstance(data, dict):
        raise APIError('Club form is required.')
    club = {key: text(data.get(key, ''), 10000 if key == 'bio' else 250)
            for key in ('name', 'category', 'bio', 'semester', 'advisor_email')}
    club['advisor_email'] = club['advisor_email'].lower()
    club['logo'] = image(data.get('logo', ''))
    entries = data.get('committee', [])
    if not isinstance(entries, list) or len(entries) > 30:
        raise APIError('Committee must contain at most 30 positions.')
    club['committee'] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise APIError('Invalid committee entry.')
        member = {key: text(entry.get(key, ''), 250) for key in ('position', 'name', 'email', 'university_id')}
        member['email'] = member['email'].lower()
        if member['email'] and not auth.university_email(member['email']):
            raise APIError('Committee members must use QIU email addresses.')
        club['committee'].append(member)
    if club['advisor_email'] and not auth.university_email(club['advisor_email']):
        raise APIError('Advisor must use a QIU email address.')
    if submit:
        if any(not club[k] for k in ('name', 'bio', 'logo', 'semester', 'advisor_email')):
            raise APIError('Complete club name, biography, logo, semester and advisor before submitting.')
        roles = [m['position'].lower() for m in club['committee']]
        required = ('president', 'vice president', 'secretary', 'treasurer')
        if any(roles.count(role) != 1 for role in required):
            raise APIError('Exactly one President, Vice President, Secretary and Treasurer is required.')
        if any(not m['name'] or not m['email'] or not m['position'] for m in club['committee']):
            raise APIError('Complete name, QIU email and position for every committee member.')
        if len({m['email'] for m in club['committee']}) != len(club['committee']):
            raise APIError('Each committee position must have a distinct officer.')
        if club['advisor_email'] in {m['email'] for m in club['committee']}:
            raise APIError('The advisor cannot be a committee officer.')
    return club


class App:
    def __init__(self, db_path, preview=False, base_url='http://127.0.0.1:8765'):
        self.preview, self.base_url = preview, base_url.rstrip('/')
        self.db = storage.connect(db_path, preview)
        self.lock = getattr(self.db, 'lock', threading.RLock())
        self.sessions = {}

    @contextmanager
    def mutation(self):
        with self.lock:
            if isinstance(self.db, storage.MySQLStore):
                with self.db.mutation():
                    yield
            else:
                yield

    def get(self, kind, record_id):
        with self.lock:
            row = self.db.execute('SELECT data FROM records WHERE kind=? AND id=?', (kind, record_id)).fetchone()
        if not row:
            raise APIError('Record not found.', 404)
        record=json.loads(row[0])
        return self.effective_club(record) if kind=='club' else record

    def all(self, kind):
        with self.lock:
            records=[json.loads(row[0]) for row in self.db.execute('SELECT data FROM records WHERE kind=? ORDER BY rowid DESC', (kind,))]
            return [self.effective_club(r) for r in records] if kind=='club' else records

    def effective_club(self, record):
        handover=record.get('committee_handover')
        if not handover:return record
        record=copy.deepcopy(record)
        now=datetime.fromisoformat(auth.now());deadline=datetime.fromisoformat(handover['ends_at'])
        if now>=deadline:
            record['committee']=copy.deepcopy(handover['incoming'])
            record['owner_email']=next((m['email'] for m in record['committee'] if m['position'].lower()=='president'),'')
            record['pending_incoming_committee']=[];record['handover_status']='completed'
        else:
            outgoing=copy.deepcopy(handover['outgoing']);emails={m['email'] for m in outgoing}
            record['committee']=outgoing+[dict(m,position='Pending '+m['position']) for m in handover['incoming'] if m['email'] not in emails]
            record['pending_incoming_committee']=copy.deepcopy(handover['incoming']);record['handover_status']='overlap'
        return record

    def put(self, kind, record):
        with self.lock:
            self.db.execute('INSERT OR REPLACE INTO records VALUES (?,?,?)', (kind, record['id'], json.dumps(record)))
            self.db.commit()

    def put_batch(self, records):
        """Consume an authorization and create its club in one transaction."""
        with self.lock, self.db:
            for kind, record in records:
                self.db.execute('INSERT OR REPLACE INTO records VALUES (?,?,?)', (kind, record['id'], json.dumps(record)))

    def log(self, user, action, record_id='', club_id=None):
        entry = {'timestamp': auth.now(), 'actor': user['email'], 'actor_name': user.get('name', ''), 'action': action, 'record_id': record_id}
        if club_id:
            entry['club_id'] = club_id
        with self.lock:
            cursor = self.db.execute('INSERT INTO logs(data) VALUES (?)', (json.dumps(entry),))
            try:
                notifications.emit(self, user, entry, cursor.lastrowid)
            except APIError as error:
                if error.status!=404:
                    raise
                # Legacy audit entries can reference removed records; no notification can be safely linked.
            self.db.commit()

    def assigned_roles(self, club, user):
        roles = [m['position'] for m in club['committee'] if m['email'] == user['email']]
        if club['advisor_email'] == user['email']:
            roles.append('Advisor')
        return roles

    def event_roles(self, proposal, user):
        return [person.get('role','Event committee') for person in proposal.get('committee',[]) if person.get('email') == user['email']]

    def proposal_visible(self, proposal, club, user):
        return self.visible(club,user) or bool(self.event_roles(proposal,user))

    def proposal_editable(self, proposal, club, user):
        return club['status']=='approved' and proposal['status'] in ('draft','returned') and (self.editable(club,user) or bool(self.event_roles(proposal,user)))

    def committee_identities(self, rows, club):
        identities = {p['email']:p for p in self.all('directory_identity') + self.all('user') + self.contacts()}
        for officer in club['committee']:
            identities.setdefault(officer['email'],officer)
        result, emails = [], set()
        for row in rows:
            email = text(row.get('email',''),250).lower()
            if email:
                if not auth.university_email(email):
                    raise APIError('Event committee members must use QIU email addresses.',fields={'committee':'Choose a QIU directory identity.'})
                if email in emails:
                    raise APIError('An event committee identity cannot be listed twice.',fields={'committee':'Remove duplicate committee identities.'})
                emails.add(email)
            identity = identities.get(email,{})
            result.append({'email':email,'name':identity.get('name',''),'university_id':identity.get('university_id',''),
                           'role':text(row.get('role',''),250),'responsibility':text(row.get('responsibility',''),5000)})
        return result

    def canonical_proposal(self, proposal, strict=False):
        result=dict(proposal,**derived_duration(proposal))
        mode=proposal.get('mode','Physical')
        if not strict and mode in ('Indoor','Outdoor'):
            result['environment']=mode
            mode='Physical'
        if mode not in ('Physical','Virtual'):
            raise APIError('Choose Physical or Virtual for the event mode.',fields={'mode':'Choose a valid event mode.'})
        result['mode']=mode
        environment=proposal.get('environment','Indoor')
        if environment not in ('Indoor','Outdoor'):
            raise APIError('Choose Indoor or Outdoor for the event setting.',fields={'environment':'Choose a valid event setting.'})
        result['environment']=environment
        for flag in ('ict_required','logistics_required'):
            value=proposal.get(flag,True)
            if type(value) is not bool:
                raise APIError('Event support choices must be yes or no.',fields={flag:'Choose yes or no.'})
            result[flag]=value
        nature=proposal.get('nature',[])
        if not isinstance(nature,list) or any(not isinstance(value,str) for value in nature):
            raise APIError('Event nature must be a list of selections.',fields={'nature':'Choose event nature options.'})
        if 'Others' not in nature:
            result['nature_other']=''
        catalog={club['id']:club['name'] for club in self.all('club') if club['status']=='approved'}
        structured=any(key in proposal for key in ('collaboration_club_ids','collaboration_other','collaboration_other_enabled'))
        if structured:
            selected=proposal.get('collaboration_club_ids',[])
            if not isinstance(selected,list) or any(not isinstance(value,str) or value not in catalog for value in selected) or len(set(selected))!=len(selected):
                raise APIError('Choose distinct approved clubs for collaboration.',fields={'collaboration_club_ids':'Choose registered approved clubs.'})
            if proposal.get('club_id') in selected:
                raise APIError('Choose other clubs as collaborators; the organising club is already recorded.',fields={'collaboration_club_ids':'Select another club.'})
            enabled=proposal.get('collaboration_other_enabled',False)
            if type(enabled) is not bool:
                raise APIError('Other collaboration must be enabled or disabled.',fields={'collaboration_other_enabled':'Choose yes or no.'})
            other=text(proposal.get('collaboration_other',''),5000) if enabled else ''
        else:
            selected=[]
            other=text(proposal.get('collaboration',''),5000)
            enabled=bool(other)
        result.update(collaboration_club_ids=selected,collaboration_other_enabled=enabled,collaboration_other=other,
                      collaboration='; '.join([catalog[value] for value in selected]+([other] if other else [])))
        if str(result.get('mode','Physical')).casefold()=='virtual':
            result.update(logistics_required=False)
            for field in ('logistics','transport','departure_time','pickup_point','return_time','return_pickup'):
                result[field]=''
        return result

    def contact(self, person):
        photo = auth.safe_photo(person.get('photo', ''), self.preview)
        record = {key: str(person.get(key, '')) for key in ('name', 'email', 'university_id', 'programme', 'department', 'person_type')}
        record.update(id=record['email'].lower(), email=record['email'].lower(), photo=photo, photo_status='available' if photo else 'missing',
                      source='Fictional local preview' if self.preview else 'Google Workspace directory', imported_at=auth.now())
        record['student_id'] = record['university_id']
        record.update(auth.student_id_fields(record['university_id']))
        return record

    def contacts(self):
        records = self.all('contact')
        return records if records or not self.preview else [self.contact(p) for p in auth.PREVIEW_PEOPLE]

    def import_contacts(self, people):
        records = {p['email']: self.contact(p) for p in people if auth.university_email(p.get('email'))}
        with self.lock, self.db:
            self.db.execute("DELETE FROM records WHERE kind='contact'")
            for record in records.values():
                self.db.execute('INSERT INTO records VALUES (?,?,?)', ('contact', record['id'], json.dumps(record)))
        return len(records)

    def query_contacts(self, filters, offset=0, limit=50):
        records = self.contacts()
        q = filters.get('q', '').casefold()
        for key in ('intake_year', 'intake_month'):
            if filters.get(key) and not filters[key].isdigit():
                raise APIError('Intake filters must be numeric.', fields={key: 'Enter a valid intake number.'})
        if filters.get('student_id') and not auth.student_id_fields(filters['student_id'])['student_id_valid']:
            raise APIError('Use the complete student ID QIU-YYYYMM-000000.', fields={'student_id': 'Enter the full student ID.'})
        emails = None
        if filters.get('club_id'):
            club = self.get('club', filters['club_id'])
            emails = {m['email'] for m in club['committee']} | {club['advisor_email']}
        options = sorted({p['programme'] for p in records if p['programme']})
        result = [p for p in records if (not q or q in ' '.join(str(p.get(k, '')) for k in ('name','email','student_id','programme','department')).casefold())
                  and (not filters.get('programme') or p['programme'].casefold() == filters['programme'].casefold())
                  and (not filters.get('student_id') or p['student_id'] == filters['student_id'])
                  and (emails is None or p['email'] in emails)
                  and all(not filters.get(k) or str(p.get(k)) == filters[k] for k in ('intake_year','intake_month'))]
        result.sort(key=lambda p: (p['name'].casefold(), p['email']))
        return {'contacts': result[offset:offset + limit], 'total': len(result), 'offset': offset, 'limit': limit, 'programme_options': options}

    def calendar_events(self, user):
        if not user:
            return []
        club_ids = {c['id'] for c in self.all('club') if self.assigned_roles(c, user)}
        event_ids={p['id'] for p in self.all('proposal') if self.event_roles(p,user)}
        return [event for event in self.all('calendar_event') if user['role'] == 'sld' or event['club_id'] in club_ids or event['proposal_id'] in event_ids]

    def activity(self, user, offset=0, limit=50, club_id='', record_id='', grouped=False, group_key=''):
        if not user:
            return {'entries': [], 'total': 0, 'offset': offset, 'limit': limit}
        clubs = {c['id']: c for c in self.all('club')}
        assigned = {cid for cid, club in clubs.items() if self.assigned_roles(club, user)}
        proposal_clubs = {p['id']: p['club_id'] for p in self.all('proposal')}
        event_ids = {p['id'] for p in self.all('proposal') if self.event_roles(p,user)}
        report_records={r['id']:r for r in self.all('club_report')}
        report_clubs={rid:r['club_id'] for rid,r in report_records.items()}
        withdrawal_records={r['id']:r for r in self.all('withdrawal')}
        grant_clubs = {g['id']: g.get('club_id') for g in self.all('registration_grant')}
        users = {u['email']: u.get('name', '') for u in self.all('user')}
        labels = {'login_profile_captured': 'Signed in and refreshed university profile',
                  'preview_login_profile_captured': 'Signed in to local preview', 'logout': 'Signed out',
                  'club_registration_authorized': 'Authorized club registration', 'club_draft_saved': 'Saved club registration',
                  'club_submitted': 'Submitted club registration', 'club_approve': 'Approved club registration stage',
                  'club_return': 'Returned club registration for correction', 'club_sld_review_opened': 'Opened SLD registration review',
                  'club_profile_export_pdf': 'Exported club profile (PDF)',
                  'proposal_draft_saved': 'Saved event proposal', 'proposal_submitted': 'Submitted event proposal',
                  'proposal_advisor_approve': 'Advisor endorsed event proposal', 'proposal_sld_approve': 'SLD approved event proposal',
                  'proposal_return': 'Returned event proposal for correction', 'event_proposal_policy_updated': 'Updated proposal submission policy'}
        labels.update(club_report_draft_saved='Saved club activity report',club_report_submitted='President signed and submitted report',club_report_secretary_approved='Secretary signed report',club_report_advisor_approved='Advisor signed report',club_report_sld_approved='SLD approved club report',club_report_returned='Returned club report for correction',club_report_handover_applied='Applied approved AGM committee handover')
        labels.update(withdrawal_draft_saved='Saved withdrawal draft',withdrawal_submit='Treasurer signed withdrawal request',withdrawal_approve='Signed withdrawal review',withdrawal_return='Returned withdrawal for correction',withdrawal_finance_document='Uploaded Finance signed approval',withdrawal_receipt_document='Uploaded bank-in receipt',withdrawal_all_approve='SLD verified withdrawal approval package',withdrawal_receive='Treasurer confirmed fund receipt',withdrawal_acknowledge='SLD acknowledged fund receipt')
        labels.update(directory_contacts_imported='Imported university contacts',
                      late_submission_permission_granted='Granted temporary late-submission permission',
                      late_submission_permission_revoked='Revoked late-submission permission')
        with self.lock:
            rows = [(row[0], json.loads(row[1])) for row in self.db.execute('SELECT id,data FROM logs ORDER BY id DESC')]
        entries = []
        for log_id, row in rows:
            row_record_id = row.get('record_id', '')
            cid = row.get('club_id') or (row_record_id if row_record_id in clubs else proposal_clubs.get(row_record_id) or report_clubs.get(row_record_id) or grant_clubs.get(row_record_id))
            if user['role'] != 'sld' and cid not in assigned and row_record_id not in event_ids:
                continue
            if club_id and club_id != cid or record_id and record_id != row.get('record_id'):
                continue
            action = row.get('action', '')
            record_type = 'proposal' if row_record_id in proposal_clubs else ('club_report' if row_record_id in report_clubs else ('club' if row_record_id in clubs else 'system'))
            if row_record_id in withdrawal_records:record_type='withdrawal'
            entry_group_key = record_type + ':' + (row_record_id or action)
            if group_key and group_key != entry_group_key:
                continue
            summary = labels.get(action, 'Recorded club activity')
            if action.startswith('proposal_export_'):
                summary = 'Exported event proposal (' + action.rsplit('_', 1)[-1].upper() + ')'
            entries.append({'id': log_id, 'timestamp': row['timestamp'], 'actor': row.get('actor', ''),
                            'actor_name': row.get('actor_name') or users.get(row.get('actor')) or row.get('actor', ''),
                            'club_id': cid, 'club_name': clubs.get(cid, {}).get('name', ''), 'action': action,
                            'record_id': row_record_id, 'summary': summary, 'group_key': entry_group_key})
        if grouped:
            groups = {}
            proposals = {p['id']: p for p in self.all('proposal')}
            for entry in entries:
                rid = entry['record_id']
                kind = 'proposal' if rid in proposals else ('club_report' if rid in report_records else ('club' if rid in clubs else 'system'))
                if rid in withdrawal_records:kind='withdrawal'
                key = entry['group_key']
                if key not in groups:
                    groups[key] = {'key': key, 'record_type': kind, 'record_id': rid, 'title': proposals.get(rid, {}).get('title') or report_records.get(rid,{}).get('title') or withdrawal_records.get(rid,{}).get('purpose') or clubs.get(rid, {}).get('name') or entry['summary'],
                                   'club_id': entry['club_id'], 'club_name': entry['club_name'], 'count': 0, 'latest_at': entry['timestamp'], 'summary': entry['summary']}
                groups[key]['count'] += 1
            result = list(groups.values())
            return {'groups': result[offset:offset + limit], 'total': len(result), 'offset': offset, 'limit': limit}
        return {'entries': entries[offset:offset + limit], 'total': len(entries), 'offset': offset, 'limit': limit}

    def visible(self, club, user):
        return user['role'] == 'sld' or club['owner_email'] == user['email'] or club['advisor_email'] == user['email'] or any(m['email'] == user['email'] for m in club['committee'])

    def editable(self, club, user):
        return user['role'] == 'sld' or club['owner_email'] == user['email'] or any(m['email'] == user['email'] for m in club['committee'])

    def registration_editable(self, club, user):
        return self.editable(club, user) and club['status'] in ('draft', 'returned', 'pending_advisor', 'pending_sld') and not club.get('sld_review_started_at')

    def decorate_club(self, club, user):
        complete = sum(bool(club.get(k)) for k in ('name', 'bio', 'logo', 'semester', 'advisor_email'))
        emails = [m['email'] for m in club['committee'] if m.get('email')]
        for role in ('president', 'vice president', 'secretary', 'treasurer'):
            entries = [m for m in club['committee'] if m['position'].lower() == role]
            complete += int(len(entries) == 1 and bool(entries[0]['name']) and bool(entries[0]['email']) and emails.count(entries[0]['email']) == 1)
        contacts = {p['email']: p for p in self.all('user')}
        contacts.update({p['email']: p for p in self.contacts()})
        club_people = []
        for person in club['committee'] + [{'position': 'Advisor', 'email': club['advisor_email']}]:
            contact = contacts.get(person['email'], {})
            club_people.append({key: contact.get(key) or person.get(key, '') for key in ('name','email','university_id','photo','programme','department','person_type')} | {'position': person['position']})
        return dict(club, club_people=club_people, can_edit=self.registration_editable(club, user), can_edit_proposals=club['status'] == 'approved' and self.editable(club, user),
                    assigned_roles=self.assigned_roles(club, user),
                    progress={'completed': complete, 'total': 9, 'percent': round(complete / 9 * 100)},
                    can_create_reports=club['status']=='approved' and club_reports.committee(user,club),
                    can_create_withdrawals=club['status']=='approved' and club_reports.committee(user,club),
                    locked=bool(club.get('sld_review_started_at')),
                    reviewing={'started_at': club.get('sld_review_started_at'), 'reviewer_email': club.get('sld_review_started_by')})

    def snapshot(self, club):
        snapshot = {k: v for k, v in club.items() if k not in ('history', 'submitted_digest', 'submitted_revision')}
        digest = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
        club['submitted_revision'] = club['revision']
        club['submitted_digest'] = digest
        self.put('club_version', {'id': club['id'] + '-r' + str(club['revision']), 'snapshot': snapshot, 'digest': digest})
        return {'revision': club['submitted_revision'], 'digest': digest}

    def settings(self):
        records = self.all('system_settings')
        settings = next((record.copy() for record in records if record['id'] == 'operational'),
                        {'event_proposal_lead_days': 14, 'revision': 0})
        if 'event_proposal_lead_days' not in settings:
            settings['event_proposal_lead_days'] = settings.pop('event_proposal_lead_weeks', 2) * 7
        settings.setdefault('handover_days',7);settings.setdefault('transfer_days',14)
        return settings

    def preparer_profile(self, club, user, proposal=None):
        if not user:
            return None
        positions=[m.get('position','') for m in club['committee'] if m.get('email')==user['email'] and m.get('position','').lower() in ('president','vice president')]
        if len(positions)!=1:
            return None
        return dict(name=user.get('name') or 'Unavailable',designation=((next((m.get('role') for m in (proposal or {}).get('committee',[]) if m.get('email')==user['email'] and m.get('role')),None)) or (club['name']+' · '+positions[0])),department=club['name'],email=user['email'])

    def available_signer_profile(self, email):
        profile={}
        for person in self.contacts()+self.all('directory_identity')+self.all('user'):
            if person.get('email')==email:
                profile.update({key:person[key] for key in ('name','directory_title','department') if person.get(key)})
        return profile

    def advisor_profile(self, club):
        email=club['advisor_email']
        profile=self.available_signer_profile(email)
        return dict(name=profile.get('name') or 'Unavailable',designation=profile.get('directory_title') or 'Club Advisor',department=profile.get('department') or 'Unavailable',email=email)

    def reviewer_profile(self, user, slot):
        profile=self.available_signer_profile(user['email'])
        return dict(name=user.get('name') or 'Unavailable',designation=user.get('directory_title') or profile.get('directory_title') or ('Club Advisor' if slot=='advisor' else 'SLD Officer'),department=user.get('department') or profile.get('department') or 'Unavailable',email=user['email'])

    def decorate_proposal(self, proposal, user, club):
        proposal=self.canonical_proposal(proposal)
        if proposal.get('submitted_revision') is not None:
            try:
                proposal['submitted_snapshot']=self.get('proposal_version',proposal['id']+'-r'+str(proposal['submitted_revision']))['snapshot']
            except APIError:
                proposal['submitted_snapshot']=None
        progress = proposal_progress(proposal)
        step_errors={str(step):{item['field']:item['label']+' is incomplete.' for item in progress['checklist'] if item['step']==step and item.get('required',True) and not item['complete']} for step in range(3)}
        return dict(proposal, progress=progress, field_errors={item['field']: item['label'] + ' is incomplete.' for item in progress['checklist'] if item.get('required', True) and not item['complete']},
                    step_errors=step_errors,
                    can_edit=bool(user and self.proposal_editable(proposal,club,user)),
                    can_submit=bool(user and club['status']=='approved' and proposal['status'] in ('draft','returned') and self.preparer_profile(club,user,proposal)),
                    preparer_profile=self.preparer_profile(club,user,proposal),
                    reviewer_profile=self.reviewer_profile(user,'advisor' if club['advisor_email']==user['email'] else 'sld') if user and (club['advisor_email']==user['email'] or user['role']=='sld') else None,
                    can_manage_committee=bool(user and self.editable(club,user)), assigned_event_roles=self.event_roles(proposal,user) if user else [])

    def bootstrap(self, session):
        import exports
        user = session.get('user')
        if user and (user['role'] == 'sld' or user.get('person_type', '').lower() in ('staff', 'employee')):
            user = dict(user, programme='')
        clubs = [c for c in self.all('club') if user and self.visible(c, user)]
        clubs = [self.decorate_club(c, user) for c in clubs]
        ids = {c['id'] for c in clubs}
        club_by_id = {c['id']: c for c in self.all('club')}
        proposals = [self.decorate_proposal(p, user, club_by_id[p['club_id']]) for p in self.all('proposal') if user and p['club_id'] in club_by_id and self.proposal_visible(p,club_by_id[p['club_id']],user)]
        event_clubs = [dict(id=c['id'],name=c['name'],status=c['status'],can_edit_proposals=False) for c in club_by_id.values() if c['id'] not in ids and any(p['club_id']==c['id'] for p in proposals)]
        grants = [g for g in self.all('registration_grant') if user and (user['role'] == 'sld' or user['email'] in (g['president_email'], g['advisor_email']))]
        logs = self.activity(user, limit=100)['entries']
        reports=club_reports.list_for(self,user) if user else []
        return {'api_version': '1.7', 'auth': {'configured': auth.configured(), 'missing_configuration':auth.missing_configuration(), 'preview': self.preview, 'pdf_available': exports.pdf_available()},
                'club_reports':reports, 'withdrawals':withdrawals.list_for(self,user) if user else [], 'agm_tracker':club_reports.annual_tracker(self,user,datetime.fromisoformat(auth.now()).astimezone(MYT).year) if user and user['role']=='sld' else None, 'notifications_unread_count': notifications.list_for(self,user,0,1)['unread_count'] if user else 0, 'user': user, 'csrf': session['csrf'], 'clubs': clubs, 'event_clubs':event_clubs, 'proposals': proposals, 'logs': logs,
                'collaboration_clubs':[{'id':club['id'],'name':club['name']} for club in self.all('club') if user and club['status']=='approved'],
                'registration_grants': grants, 'settings': self.settings(), 'server_time': auth.now(), 'calendar_events': self.calendar_events(user), 'sdg_options': SDGS,
                'deadline_exceptions': [record for record in self.all('deadline_exception') if user and (user['role'] == 'sld' or record['id'] in ids)],
                'dashboard': {'report_pending_secretary':sum(r['status']=='pending_secretary' for r in reports), 'report_pending_advisor':sum(r['status']=='pending_advisor' for r in reports), 'report_pending_sld':sum(r['status']=='pending_sld' for r in reports), 'clubs': len(clubs), 'approved_clubs': sum(c['status'] == 'approved' for c in clubs),
                              'pending_advisor': sum(c['status'] == 'pending_advisor' for c in clubs),
                              'pending_sld': sum(c['status'] in ('pending_sld', 'reviewing_sld') for c in clubs),
                              'draft_clubs': sum(c['status'] == 'draft' for c in clubs),
                              'returned_clubs': sum(c['status'] == 'returned' for c in clubs),
                              'available_grants': sum(g['status'] == 'available' for g in grants),
                              'proposal_drafts': sum(p['status'] == 'draft' for p in proposals),
                              'submitted_proposals': sum(p['status'] != 'draft' for p in proposals),
                              'registration_progress': round(sum(c['progress']['percent'] for c in clubs) / len(clubs)) if clubs else 0,
                              'updated_at': max([c['updated_at'] for c in clubs] + [p['updated_at'] for p in proposals] + [g.get('updated_at', g['created_at']) for g in grants], default=None)},
                'directory': {'enabled': auth.directory_enabled(), 'status': user.get('directory_status') if user else 'signed_out'}}


class Handler(BaseHTTPRequestHandler):
    server_version = 'QIU-SLD'

    def log_message(self, format, *args):
        # Do not log OAuth codes, tokens, query strings or submitted personal data.
        print('%s %s' % (self.command, urlsplit(self.path).path.encode('unicode_escape').decode()))

    @property
    def app(self):
        return self.server.app

    def session(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie', ''))
        except Exception:
            pass
        key = cookie['sld_session'].value if 'sld_session' in cookie else ''
        with self.app.lock:
            # Sessions contain short-lived Google access tokens: discard expired entries on every request.
            current_time = time.time()
            for expired_key in [session_key for session_key, value in self.app.sessions.items() if value['expires'] < current_time]:
                del self.app.sessions[expired_key]
            session = self.app.db.load_session(key) if isinstance(self.app.db,storage.MySQLStore) and key else self.app.sessions.get(key)
            if not session:
                key = secrets.token_urlsafe(32)
                session = {'csrf': secrets.token_urlsafe(32), 'expires': time.time() + 8 * 3600}
                self.app.sessions[key] = session
            self.session_key = key
            self.current_session = session
        return session

    def persist_session(self):
        if isinstance(self.app.db,storage.MySQLStore) and hasattr(self,'current_session'):
            self.app.db.save_session(self.session_key,self.current_session)
            self.app.db.flush()

    def response_headers(self, status, mimetype='application/json; charset=utf-8', length=None, disposition=None):
        if status<500:
            self.persist_session()
        self.send_response(status)
        self.send_header('Content-Type', mimetype)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; style-src-attr 'unsafe-inline'; img-src 'self' data: https://lh3.googleusercontent.com https://*.googleusercontent.com; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        if hasattr(self, 'session_key'):
            secure = '; Secure' if self.app.base_url.startswith('https://') else ''
            self.send_header('Set-Cookie', 'sld_session=' + self.session_key + '; Path=/; HttpOnly; SameSite=Lax' + secure)
        if length is not None:
            self.send_header('Content-Length', str(length))
        if disposition:
            fallback = re.sub(r'[^A-Za-z0-9_. -]', '_', disposition)
            self.send_header('Content-Disposition', 'attachment; filename="' + fallback + '"; filename*=UTF-8\'\'' + quote(disposition))
        self.end_headers()

    def json(self, value, status=200):
        raw = json.dumps(value, allow_nan=False).encode()
        self.response_headers(status, length=len(raw))
        self.wfile.write(raw)

    def redirect(self, target):
        self.persist_session()
        self.send_response(302)
        self.send_header('Location', target)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Set-Cookie', 'sld_session=' + self.session_key + '; Path=/; HttpOnly; SameSite=Lax' + ('; Secure' if self.app.base_url.startswith('https://') else ''))
        self.send_header('Content-Length', '0')
        self.end_headers()

    def require_user(self, session):
        if not session.get('user'):
            raise APIError('Your session has expired. Sign in again to continue; your saved work remains available.', 401)
        return session['user']

    def verify_mutation_session(self, session):
        """Called after the shared mutation lock, so queued requests cannot outlive logout."""
        persisted=self.app.db.load_session(self.session_key) if isinstance(self.app.db,storage.MySQLStore) else self.app.sessions.get(self.session_key)
        if not persisted or persisted.get('expires',0)<=time.time():
            self.require_user({})
        user=self.require_user(persisted)
        if not secrets.compare_digest(persisted['csrf'],session['csrf']):
            raise APIError('Your session changed. Sign in again to continue.',401)
        session['user']=user
        return user

    def bound_grant(self, club, grant):
        """SLD assigns identity; the president completes remaining profile information."""
        if club['name'] != grant['club_name'] or club['advisor_email'] != grant['advisor_email'] or club['semester'] != grant['semester']:
            raise APIError('Club name, advisor and semester must match the SLD authorization.', 403)
        presidents = [m for m in club['committee'] if m['position'].lower() == 'president']
        if len(presidents) != 1 or presidents[0]['email'] != grant['president_email']:
            raise APIError('The President must remain the identity authorized by SLD.', 403)

    def do_GET(self):
        try:
            session = self.session()
            path = urlsplit(self.path).path
            query = parse_qs(urlsplit(self.path).query)
            if path == '/api/bootstrap':
                return self.json(self.app.bootstrap(session))
            if path in ('/auth/google/start', '/auth/google'):
                if not auth.configured():
                    raise APIError('Google Workspace login is not configured yet.', 503)
                target, pending = auth.begin_login(self.app.base_url)
                pending['expires'] = time.time() + 600
                session['oauth'] = pending
                return self.redirect(target)
            if path == '/auth/callback':
                pending = session.pop('oauth', None)
                if not pending or pending['expires'] < time.time() or not secrets.compare_digest(query.get('state', [''])[0], pending['state']):
                    raise APIError('Login expired or could not be verified. Please sign in again.', 401)
                try:
                    user, token = auth.complete_login(query.get('code', [''])[0], pending, self.app.base_url)
                except Exception:
                    raise APIError('Google login failed. Verify your QIU account and university OAuth setup.', 401)
                self.rotate_session(session)
                session.update(user=user, token=token)
                self.app.put('user', user)
                self.app.log(user, 'login_profile_captured')
                return self.redirect('/')
            user = self.require_user(session) if path.startswith('/api/') else None
            if user and (ROOT / 'finance.py').is_file():
                import finance
                try:
                    result = finance.handle_get(self.app,user,path,query)
                except finance.FinanceError as error:
                    raise APIError(str(error),getattr(error,'status',400),getattr(error,'code',None),getattr(error,'fields',None))
                if result is not None:
                    if isinstance(result,tuple):
                        raw,mime,filename=result
                        self.response_headers(200,mime,len(raw),filename)
                        self.wfile.write(raw)
                        return
                    return self.json(result)
            for module in (profiles,club_reports,performance,withdrawals):
                result=module.handle_get(self.app,user,path,query)
                if result is not None:
                    if isinstance(result,tuple):
                        raw,mime,filename=result;self.response_headers(200,mime,len(raw),filename);self.wfile.write(raw);return
                    return self.json(result)
            if (ROOT/'evidence.py').is_file():
                import evidence
                result=evidence.handle_get(self.app,user,path,query)
                if result is not None:
                    if isinstance(result,tuple):
                        raw,mime,filename=result;self.response_headers(200,mime,len(raw),filename);self.wfile.write(raw);return
                    return self.json(result)
            if (ROOT/'assistant.py').is_file():
                import assistant
                result=assistant.handle_get(self.app,user,path,query)
                if result is not None:return self.json(result)
            if path == '/api/notifications':
                try:
                    offset,limit=int(query.get('offset',['0'])[0]),int(query.get('limit',['25'])[0])
                except ValueError:
                    raise APIError('Notification pagination must use whole numbers.')
                if offset<0 or not 1<=limit<=100:
                    raise APIError('Notification pagination is out of range.')
                return self.json(notifications.list_for(self.app,user,offset,limit))
            if path == '/api/activity':
                try:
                    offset, limit = int(query.get('offset', ['0'])[0]), int(query.get('limit', ['50'])[0])
                except ValueError:
                    raise APIError('Activity pagination must use whole numbers.')
                if offset < 0 or not 1 <= limit <= 100:
                    raise APIError('Activity offset must be nonnegative and limit must be 1 to 100.')
                return self.json(self.app.activity(user, offset, limit, text(query.get('club_id',[''])[0],100), text(query.get('record_id',[''])[0],100), query.get('grouped',['0'])[0] == '1', text(query.get('group_key',[''])[0],200)))
            if path == '/api/contacts':
                if user['role'] != 'sld':
                    raise APIError('Only SLD can browse the university contacts catalogue.', 403)
                try:
                    offset, limit = int(query.get('offset', ['0'])[0]), int(query.get('limit', ['50'])[0])
                except ValueError:
                    raise APIError('Contacts pagination must use whole numbers.')
                if offset < 0 or not 1 <= limit <= 100:
                    raise APIError('Contacts offset must be nonnegative and limit must be 1 to 100.')
                filters = {key: text(query.get(key, [''])[0], 250) for key in ('q','programme','student_id','club_id','intake_year','intake_month')}
                return self.json(self.app.query_contacts(filters, offset, limit))
            if path == '/api/calendar/export':
                import calendar_export
                raw = calendar_export.calendar_ics(self.app.calendar_events(user))
                if isinstance(raw, str):
                    raw = raw.encode('utf-8')
                self.response_headers(200, 'text/calendar; charset=utf-8', len(raw), 'qiu-club-events.ics')
                self.wfile.write(raw)
                return
            club_export = re.fullmatch(r'/api/clubs/([a-zA-Z0-9_-]+)/export', path)
            if club_export:
                club = self.app.get('club', club_export[1])
                if not self.app.visible(club, user):
                    raise APIError('You cannot export this club profile.', 403)
                if query.get('format', ['pdf'])[0] != 'pdf':
                    raise APIError('Club profile export supports PDF.')
                import exports
                raw = exports.club_pdf(club)
                self.response_headers(200, 'application/pdf', len(raw), 'club-profile.pdf')
                self.wfile.write(raw)
                self.app.log(user, 'club_profile_export_pdf', club['id'])
                return
            if path == '/api/directory':
                q = text(query.get('q', [''])[0], 100)
                if len(q) < 2:
                    return self.json({'people': []})
                if self.app.preview:
                    people = [dict(p, preview=True, profile_source='Fictional local preview') for p in auth.PREVIEW_PEOPLE if q.lower() in (p['name'] + ' ' + p['email']).lower()]
                    return self.json({'people': people})
                if not auth.directory_enabled():
                    raise APIError('University directory integration is not enabled.', 503)
                try:
                    people = [auth.map_person(p) for p in auth.search_directory(session.get('token', ''), q)]
                    people = [p for p in people if auth.university_email(p['email'])]
                    self.app.put_batch([('directory_identity',dict(p,id=p['email'])) for p in people])
                    return self.json({'people': people})
                except Exception:
                    raise APIError('University directory is unavailable or permission was not granted.', 503)
            match = re.fullmatch(r'/api/proposals/([a-zA-Z0-9_-]+)/export', path)
            if match:
                proposal = self.app.get('proposal', match[1])
                proposal = self.app.canonical_proposal(proposal)
                club = self.app.get('club', proposal['club_id'])
                if not self.app.proposal_visible(proposal,club,user):
                    raise APIError('You cannot access this proposal.', 403)
                fmt = query.get('format', ['docx'])[0]
                if fmt not in ('docx', 'pdf', 'xlsx'):
                    raise APIError('Unsupported export format.')
                import exports
                raw, filename, mime = exports.export_proposal(proposal, dict(club,advisor_profile=self.app.advisor_profile(club)), user, fmt)
                self.response_headers(200, mime, len(raw), filename)
                self.wfile.write(raw)
                self.app.log(user, 'proposal_export_' + fmt, proposal['id'], club['id'])
                return
            static = {'/': ROOT / 'web/index.html', '/tokens.css': ROOT / 'tokens.css', '/setup/google':ROOT / 'docs/google-setup.html', '/setup/google.css':ROOT / 'docs/google-setup.css'}
            if path not in static and re.fullmatch(r'/(?:web/)?[a-zA-Z0-9_-]+\.(?:js|css|svg|png|ico)', path):
                static[path] = ROOT / 'web' / path.rsplit('/', 1)[-1]
            if re.fullmatch(r'/web/avatars/(student|advisor|sld|vice|secretary|treasurer|visitor)\.svg', path):
                static[path] = ROOT / 'web' / 'avatars' / path.rsplit('/', 1)[-1]
            file = static.get(path)
            if not file or not file.is_file():
                raise APIError('Not found.', 404)
            raw = file.read_bytes()
            self.response_headers(200, mimetypes.guess_type(str(file))[0] or 'application/octet-stream', len(raw))
            self.wfile.write(raw)
        except APIError as error:
            self.json({'error': str(error), 'code': error.code, 'fields': error.fields}, error.status)
        except storage.StorageError:
            self.json({'error':'Database unavailable. Your request was not confirmed; retry shortly.','code':'DATABASE_UNAVAILABLE','fields':{}},503)
        except (ValueError, RuntimeError) as error:
            self.json({'error': 'The request could not be completed. Check the selected fields and try again.', 'code': 'VALIDATION_ERROR', 'fields': {}}, 400)
        except Exception:
            self.json({'error': 'Unable to complete request. Check local configuration.', 'code':'INTERNAL_ERROR','fields':{}}, 500)

    def rotate_session(self, session):
        with self.app.lock:
            if isinstance(self.app.db,storage.MySQLStore):
                self.app.db.revoke_session(self.session_key)
            self.app.sessions.pop(self.session_key, None)
            self.session_key = secrets.token_urlsafe(32)
            session['csrf'] = secrets.token_urlsafe(32)
            self.app.sessions[self.session_key] = session
            self.current_session = session

    def do_POST(self):
        try:
            session = self.session()
            path = urlsplit(self.path).path
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                raise APIError('Invalid request size.')
            if not 0 < length <= 4_000_000:
                raise APIError('Request must be under 4 MB.', 413)
            # Drain bounded normal bodies before sending a rejection: unread bytes can cause a Windows TCP reset.
            raw_body = self.rfile.read(length)
            if path != '/api/preview/login':
                self.require_user(session)
            if self.headers.get('Origin') != self.app.base_url or not secrets.compare_digest(self.headers.get('X-CSRF-Token', ''), session['csrf']):
                raise APIError('Request verification failed. Reload the page and try again.', 403)
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                raise APIError('JSON request required.', 415)
            try:
                data = json.loads(raw_body, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            except (ValueError, UnicodeDecodeError):
                raise APIError('Invalid JSON request.')
            if not isinstance(data, dict):
                raise APIError('Invalid request.')
            path = urlsplit(self.path).path
            if path=='/api/assistant/query' and (ROOT/'assistant.py').is_file():
                with self.app.mutation():
                    user=self.verify_mutation_session(session)
                import assistant
                identity=(user['email'],user['role'])
                result=assistant.handle_post(self.app,user,path,data)
                if result is not None:
                    with self.app.mutation():
                        refreshed=self.verify_mutation_session(session)
                        if (refreshed['email'],refreshed['role'])!=identity:
                            raise APIError('Your session changed. Sign in again to continue.',401)
                        return self.json(result)
            # MySQL acquires its database-wide mutation lock before workflow reads.
            if path == '/api/contacts/import':
                user = self.require_user(session)
                if user['role'] != 'sld':
                    raise APIError('Only SLD can import university contacts.', 403)
                if self.app.preview:
                    people = auth.PREVIEW_PEOPLE
                else:
                    if not auth.directory_enabled() or not session.get('token'):
                        raise APIError('Google directory access is not configured. Sign in with the approved university directory permission.', 503, 'DIRECTORY_UNAVAILABLE')
                    try:
                        people = [auth.map_person(person) for person in auth.list_directory(session['token'])]
                    except Exception:
                        raise APIError('University directory import could not complete. Existing contacts were retained; check access and sign in again if the Google token expired.', 503, 'DIRECTORY_IMPORT_FAILED')
                with self.app.mutation():
                    user=self.verify_mutation_session(session)
                    if user['role']!='sld':
                        raise APIError('Only SLD can import university contacts.',403)
                    count = self.app.import_contacts(people)
                    self.app.log(user, 'directory_contacts_imported')
                    return self.json({'imported': count, **self.app.query_contacts({}, limit=50)})
            with self.app.mutation():
                if path!='/api/preview/login':
                    self.verify_mutation_session(session)
                if path == '/api/preview/login':
                    if not self.app.preview:
                        raise APIError('Preview login is disabled.', 404)
                    user = auth.preview_user(data.get('persona'))
                    self.rotate_session(session)
                    session['user'] = user
                    self.app.put('user', user)
                    self.app.log(user, 'preview_login_profile_captured')
                    return self.json(self.app.bootstrap(session))
                user = self.require_user(session)
                if (ROOT/'assistant.py').is_file():
                    import assistant
                    result=assistant.handle_post(self.app,user,path,data)
                    if result is not None:return self.json(result)
                result=withdrawals.handle_post(self.app,user,path,data)
                if result is not None:return self.json(result)
                if (ROOT/'evidence.py').is_file():
                    import evidence
                    result=evidence.handle_post(self.app,user,path,data)
                    if result is not None:return self.json(result)
                result=club_reports.handle_post(self.app,user,path,data)
                if result is not None:return self.json(result)
                notification_route = re.fullmatch(r'/api/notifications/([a-zA-Z0-9_-]+)/read',path)
                if notification_route:
                    return self.json(notifications.mark_read(self.app,user,notification_route[1]))
                if (ROOT / 'finance.py').is_file():
                    import finance
                    try:
                        result = finance.handle_post(self.app,user,path,data)
                    except finance.FinanceError as error:
                        raise APIError(str(error),getattr(error,'status',400),getattr(error,'code',None),getattr(error,'fields',None))
                    if result is not None:
                        return self.json(result)
                if path == '/api/logout':
                    self.app.log(user, 'logout')
                    session.clear()
                    session.update(csrf=secrets.token_urlsafe(32), expires=time.time() + 8 * 3600)
                    self.rotate_session(session)
                    return self.json(self.app.bootstrap(session))
                if path == '/api/settings':
                    if user['role'] != 'sld':
                        raise APIError('Only SLD can change submission policies.', 403)
                    previous = self.app.settings()
                    if data.get('revision') != previous['revision']:
                        raise APIError('The policy changed. Reload the latest settings.', 409)
                    days = data.get('event_proposal_lead_days',previous['event_proposal_lead_days'])
                    if type(days) is not int or not 1 <= days <= 365:
                        raise APIError('Proposal lead time must be an integer from 1 to 365 days.', fields={'event_proposal_lead_days':'Enter a whole number from 1 to 365.'})
                    settings = {'id': 'operational', 'event_proposal_lead_days': days, 'revision': previous['revision'] + 1,
                                'updated_at': auth.now(), 'updated_by': user['email']}
                    for key in ('handover_days','transfer_days'):
                        value=data.get(key,previous[key])
                        if type(value) is not int or not 1<=value<=90:raise APIError('Policy days must be whole numbers from1 to90.',fields={key:'Enter1 to90days.'})
                        settings[key]=value
                    self.app.put('system_settings', settings)
                    self.app.log(user, 'event_proposal_policy_updated', 'operational')
                    return self.json({'settings': settings})
                exception_route = re.fullmatch(r'/api/clubs/([a-zA-Z0-9_-]+)/deadline-exception', path)
                if exception_route:
                    if user['role'] != 'sld':
                        raise APIError('Only SLD can grant or revoke late-submission permission.', 403)
                    club = self.app.get('club', exception_route[1])
                    previous = next((record for record in self.app.all('deadline_exception') if record['id'] == club['id']), {'revision': 0})
                    if data.get('revision', previous['revision']) != previous['revision']:
                        raise APIError('This permission changed. Reload before updating it.', 409)
                    if type(data.get('enabled')) is not bool:
                        raise APIError('Choose whether late-submission permission is enabled.')
                    reason = text(data.get('reason', ''), 2000)
                    if not reason:
                        raise APIError('A permission or revocation reason is required.', fields={'reason':'Enter the SLD reason.'})
                    stamp = auth.now()
                    expiry = None
                    if data['enabled']:
                        try:
                            expiry = datetime.fromisoformat(text(data.get('expires_at',''),100))
                            if expiry.tzinfo is None or expiry <= datetime.fromisoformat(stamp):
                                raise ValueError()
                        except ValueError:
                            raise APIError('Permission expiry must be a future date and time with timezone.', fields={'expires_at':'Choose a future expiry.'})
                    record = {'id':club['id'], 'club_id':club['id'], 'revision':previous['revision'] + 1,
                              'enabled':data['enabled'], 'reason':reason, 'expires_at':expiry.isoformat() if expiry else None,
                              'updated_at':stamp, 'updated_by':user['email'], 'created_at':previous.get('created_at',stamp)}
                    versions = [('deadline_exception', record),
                                ('deadline_exception_version', {'id': club['id'] + '-r' + str(record['revision']),
                                                                'club_id': club['id'], 'snapshot': record.copy()})]
                    if previous['revision']:
                        versions.append(('deadline_exception_version', {'id': club['id'] + '-r' + str(previous['revision']),
                                                                       'club_id': club['id'], 'snapshot': previous.copy()}))
                    self.app.put_batch(versions)
                    self.app.log(user,'late_submission_permission_granted' if record['enabled'] else 'late_submission_permission_revoked',club['id'])
                    return self.json({'deadline_exception':record})
                if path == '/api/registration-grants':
                    if user['role'] != 'sld':
                        raise APIError('Only SLD can authorize club registration.', 403)
                    grant = {key: text(data.get(key, ''), 250) for key in ('club_name', 'president_email', 'advisor_email', 'semester')}
                    for key in ('president_email', 'advisor_email'):
                        grant[key] = grant[key].lower()
                        if not auth.university_email(grant[key]):
                            raise APIError('President and advisor must have QIU email addresses.')
                    if not grant['club_name'] or not grant['semester'] or grant['president_email'] == grant['advisor_email']:
                        raise APIError('Complete the club name, semester and distinct president/advisor.')
                    if any(g['club_name'].casefold() == grant['club_name'].casefold() and g['semester'].casefold() == grant['semester'].casefold() for g in self.app.all('registration_grant')):
                        raise APIError('Registration for this club and semester is already authorized.', 409)
                    grant.update(id=secrets.token_urlsafe(12), status='available', revision=1, created_at=auth.now(), created_by=user['email'])
                    grant['updated_at'] = grant['created_at']
                    self.app.put('registration_grant', grant)
                    self.app.log(user, 'club_registration_authorized', grant['id'])
                    return self.json({'registration_grant': grant})
                if path == '/api/clubs':
                    source = data.get('club', {})
                    if not isinstance(source, dict):
                        raise APIError('Club form is required.')
                    if not source.get('id') and not source.get('registration_grant_id'):
                        raise APIError('SLD must authorize this president to register the club first.', 403)
                    club = validate_club(source)
                    previous = self.app.get('club', source['id']) if source.get('id') else None
                    if previous:
                        if not self.app.editable(previous, user):
                            raise APIError('You cannot edit this club.', 403)
                        if not self.app.registration_editable(previous, user):
                            raise APIError('SLD has opened this registration for review or it is approved. Editing is locked until returned.', 409)
                        if source.get('revision') != previous.get('revision', 0):
                            raise APIError('Another committee member changed this draft. Your entries are still on screen; copy them before reopening the latest draft.', 409)
                        club.update({k: previous[k] for k in ('id', 'owner_email', 'created_at', 'status', 'history')})
                        if previous.get('registration_grant_id'):
                            club['registration_grant_id'] = previous['registration_grant_id']
                            club['sld_review_started_at'] = previous.get('sld_review_started_at')
                            club['sld_review_started_by'] = previous.get('sld_review_started_by')
                            self.bound_grant(club, self.app.get('registration_grant', club['registration_grant_id']))
                    else:
                        grant_id = text(source.get('registration_grant_id', ''), 100)
                        if not grant_id:
                            raise APIError('SLD must authorize this president to register the club first.', 403)
                        grant = self.app.get('registration_grant', grant_id)
                        if user['email'] != grant['president_email'] or user['role'] == 'sld':
                            raise APIError('Only the authorized president can use this registration grant.', 403)
                        if grant['status'] != 'available':
                            raise APIError('This registration authorization has already been used.', 409)
                        self.bound_grant(club, grant)
                        club.update(id=secrets.token_urlsafe(12), owner_email=user['email'], created_at=auth.now(), status='draft', history=[])
                        club['registration_grant_id'] = grant_id
                    club['revision'] = previous.get('revision', 0) + 1 if previous else 1
                    club['updated_at'] = auth.now()
                    if previous and previous['status'] in ('pending_advisor', 'pending_sld'):
                        club['status'] = 'pending_advisor'
                        version = self.app.snapshot(club)
                        club['history'].append({'action': 'submitted_revision_updated', 'actor': user['email'], 'timestamp': auth.now(),
                                                'invalidated_digest': previous.get('submitted_digest'), **version})
                    if previous:
                        self.app.put('club', club)
                    else:
                        grant.update(status='used', club_id=club['id'], used_at=auth.now(), updated_at=auth.now(), revision=grant['revision'] + 1)
                        self.app.put_batch([('club', club), ('registration_grant', grant)])
                    self.app.log(user, 'club_draft_saved', club['id'])
                    return self.json({'club': self.app.decorate_club(club, user)})
                match = re.fullmatch(r'/api/clubs/([a-zA-Z0-9_-]+)/(submit|review|open-review)', path)
                if match:
                    club = self.app.get('club', match[1])
                    if match[2] == 'open-review' and user['role'] != 'sld':
                        raise APIError('Only SLD can open an official registration review.', 403)
                    if match[2] == 'open-review' and club.get('sld_review_started_at'):
                        return self.json({'club': self.app.decorate_club(club, user)})
                    if (match[2] != 'open-review' or 'revision' in data) and data.get('revision') != club.get('revision', 0):
                        raise APIError('This registration changed. Reopen its latest version before reviewing or submitting.', 409)
                    club['revision'] = club.get('revision', 0) + 1
                    if match[2] == 'open-review':
                        if user['role'] != 'sld':
                            raise APIError('Only SLD can open an official registration review.', 403)
                        if club['status'] not in ('pending_advisor', 'pending_sld', 'reviewing_sld'):
                            raise APIError('Only submitted registrations can be opened for review.', 409)
                        if not club.get('sld_review_started_at'):
                            club['sld_review_started_at'] = auth.now()
                            club['sld_review_started_by'] = user['email']
                        if club['status'] == 'pending_sld':
                            club['status'] = 'reviewing_sld'
                        entry = {'action': 'sld_review_opened', 'actor': user['email'], 'timestamp': auth.now(), 'revision': club['revision']}
                    elif match[2] == 'submit':
                        if not self.app.editable(club, user):
                            raise APIError('You cannot submit this club.', 403)
                        if club['status'] not in ('draft', 'returned'):
                            raise APIError('Club is already submitted.', 409)
                        validate_club(club, submit=True)
                        club['status'] = 'pending_advisor'
                        entry = {'action': 'submitted', 'actor': user['email'], 'timestamp': auth.now(), **self.app.snapshot(club)}
                    else:
                        advisor = club['status'] == 'pending_advisor' and club['advisor_email'] == user['email']
                        sld = user['role'] == 'sld' and (club['status'] == 'reviewing_sld' or
                              (club['status'] == 'pending_advisor' and club.get('sld_review_started_at') and data.get('action') == 'return'))
                        if not (advisor or sld):
                            raise APIError('This approval is not assigned to you or is out of order.', 403)
                        action = data.get('action')
                        if action not in ('approve', 'return'):
                            raise APIError('Choose approve or return.')
                        comment = text(data.get('comment', ''))
                        if action == 'return' and not comment:
                            raise APIError('A correction reason is required.')
                        if action=='approve' and advisor and data.get('confirm_submission') is not True:raise APIError('Confirm submission to SLD before continuing.',409,'CONFIRMATION_REQUIRED')
                        signature = image(data.get('signature', ''), required=action == 'approve', signature=True)
                        name = text(data.get('name', ''), 250)
                        if action == 'approve' and not name:
                            raise APIError('Type the signing name.')
                        if action == 'approve':
                            validate_club(club, submit=True)
                        club['status'] = 'returned' if action == 'return' else (('reviewing_sld' if club.get('sld_review_started_at') else 'pending_sld') if advisor else 'approved')
                        if action == 'return':
                            club['sld_review_started_at'] = None
                            club['sld_review_started_by'] = None
                        entry = {'action': action, 'stage': 'advisor' if advisor else 'sld', 'actor': user['email'],
                                 'timestamp': auth.now(), 'comment': comment, 'signature': signature, 'name': name,
                                 'revision': club.get('submitted_revision'), 'digest': club.get('submitted_digest')}
                    club['history'].append(entry)
                    club['updated_at'] = auth.now()
                    self.app.put('club', club)
                    self.app.log(user, 'club_' + entry['action'], club['id'])
                    return self.json({'club': self.app.decorate_club(club, user)})
                submit_proposal = re.fullmatch(r'/api/proposals/([a-zA-Z0-9_-]+)/submit', path)
                if submit_proposal:
                    proposal = self.app.get('proposal', submit_proposal[1])
                    proposal = self.app.canonical_proposal(proposal,strict=True)
                    club = self.app.get('club', proposal['club_id'])
                    preparer_profile=self.app.preparer_profile(club,user,proposal)
                    if not preparer_profile:
                        raise APIError('Only the club President or Vice President may sign and submit this proposal.',403)
                    if club['advisor_email']==user['email']:
                        raise APIError('The preparer cannot also be the assigned advisor.',403)
                    if club['status'] != 'approved':
                        raise APIError('The club registration must be approved before an event proposal can be submitted.', 409)
                    if proposal['status'] not in ('draft', 'returned'):
                        raise APIError('This proposal has already been submitted.', 409)
                    if data.get('revision') != proposal.get('revision', 0):
                        raise APIError('This proposal changed. Reopen the latest draft before submitting.', 409)
                    start = event_start(proposal)
                    end = event_end(proposal, start)
                    policy = self.app.settings()
                    if 'settings_revision' in data and data['settings_revision'] != policy['revision']:
                        raise APIError('The submission policy changed. Reload its latest version before submitting.', 409)
                    progress = proposal_progress(proposal)
                    missing = {item['field']:item['label'] + ' is required before submission.' for item in progress['checklist'] if item.get('required', True) and not item['complete']}
                    if missing:
                        raise APIError('Complete the required proposal sections before submitting.', fields=missing)
                    days = policy['event_proposal_lead_days']
                    deadline = start - timedelta(days=days)
                    submitted_at = auth.now()
                    current = datetime.fromisoformat(submitted_at)
                    if start <= current:
                        raise APIError('The event must start in the future. Late-submission permission cannot authorize a past event.', fields={'date':'Choose a future event start.'})
                    exception = next((record for record in self.app.all('deadline_exception') if record['id'] == club['id']), None)
                    allowed = exception and exception['enabled'] and datetime.fromisoformat(exception['expires_at']) > current
                    if current > deadline and not allowed:
                        raise APIError('Proposal must be submitted at least ' + str(days) + ' days before event start. Deadline: ' + deadline.strftime('%d %b %Y, %I:%M %p') + ' Malaysia time.', code='DEADLINE_PASSED', fields={'date':'Submission deadline passed; request SLD permission.'})
                    proposal.pop('deadline_exception_used', None)
                    if current > deadline:
                        proposal['deadline_exception_used'] = {key:exception[key] for key in ('id','revision','reason','updated_by','updated_at','expires_at')}
                        proposal['deadline_exception_used']['actor'] = exception['updated_by']
                    proposal.update(submitted_at=submitted_at, updated_at=submitted_at, status='pending_advisor',
                                    revision=proposal.get('revision', 0) + 1, policy_days_at_submission=days,
                                    deadline_at=deadline.isoformat(), event_starts_at=start.isoformat(), event_ends_at=end.isoformat())
                    preparer=dict(preparer_profile,slot='preparer',signature=image(data.get('signature',''),required=True,signature=True),signed_at=submitted_at,revision=proposal['revision'])
                    proposal['signatures']={'preparer':preparer}
                    proposal['prepared_by_name']=preparer['name']
                    snapshot = {k: v for k, v in proposal.items() if k not in ('history', 'submitted_revision', 'submitted_digest', 'submitted_snapshot', 'can_edit')}
                    # Copy the signature container: adding the binding digest must never alter the hashed snapshot.
                    snapshot['signatures']={'preparer':dict(preparer)}
                    digest = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
                    preparer['digest']=digest
                    proposal['submitted_revision'], proposal['submitted_digest'] = proposal['revision'], digest
                    proposal.setdefault('history', []).append({'action': 'submitted', 'actor': user['email'], 'timestamp': submitted_at,
                                                              'revision': proposal['revision'], 'digest': digest, 'signer':dict(preparer)})
                    self.app.put_batch([('proposal_signature',dict(preparer,id=proposal['id']+'-r'+str(proposal['revision'])+'-preparer',proposal_id=proposal['id'],club_id=club['id'])),('proposal_version', {'id': proposal['id'] + '-r' + str(proposal['revision']), 'snapshot': snapshot, 'digest': digest}),
                                        ('proposal', proposal)])
                    self.app.log(user, 'proposal_submitted', proposal['id'], club['id'])
                    return self.json({'proposal': self.app.decorate_proposal(proposal, user, club)})
                review_proposal = re.fullmatch(r'/api/proposals/([a-zA-Z0-9_-]+)/review', path)
                if review_proposal:
                    proposal = self.app.get('proposal', review_proposal[1])
                    club = self.app.get('club', proposal['club_id'])
                    if proposal['status'] == 'approved':
                        raise APIError('This event proposal is already approved.', 409)
                    advisor = proposal['status'] == 'pending_advisor' and club['advisor_email'] == user['email']
                    sld = proposal['status'] == 'pending_sld' and user['role'] == 'sld'
                    if not (advisor or sld):
                        raise APIError('This proposal review is not assigned to you or is out of order.', 403)
                    if data.get('revision') != proposal['revision']:
                        raise APIError('This proposal changed. Reopen the latest submitted version.', 409)
                    action = data.get('action')
                    if action not in ('approve', 'return'):
                        raise APIError('Choose approve or return.')
                    comment = text(data.get('comment', ''))
                    if action == 'return' and not comment:
                        raise APIError('A correction reason is required.')
                    preparer=proposal.get('signatures',{}).get('preparer')
                    if action=='approve' and (not preparer or preparer.get('revision')!=proposal.get('submitted_revision') or preparer.get('digest')!=proposal.get('submitted_digest')):
                        raise APIError('This submitted version has no valid preparer signature. Return it for President or Vice President signing.',409,'SIGNATURE_REQUIRED')
                    if action=='approve' and (preparer.get('email')==user['email'] or any(signer.get('email')==user['email'] for signer in proposal.get('signatures',{}).values()) or self.app.event_roles(proposal,user)):
                        raise APIError('A signer or event committee member cannot endorse the same submitted version in another slot.',403)
                    if action == 'approve' and any(m['email']==user['email'] for m in club['committee']):
                        raise APIError('A club committee member cannot endorse their own club proposal as reviewer.',403)
                    if action=='approve' and advisor and data.get('confirm_submission') is not True:raise APIError('Confirm submission to SLD before continuing.',409,'CONFIRMATION_REQUIRED')
                    if action=='approve' and sld:
                        from decimal import Decimal
                        income=sum(Decimal(str(row.get('price',0)))*Decimal(str(row.get('quantity',0))) for row in proposal.get('revenue',[]))
                        expense=sum(Decimal(str(row.get('price',0)))*Decimal(str(row.get('quantity',0))) for row in proposal.get('expenses',[]))
                        if expense>income:
                            reason=text(data.get('deficit_approval_reason',''),5000)
                            if not reason:raise APIError('A planned deficit requires an explicit SLD approval reason.',fields={'deficit_approval_reason':'Record the SLD approval reason.'})
                            proposal['deficit_approval']={'amount':str(expense-income),'reason':reason,'approved_by':user['email'],'approved_at':auth.now(),'submitted_revision':proposal['submitted_revision'],'digest':proposal['submitted_digest']}
                    signature = image(data.get('signature', ''), required=action == 'approve', signature=True)
                    slot='advisor' if advisor else 'sld'
                    profile=self.app.reviewer_profile(user,slot)
                    name=profile['name']
                    stamp = auth.now()
                    signer=dict(profile,slot=slot,signature=signature,signed_at=stamp,revision=proposal['submitted_revision'],digest=proposal['submitted_digest']) if action=='approve' else None
                    if signer:
                        proposal.setdefault('signatures',{})[slot]=signer
                    proposal['history'].append({'action': action, 'stage': 'advisor' if advisor else 'sld', 'actor': user['email'],
                                                'timestamp': stamp, 'signature': signature, 'name': name, 'comment': comment,
                                                'revision': proposal.get('submitted_revision'), 'digest': proposal.get('submitted_digest'), 'signer':signer})
                    if action=='return':
                        proposal['signatures']={}
                    proposal.update(revision=proposal['revision'] + 1, updated_at=stamp,
                                    status='returned' if action == 'return' else ('pending_sld' if advisor else 'approved'))
                    signature_records=[('proposal_signature',dict(signer,id=proposal['id']+'-r'+str(proposal['submitted_revision'])+'-'+slot,proposal_id=proposal['id'],club_id=club['id']))] if signer else []
                    if action == 'approve' and sld:
                        proposal['approved_at'] = stamp
                        calendar = {'id': proposal['id'], 'proposal_id': proposal['id'], 'club_id': club['id'], 'club_name': club['name'],
                                    'title': proposal['title'], 'start_at': proposal['event_starts_at'], 'end_at': proposal['event_ends_at'],
                                    'venue': proposal.get('venue', ''), 'description': proposal.get('summary', ''),
                                    'approved_at': stamp, 'updated_at': stamp}
                        self.app.put_batch([('proposal', proposal), ('calendar_event', calendar)]+signature_records)
                    else:
                        self.app.put_batch([('proposal',proposal)]+signature_records)
                    self.app.log(user, 'proposal_return' if action == 'return' else ('proposal_advisor_approve' if advisor else 'proposal_sld_approve'),
                                 proposal['id'], club['id'])
                    return self.json({'proposal': self.app.decorate_proposal(proposal, user, club)})
                if path == '/api/proposals':
                    source = data.get('proposal')
                    if not isinstance(source, dict):
                        raise APIError('Proposal form is required.')
                    # Planned form fields are editable; record metadata only comes from the server.
                    proposal = bounded({key: value for key, value in source.items() if key in PROPOSAL_FIELDS})
                    for key in ('activities', 'itinerary', 'committee', 'revenue', 'expenses'):
                        value = proposal.get(key, [])
                        if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
                            raise APIError('Proposal table rows must be objects.')
                    for key in ('revenue', 'expenses'):
                        import exports
                        exports.total(proposal.get(key, []))
                    for key in ('title', 'summary', 'date', 'end_date', 'start_time', 'end_time', 'venue', 'mode', 'duration', 'introduction', 'eligibility', 'ict', 'logistics', 'transport', 'departure_time', 'pickup_point', 'return_time', 'return_pickup', 'conclusion'):
                        if key in proposal and not isinstance(proposal[key], str):
                            raise APIError('Proposal text fields must contain text.')
                    validate_sdgs(proposal.get('sdgs', []))
                    objectives = proposal.get('objectives',[])
                    if isinstance(objectives,str):
                        objectives = [line.strip() for line in objectives.splitlines() if line.strip()]
                    if not isinstance(objectives,list) or any(not isinstance(value,str) for value in objectives):
                        raise APIError('Objectives must be a list of text entries.',fields={'objectives':'Use one objective per row.'})
                    proposal['objectives'] = [value.strip() for value in objectives]
                    for flag, field in [('ict_required','ict'),('logistics_required','logistics')]:
                        value=proposal.get(flag,True)
                        if type(value) is not bool:
                            raise APIError('Event support choices must be yes or no.',fields={flag:'Choose yes or no.'})
                        proposal[flag]=value
                        if not value:
                            proposal[field]=''
                            if flag == 'logistics_required':
                                for hidden_field in ('transport','departure_time','pickup_point','return_time','return_pickup'):
                                    proposal[hidden_field]=''
                    proposal=self.app.canonical_proposal(proposal,strict=True)
                    club = self.app.get('club', text(proposal.get('club_id', ''), 100))
                    previous = self.app.get('proposal', text(source['id'], 100)) if source.get('id') else None
                    if previous and previous['club_id'] != club['id']:
                        raise APIError('Cannot move a proposal between clubs.', 403)
                    if not self.app.editable(club,user) and (not previous or not self.app.proposal_editable(previous,club,user)):
                        raise APIError('You can edit only the club or event proposals assigned to you.',403)
                    if club['status'] != 'approved':
                        raise APIError('Only approved clubs can prepare event proposals.', 409)
                    creation_mapping=None
                    creation_key=source.get('creation_key') if not source.get('id') else None
                    if creation_key is not None:
                        try:
                            if not isinstance(creation_key,str) or len(creation_key)!=36 or str(uuid.UUID(creation_key)) != creation_key.lower():
                                raise ValueError()
                        except (ValueError,AttributeError):
                            raise APIError('The new-draft creation key is invalid. Reopen the proposal form.',fields={'creation_key':'Use a valid UUID creation key.'})
                        mapping_id=hashlib.sha256((user['email']+'\0'+club['id']+'\0'+creation_key.lower()).encode()).hexdigest()
                        try:
                            mapping=self.app.get('proposal_creation',mapping_id)
                        except APIError as error:
                            if error.status != 404:
                                raise
                            mapping=None
                        if mapping:
                            existing=self.app.get('proposal',mapping['proposal_id'])
                            if existing['revision'] != mapping['initial_revision']:
                                raise APIError('This draft was already created and then changed. Open the existing proposal before saving more edits.',409,'CREATION_REPLAY_CONFLICT')
                            return self.json({'proposal':self.app.decorate_proposal(existing,user,club),'creation_replayed':True})
                        creation_mapping={'id':mapping_id,'actor_email':user['email'],'club_id':club['id'],'initial_revision':1,'created_at':auth.now()}
                    if previous and not self.app.editable(club,user):
                        if proposal.get('committee',[]) != previous.get('committee',[]):
                            raise APIError('Only club committees and SLD can change event committee assignments.',403)
                        proposal['committee']=previous.get('committee',[])
                    else:
                        proposal['committee']=self.app.committee_identities(proposal.get('committee',[]),club)
                    if previous and previous['status'] not in ('draft', 'returned'):
                        raise APIError('Submitted or approved proposal content is locked until returned for correction.', 409)
                    if previous and source.get('revision') != previous.get('revision', 0):
                        raise APIError('Another committee member changed this proposal. Your entries are still on screen; copy them before reopening the latest draft.', 409)
                    proposal.update(id=previous['id'] if previous else secrets.token_urlsafe(12),
                                    revision=previous.get('revision', 0) + 1 if previous else 1,
                                    owner_email=previous['owner_email'] if previous else user['email'],
                                    prepared_by_name=previous.get('prepared_by_name', '') if previous else user['name'],
                                    last_editor_email=user['email'],
                                    created_at=previous['created_at'] if previous else auth.now(), updated_at=auth.now(), status='draft',
                                    history=previous.get('history', []) if previous else [])
                    if creation_mapping is not None:
                        creation_mapping['proposal_id']=proposal['id']
                        self.app.put_batch([('proposal',proposal),('proposal_creation',creation_mapping)])
                    else:
                        self.app.put('proposal', proposal)
                    self.app.log(user, 'proposal_draft_saved', proposal['id'], club['id'])
                    return self.json({'proposal': self.app.decorate_proposal(proposal, user, club)})
                raise APIError('Not found.', 404)
        except APIError as error:
            self.json({'error': str(error), 'code': error.code, 'fields': error.fields}, error.status)
        except (ValueError, TypeError, KeyError):
            self.json({'error': 'Invalid form fields.', 'code':'VALIDATION_ERROR','fields':{}}, 400)
        except Exception:
            self.json({'error': 'Unable to save request. No approval has been granted.', 'code':'INTERNAL_ERROR','fields':{}}, 500)


class ExclusiveHTTPServer(ThreadingHTTPServer):
    """Windows must reject a second process instead of delivering requests to stale code."""
    allow_reuse_address = False

    def server_bind(self):
        if os.name == 'nt':
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview', action='store_true', help='Fictional local personas; never enable in production.')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    base_url = os.getenv('SLD_APP_URL', 'http://127.0.0.1:' + str(args.port))
    if args.preview and urlsplit(base_url).hostname not in ('127.0.0.1', 'localhost'):
        parser.error('Preview must use a loopback application URL.')
    data = ROOT / 'data'
    data.mkdir(exist_ok=True)
    server = ExclusiveHTTPServer(('127.0.0.1', args.port), Handler)
    server.app = App(data / ('preview.sqlite3' if args.preview else 'sld.sqlite3'), args.preview, base_url)
    print('QIU SLD ' + ('FICTIONAL PREVIEW' if args.preview else 'Google Workspace mode') + ' ' + base_url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        server.app.db.close()


if __name__ == '__main__':
    main()
