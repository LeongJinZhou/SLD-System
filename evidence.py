"""Private completed-activity photos, post-event review and ordered SLD archives."""
import base64
import copy
import hashlib
import io
import json
import re
import secrets
import warnings
import zipfile
from datetime import datetime
from html import escape

from PIL import Image
import auth
import club_reports

MAX_IMAGE = 2 * 1024 * 1024
MAX_PHOTOS = 30
MAX_ARCHIVE = 256 * 1024 * 1024


def error(message, status=400, code=None, fields=None):
    from server import APIError
    raise APIError(message, status, code, fields)


def segment(value):
    value = re.sub(r'[^\w .()-]', '_', str(value), flags=re.UNICODE).strip(' .')
    return (value or 'Unnamed')[:100]


def photos(app, kind, record_id, bodies=False):
    """Scope in SQL; UI/count requests never load the private image bodies."""
    import storage
    field = lambda key: "JSON_EXTRACT(data,'$." + key + "')"
    if isinstance(app.db, storage.MySQLStore):
        field = lambda key: "JSON_UNQUOTE(JSON_EXTRACT(data,'$." + key + "'))"
    projection = 'data' if bodies else "JSON_REMOVE(data,'$.content_base64')"
    with app.lock:
        rows = app.db.execute('SELECT ' + projection + ' FROM records WHERE kind=? AND ' + field('target_type') + '=? AND ' + field('target_id') + '=?',
                              ('activity_photo', kind, record_id)).fetchall()
    return [json.loads(row[0]) for row in rows]


def metadata(photo):
    return {k: v for k, v in photo.items() if k != 'content_base64'}


def photo_count(app, kind, record_id):
    return len({p['sha256'] for p in photos(app, kind, record_id)})


def require_photos(app, kind, record_id, minimum):
    if photo_count(app, kind, record_id) < minimum:
        error(f'Upload at least {minimum} different activity photos before submitting.',
              fields={'photos': f'At least {minimum} photos are required.'})


def completion_for(app, proposal_id):
    return next((r for r in app.all('event_completion') if r['proposal_id'] == proposal_id), None)


def context(app, user, kind, record_id, editing=False):
    if kind not in ('club_report', 'proposal'):
        error('Choose an event, weekly report or AGM report.')
    if kind == 'club_report':
        record = app.get(kind, record_id)
        club = app.get('club', record['club_id'])
        if not club_reports.visible(app, user, club):
            error('You do not have access to these report photos.', 403)
        can_upload = club_reports.committee(user, club) and record['status'] in ('draft', 'returned')
        minimum = 1 if record['type'] == 'agm' else 2
        target = record
    else:
        import finance
        try:
            record, club, can_prepare = finance.context(app, user, record_id)
        except finance.FinanceError as exc:
            error(str(exc), exc.status, exc.code, exc.fields)
        target = completion_for(app, record_id)
        can_upload = can_prepare and (target is None or target['status'] in ('draft', 'returned'))
        minimum = 2
        # Post-event evidence belongs to a completed, approved schedule, never planning.
        from server import event_start, event_end
        finish = event_end(record, event_start(record)) if record['status'] == 'approved' else None
        if record['status'] != 'approved' or not finish or finish > datetime.fromisoformat(auth.now()):
            can_upload = False
    if editing and not can_upload:
        error('Photo uploads are available to assigned organisers after the activity, while its report is editable.', 403)
    return record, club, target, minimum, can_upload


def view(app, user, kind, record_id):
    _, _, target, minimum, can_upload = context(app, user, kind, record_id)
    rows = sorted(photos(app, kind, record_id), key=lambda p: (p['uploaded_at'], p['id']))
    return dict(photos=[metadata(p) for p in rows], minimum=minimum, count=photo_count(app, kind, record_id),
                can_upload=can_upload, target_revision=target['revision'] if kind == 'club_report' else None,
                completion_revision=target['revision'] if kind == 'proposal' and target else None,
                zip_url=f'/api/photos/zip?target_type={kind}&target_id={record_id}' if user['role'] == 'sld' else None)


def checked_image(data_url):
    if not isinstance(data_url, str) or len(data_url) > 2800000:
        error('Choose a JPEG, PNG or WebP photo no larger than 2 MB.')
    match = re.fullmatch(r'data:(image/(?:png|jpeg|webp));base64,([A-Za-z0-9+/=]+)', data_url)
    if not match:
        error('Choose a JPEG, PNG or WebP photo.')
    try:
        raw = base64.b64decode(match[2], validate=True)
        if not raw or len(raw) > MAX_IMAGE:
            raise ValueError()
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as img:
                formats = {'PNG': ('image/png', '.png'), 'JPEG': ('image/jpeg', '.jpg'), 'WEBP': ('image/webp', '.webp')}
                mime, extension = formats[img.format]
                if mime != match[1] or img.width * img.height > 20000000 or getattr(img, 'n_frames', 1) != 1:
                    raise ValueError()
                img.verify()
            with Image.open(io.BytesIO(raw)) as img:
                img.load()
        return raw, mime, extension
    except (ValueError, KeyError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        error('This photo could not be read. Choose a valid, single-image JPEG, PNG or WebP file, no larger than 2 MB or 20 megapixels.')


def mutate_target(app, target, kind, user):
    if target:
        target['revision'] += 1
        target['updated_at'] = auth.now()
        target['updated_by'] = user['email']
        target['photo_evidence'] = [metadata(p) for p in photos(app, kind, target['id'] if kind == 'club_report' else target['proposal_id'])]
        app.put('club_report' if kind == 'club_report' else 'event_completion', target)


def revision_check(target, kind, data):
    if target and data.get('target_revision' if kind == 'club_report' else 'completion_revision') != target['revision']:
        error('This report changed. Refresh the report before changing its photos.', 409)


def upload(app, user, data):
    kind, rid = data.get('target_type'), data.get('target_id')
    record, club, target, _, _ = context(app, user, kind, rid, True)
    revision_check(target, kind, data)
    raw, mime, extension = checked_image(data.get('data_url'))
    current = photos(app, kind, rid)
    digest = hashlib.sha256(raw).hexdigest()
    if any(p['sha256'] == digest for p in current):
        error('This photo is already attached. Choose a different activity photo.', 409, 'DUPLICATE_PHOTO')
    if len(current) >= MAX_PHOTOS:
        error(f'A report can contain up to {MAX_PHOTOS} photos.')
    from server import text
    name = segment(text(data.get('name', 'Activity photo'), 180)).rsplit('.', 1)[0] + extension
    photo = dict(id=secrets.token_hex(12), target_type=kind, target_id=rid, club_id=club['id'], name=name,
                 content_type=mime, size=len(raw), sha256=digest, uploaded_at=auth.now(),
                 uploaded_by={'name': user.get('name') or user['email'], 'email': user['email']},
                 content_base64=base64.b64encode(raw).decode())
    app.put('activity_photo', photo)
    mutate_target(app, target, kind, user)
    app.log(user, 'activity_photo_uploaded', record['id'], club['id'])
    return dict(view(app, user, kind, rid), photo=metadata(photo))


def delete_photo(app, user, pid, data):
    photo = app.get('activity_photo', pid)
    _, club, target, _, _ = context(app, user, photo['target_type'], photo['target_id'], True)
    revision_check(target, photo['target_type'], data)
    with app.lock:
        app.db.execute('DELETE FROM records WHERE kind=? AND id=?', ('activity_photo', pid))
    mutate_target(app, target, photo['target_type'], user)
    app.log(user, 'activity_photo_removed', photo['target_id'], club['id'])
    return view(app, user, photo['target_type'], photo['target_id'])


def archive_label(record, club, kind):
    activity = record.get('type', 'event') if kind == 'club_report' else 'event'
    person = record.get('submitted_by_name') or record.get('submitted_by') or record.get('owner_email') or record.get('created_by') or 'Draft'
    return '_'.join(segment(v) for v in (activity + '-' + record.get('title', 'Activity'), club['name'], record.get('date', ''), person))


def write_photos(z, folder, rows, add=None):
    write = add or z.writestr
    rows = sorted(rows, key=lambda p: (p['uploaded_at'], p['id']))
    for n, photo in enumerate(rows, 1):
        extension = {'image/png': '.png', 'image/jpeg': '.jpg', 'image/webp': '.webp'}[photo['content_type']]
        write(folder + f'/{n:02d}-{photo["id"]}{extension}', base64.b64decode(photo['content_base64'], validate=True))
    write(folder + '/manifest.json', json.dumps([metadata(p) for p in rows], ensure_ascii=False, indent=2).encode())


def photo_zip(app, user, kind, rid):
    if user['role'] != 'sld':
        error('Only SLD can download photo archives.', 403)
    record, club, target, _, _ = context(app, user, kind, rid)
    named = dict(record)
    if kind == 'proposal' and target:
        named.update({k: target.get(k) for k in ('submitted_by', 'submitted_by_name')})
    folder = archive_label(named, club, kind)
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
        write_photos(z, folder, photos(app, kind, rid, True))
    return output.getvalue(), 'application/zip', folder + '.zip'


def completion_view(app, user, proposal_id):
    proposal, club, report, _, can_prepare = context(app, user, 'proposal', proposal_id)
    return dict(view(app, user, 'proposal', proposal_id), report=report, proposal_id=proposal_id,
                club_id=club['id'], title=proposal['title'], can_prepare=can_prepare,
                can_review=user['role'] == 'sld' and bool(report and report['status'] == 'pending_sld'),
                reviewer_profile=app.reviewer_profile(user, 'sld') if user['role'] == 'sld' else None)


def save_completion(app, user, data):
    from server import text
    source = data.get('report')
    if not isinstance(source, dict):
        error('Complete the post-event report.')
    old = app.get('event_completion', source['id']) if source.get('id') else None
    pid = old['proposal_id'] if old else text(source.get('proposal_id', ''), 100)
    proposal, club, existing, _, _ = context(app, user, 'proposal', pid, True)
    if old and old.get('revision') != source.get('revision'):
        error('The post-event report changed. Refresh before editing.', 409)
    if not old and existing:
        # A retry for creation returns the same report rather than a second draft.
        if source.get('creation_key') and existing.get('creation_key') == source['creation_key'] and existing['created_by'] == user['email']:
            return dict(report=existing, creation_replayed=True)
        error('This event already has a post-event report. Open its existing report.', 409)
    stamp = auth.now()
    r = copy.deepcopy(old) if old else dict(id=secrets.token_hex(12), proposal_id=pid, club_id=club['id'],
        title=proposal['title'], date=proposal.get('end_date') or proposal.get('date'), status='draft', revision=0,
        created_by=user['email'], created_at=stamp, history=[], creation_key=text(source.get('creation_key', ''), 100))
    r.update(summary=text(source.get('summary', ''), 20000), revision=r['revision'] + 1,
             updated_at=stamp, updated_by=user['email'], photo_evidence=[metadata(p) for p in photos(app, 'proposal', pid)])
    app.put('event_completion', r)
    return dict(report=r)


def transition_completion(app, user, rid, action, data):
    from server import image, text
    r = app.get('event_completion', rid)
    proposal, club, _, _, can_prepare = context(app, user, 'proposal', r['proposal_id'])
    if data.get('revision') != r['revision']:
        error('The post-event report changed. Refresh before continuing.', 409)
    stamp = auth.now()
    if action == 'submit':
        if not can_prepare:
            error('Only assigned organisers can submit an editable post-event report.', 403)
        if data.get('confirm_submission') is not True:
            error('Confirm the post-event submission before sending it to SLD.', code='CONFIRMATION_REQUIRED')
        if not r.get('summary'):
            error('Describe the event outcomes before submitting.', fields={'summary': 'Event outcomes are required.'})
        require_photos(app, 'proposal', proposal['id'], 2)
        r.update(status='pending_sld', submitted_at=stamp, submitted_by=user['email'],
                 submitted_by_name=user.get('name') or user['email'], submitted_revision=r['revision'],
                 photo_evidence=[metadata(p) for p in photos(app, 'proposal', proposal['id'])])
        snapshot = copy.deepcopy(r)
        digest = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
        r['submitted_digest'] = digest
        r['history'].append(dict(action='submit', actor=user['email'], name=user.get('name'), timestamp=stamp,
                                comment='', revision=r['submitted_revision'], digest=digest))
        app.put('event_completion_version', dict(id=rid + '-r' + str(r['revision']), report_id=rid, snapshot=snapshot, digest=digest))
        log_action = 'submitted'
    else:
        if user['role'] != 'sld':
            error('Only SLD can review a post-event report.', 403)
        if r['status'] != 'pending_sld':
            error('This post-event report is not awaiting SLD review.', 409)
        choice = data.get('action')
        comment = text(data.get('comment', ''), 5000)
        if choice not in ('approve', 'return') or choice == 'return' and not comment:
            error('Choose an action and give a correction reason when returning a report.')
        if choice == 'approve':
            if user['email'] == r['submitted_by'] or app.event_roles(proposal, user) or club_reports.committee(user, club):
                error('An organiser cannot approve their own event completion.', 403)
            require_photos(app, 'proposal', proposal['id'], 2)
            signature = image(data.get('signature', ''), required=True, signature=True)
            profile = app.reviewer_profile(user, 'sld')
            r['signature'] = dict(profile, signature=signature, signed_at=stamp, submitted_revision=r['submitted_revision'], digest=r['submitted_digest'])
            r.update(status='approved', approved_at=stamp, approved_by=user['email'])
        else:
            r.update(status='returned', signature=None)
        r['history'].append(dict(action=choice, actor=user['email'], name=user.get('name'), timestamp=stamp,
                                comment=comment, revision=r['submitted_revision'], digest=r['submitted_digest']))
        log_action = 'approved' if choice == 'approve' else 'returned'
    r.update(revision=r['revision'] + 1, updated_at=stamp, updated_by=user['email'])
    app.put('event_completion', r)
    app.log(user, 'event_completion_' + log_action, rid, club['id'])
    return dict(report=r)


def completion_pdf(report, proposal, club):
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as PDFImage
    from reportlab.lib.pagesizes import A4
    styles = getSampleStyleSheet()
    def stamp(value):
        return datetime.fromisoformat(value).astimezone(club_reports.MYT).strftime('%d %b %Y, %I:%M %p MYT')
    def p(value, style='BodyText'):
        return Paragraph(escape(str(value or '—')).replace('\n', '<br/>'), styles[style])
    output = io.BytesIO()
    story = [p('Post-event report', 'Title'), p(club['name'], 'Heading2'), p(proposal['title']),
             p('Status: ' + report['status'].replace('_', ' ').title()), Spacer(1, 16), p('Event outcomes', 'Heading2'), p(report.get('summary')),
             Spacer(1, 16), p('Photo evidence', 'Heading2')]
    for photo in report.get('photo_evidence', []):
        story.append(p(photo['name'] + ' · SHA-256: ' + photo['sha256']))
    sig = report.get('signature')
    if sig:
        story += [Spacer(1, 16), p('Reviewed by SLD', 'Heading2'), p(sig['name']), p(sig['designation']), p(sig['department']), p(stamp(sig['signed_at']))]
        if sig.get('signature'):
            story.append(PDFImage(io.BytesIO(base64.b64decode(sig['signature'].split(',', 1)[1])), width=150, height=60, kind='proportional'))
    story += [Spacer(1, 16), p('Review log', 'Heading2')]
    rows = [[p('Action'), p('Reviewed by'), p('Server date'), p('Remarks')]]
    for h in report.get('history', []):
        rows.append([p(h['action'].title()), p(h.get('name') or h['actor']), p(stamp(h['timestamp'])), p(h['comment'])])
    t = Table(rows, colWidths=[65, 115, 115, 170], repeatRows=1, splitInRow=1)
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eef2f6')), ('BOTTOMPADDING', (0, 0), (-1, -1), 8)]))
    story.append(t)
    SimpleDocTemplate(output, pagesize=A4, leftMargin=40, rightMargin=40).build(story)
    return output.getvalue()


def annual_archive(app, user, cid, year):
    if user['role'] != 'sld':
        error('Only SLD can download full annual club archives.', 403)
    if not 1900 <= year <= 2100:
        error('Choose a valid annual archive year.')
    club = app.get('club', cid)
    reports = [r for r in app.all('club_report') if r['club_id'] == cid and
               (club_reports.report_year(r) == year if r['type'] == 'agm' else str(r.get('date', '')).startswith(str(year) + '-'))]
    if not any(r['type'] == 'agm' and r['status'] == 'approved' and r.get('handover_applied_at') for r in reports):
        error('Acknowledge the approved AGM and start its committee handover before compiling the annual archive.', 409)
    events = [p for p in app.all('proposal') if p['club_id'] == cid and str(p.get('date', '')).startswith(str(year) + '-')]
    event_ids = {p['id'] for p in events}
    files = [p for r in reports for p in photos(app, 'club_report', r['id'])] + [p for pid in event_ids for p in photos(app, 'proposal', pid)]
    import finance
    receipts = [r for pid in event_ids for r in finance.event_receipts(app, pid)]
    if sum(p['size'] for p in files) + sum(r['size'] for r in receipts) > MAX_ARCHIVE:
        error('This annual archive exceeds 256 MB. Download individual activity archives instead.', 413)
    import exports
    folder = segment(club['name']) + '_' + str(year)
    output = io.BytesIO()
    manifest = dict(club_id=cid, club_name=club['name'], year=year, compiled_at=auth.now(), compiled_by=user['email'], files=[])
    total_size = 0
    def add(z, name, raw):
        nonlocal total_size
        total_size += len(raw)
        if total_size > MAX_ARCHIVE:
            error('This annual archive exceeds 256 MB. Download individual activity archives instead.', 413)
        path = folder + '/' + name
        z.writestr(path, raw)
        manifest['files'].append(dict(path=path, sha256=hashlib.sha256(raw).hexdigest(), size=len(raw)))
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
        add(z, 'Read me.txt', ('Annual club archive\nClub: ' + club['name'] + '\nYear: ' + str(year) +
             '\nCompiled using the server clock: ' + auth.now() + '\n\nFolders\nCommittee: recorded annual hierarchy.\nAGM and Weekly activities: reports, photos and records.\nEvents: proposal, receipts, photos and reports grouped per event.\nWithdrawals: fund requests and Finance/receipt evidence.\nProgress: recorded activity timeline.\nAudit: immutable submitted versions and signatures.\nManifest.json: complete file list and SHA-256 hashes.\n\nStatuses are preserved as recorded; a draft or returned document is not an approval.\nPrivate university records: SLD access only.').encode())
        add(z, 'Club/Profile.pdf', exports.club_pdf(club))
        hierarchy = [h for h in app.all('club_hierarchy') if h.get('club_id') == cid and h.get('year') == year]
        add(z, 'Committee/Hierarchy.json', json.dumps(hierarchy, ensure_ascii=False, indent=2).encode())
        for r in sorted(reports, key=lambda r: (r.get('date', ''), r['id'])):
            base = ('AGM' if r['type'] == 'agm' else 'Weekly activities') + '/' + segment(r['title']) + '-' + r['id']
            add(z, base + '/Report.pdf', exports.club_report_pdf(r, club))
            add(z, base + '/Record.json', json.dumps(r, ensure_ascii=False, indent=2).encode())
            write_photos(z, base + '/Photos', photos(app, 'club_report', r['id'], True), lambda name, raw: add(z, name, raw))
        for event in sorted(events, key=lambda p: (p.get('date', ''), p['id'])):
            base = 'Events/' + segment(event['title']) + '-' + event['id']
            add(z, base + '/Proposal/Proposal.pdf', exports.export_proposal(event, club, user, 'pdf')[0])
            add(z, base + '/Proposal/Record.json', json.dumps(event, ensure_ascii=False, indent=2).encode())
            for receipt in receipts:
                if receipt['proposal_id'] == event['id']:
                    raw = app.get('receipt', receipt['id'])
                    add(z, base + '/Receipts/' + receipt['id'] + '-' + segment(receipt['filename']), base64.b64decode(raw['content_base64'], validate=True))
            write_photos(z, base + '/Photos', photos(app, 'proposal', event['id'], True), lambda name, raw: add(z, name, raw))
            actual = next((r for r in app.all('finance_report') if r['proposal_id'] == event['id']), None)
            if actual:
                add(z, base + '/Reports/Financial report.pdf', exports.finance_pdf(actual, event, club))
            completion = completion_for(app, event['id'])
            if completion:
                add(z, base + '/Reports/Post-event report.pdf', completion_pdf(completion, event, club))
        # Private snapshots and review versions make the archive independently traceable.
        for kind in ('club_report_version', 'club_report_signature', 'proposal_version', 'proposal_signature', 'finance_version', 'event_completion_version'):
            selected = [r for r in app.all(kind) if r.get('report_id') in {x['id'] for x in reports} | {x['id'] for x in app.all('finance_report') if x['proposal_id'] in event_ids} | {x['id'] for x in app.all('event_completion') if x['proposal_id'] in event_ids} or r.get('proposal_id') in event_ids or r.get('snapshot', {}).get('club_id') == cid and r.get('snapshot', {}).get('id') in event_ids]
            if selected:
                add(z, 'Audit/' + kind + '.json', json.dumps(selected, ensure_ascii=False, indent=2).encode())
        withdrawals = [w for w in app.all('withdrawal') if w['club_id'] == cid and datetime.fromisoformat(w['created_at']).astimezone(club_reports.MYT).year == year]
        for w in withdrawals:
            base = 'Withdrawals/' + segment(w.get('purpose', 'Fund request')) + '-' + w['id']
            add(z, base + '/Record.json', json.dumps(w, ensure_ascii=False, indent=2).encode())
            import storage
            field = "JSON_EXTRACT(data,'$.withdrawal_id')"
            if isinstance(app.db, storage.MySQLStore):
                field = 'JSON_UNQUOTE(' + field + ')'
            docs = app.db.execute('SELECT data FROM records WHERE kind=? AND ' + field + '=?', ('withdrawal_document', w['id'])).fetchall()
            for row in docs:
                doc = json.loads(row[0])
                add(z, base + '/Supporting documents/' + doc['id'] + '-' + segment(doc['filename']), base64.b64decode(doc['content_base64'], validate=True))
        for kind in ('withdrawal_version', 'withdrawal_signature'):
            selected = [r for r in app.all(kind) if r.get('withdrawal_id') in {w['id'] for w in withdrawals}]
            if selected:
                add(z, 'Audit/' + kind + '.json', json.dumps(selected, ensure_ascii=False, indent=2).encode())
        logs = [json.loads(row[0]) for row in app.db.execute('SELECT data FROM logs')]
        logs = [r for r in logs if r.get('club_id') == cid and datetime.fromisoformat(r['timestamp']).astimezone(club_reports.MYT).year == year]
        add(z, 'Progress/Activity log.json', json.dumps(logs, ensure_ascii=False, indent=2).encode())
        add(z, 'Manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2).encode())
    app.log(user, 'club_annual_archive_exported', cid, cid)
    return output.getvalue(), 'application/zip', folder + '_Annual-archive.zip'


def handle_get(app, user, path, query):
    if path == '/api/photos':
        return view(app, user, query.get('target_type', [''])[0], query.get('target_id', [''])[0])
    if path == '/api/photos/zip':
        return photo_zip(app, user, query.get('target_type', [''])[0], query.get('target_id', [''])[0])
    match = re.fullmatch(r'/api/photos/([A-Za-z0-9_-]+)/file', path)
    if match:
        photo = app.get('activity_photo', match[1])
        context(app, user, photo['target_type'], photo['target_id'])
        return base64.b64decode(photo['content_base64']), photo['content_type'], photo['name']
    match = re.fullmatch(r'/api/proposals/([A-Za-z0-9_-]+)/completion', path)
    if match:
        return completion_view(app, user, match[1])
    match = re.fullmatch(r'/api/event-completions/([A-Za-z0-9_-]+)/export', path)
    if match:
        report = app.get('event_completion', match[1])
        proposal, club, _, _, _ = context(app, user, 'proposal', report['proposal_id'])
        return completion_pdf(report, proposal, club), 'application/pdf', 'post-event-report.pdf'
    match = re.fullmatch(r'/api/clubs/([A-Za-z0-9_-]+)/annual-archive', path)
    if match:
        try:
            year = int(query.get('year', [''])[0])
        except ValueError:
            error('Choose a valid annual archive year.')
        return annual_archive(app, user, match[1], year)


def handle_post(app, user, path, data):
    if path == '/api/photos':
        return upload(app, user, data)
    match = re.fullmatch(r'/api/photos/([A-Za-z0-9_-]+)/delete', path)
    if match:
        return delete_photo(app, user, match[1], data)
    if path == '/api/event-completions':
        return save_completion(app, user, data)
    match = re.fullmatch(r'/api/event-completions/([A-Za-z0-9_-]+)/(submit|review)', path)
    if match:
        return transition_completion(app, user, match[1], match[2], data)
