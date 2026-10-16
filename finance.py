"""Actual event accounts. Planned budgets never post to the club ledger."""
import base64
import hashlib
import json
import re
import secrets
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import auth

MYT = timezone(timedelta(hours=8))


class FinanceError(Exception):
    def __init__(self, message, status=400, code=None, fields=None):
        self.status, self.code, self.fields = status, code or {403:'ACCESS_DENIED',404:'RECORD_NOT_FOUND',409:'REVISION_CONFLICT'}.get(status,'VALIDATION_ERROR'), fields or {}
        super().__init__(message)


def cents(value, positive=False, signed=False):
    if isinstance(value, bool) or not isinstance(value, (str,int)) or not re.fullmatch(r'-?\d{1,9}(?:\.\d{1,2})?',str(value)):
        raise FinanceError('Enter a valid amount with at most two decimal places.')
    amount = Decimal(str(value))
    if abs(amount) > Decimal('100000000') or (not signed and amount < 0) or (positive and amount <= 0):
        raise FinanceError('Amounts must be positive and no greater than MYR 100,000,000.' if positive else 'The amount is outside the supported range.')
    return int(amount * 100)


def money(value):
    return f'{Decimal(value)/100:.2f}'


def text(value, limit=2000):
    if not isinstance(value,str) or len(value)>limit:
        raise FinanceError('Text is invalid or exceeds the supported length.')
    return value.strip()


def planned(proposal, key):
    total = Decimal(0)
    try:
        for row in proposal.get(key,[]):
            price, quantity = Decimal(str(row.get('price') or 0)), Decimal(str(row.get('quantity') or 0))
            if not price.is_finite() or not quantity.is_finite() or price<0 or quantity<0:
                raise ValueError()
            total += price*quantity
        if total>100000000:
            raise ValueError()
        return int((total*100).quantize(Decimal('1')))
    except (InvalidOperation,ValueError,TypeError):
        raise FinanceError('The proposal budget contains an invalid amount.')


def context(app,user,proposal_id,prepare=False):
    proposal = app.get('proposal',proposal_id)
    club = app.get('club',proposal['club_id'])
    if not app.proposal_visible(proposal,club,user):
        raise FinanceError('You do not have access to this event account.',403)
    can_prepare = user['role']=='sld' or app.editable(club,user) or bool(app.event_roles(proposal,user))
    if prepare and (not can_prepare or proposal['status']!='approved'):
        raise FinanceError('Only an approved event’s assigned organisers may prepare its actual accounts.',403)
    return proposal,club,can_prepare and proposal['status']=='approved'


def report_for(app,proposal_id):
    return next((r for r in app.all('finance_report') if r['proposal_id']==proposal_id),None)


def receipt_metadata(receipt):
    return {k:v for k,v in receipt.items() if k!='content_base64'}


def event_receipts(app,proposal_id):
    """Project private file bodies out in SQL before returning event metadata."""
    import storage
    field="JSON_EXTRACT(data,'$.proposal_id')"
    if isinstance(app.db,storage.MySQLStore):
        field='JSON_UNQUOTE('+field+')'
    with app.lock:
        rows=app.db.execute("SELECT JSON_REMOVE(data,'$.content_base64') FROM records WHERE kind=? AND "+field+"=? ORDER BY rowid DESC",('receipt',proposal_id)).fetchall()
    return [json.loads(row[0]) for row in rows]


def event_view(app,user,proposal_id):
    proposal,club,can_prepare=context(app,user,proposal_id)
    return dict(proposal_id=proposal_id,club_id=club['id'],title=proposal['title'],planned_income=money(planned(proposal,'revenue')),
                planned_expenses=money(planned(proposal,'expenses')),report=report_for(app,proposal_id),
                receipts=event_receipts(app,proposal_id),can_prepare=can_prepare,can_review=user['role']=='sld',reviewer_profile=app.reviewer_profile(user,'sld') if user['role']=='sld' else None)


def local_day(stamp):
    return datetime.fromisoformat(stamp.replace('Z','+00:00')).astimezone(MYT).strftime('%Y-%m-%d')


def club_view(app,user,club_id):
    club=app.get('club',club_id)
    if not app.visible(club,user):
        raise FinanceError('Club accounts are available only to its committee, advisor and SLD.',403)
    entries=[r for r in app.all('ledger_entry') if r['club_id']==club_id]
    entries.sort(key=lambda r:(r['approved_at'],r['id']))
    opening=next((r for r in app.all('finance_opening') if r['club_id']==club_id),None)
    running=opening['amount_cents'] if opening else 0
    monthly,yearly,days=defaultdict(lambda:dict(income=0,expenses=0,events=0,scheduled_events=0,actions=0)),defaultdict(lambda:dict(income=0,expenses=0,events=0,scheduled_events=0,actions=0)),{}
    def activity(day):
        return days.setdefault(day,dict(date=day,count=0,event_ids=[],event_statuses={},actions=[]))
    proposals=app.all('proposal')
    proposal_clubs={p['id']:p['club_id'] for p in proposals}
    grant_clubs={g['id']:g.get('club_id') for g in app.all('registration_grant')}
    action_counts=defaultdict(int)
    proposal_statuses=defaultdict(int)
    report_statuses=defaultdict(int)
    for proposal in proposals:
        if proposal['club_id']==club_id:proposal_statuses[proposal['status']]+=1
        if proposal['club_id']==club_id and proposal.get('date') and re.fullmatch(r'\d{4}-\d{2}-\d{2}',proposal['date']):
            try:datetime.strptime(proposal['date'],'%Y-%m-%d')
            except ValueError:continue
            day=proposal['date']; cell=activity(day);cell['count']+=1;cell['event_ids'].append(proposal['id'])
            cell['event_statuses'][proposal['id']]=proposal['status']
            monthly[day[:7]]['scheduled_events']+=1;yearly[day[:4]]['scheduled_events']+=1
            if proposal['status']=='approved':monthly[day[:7]]['events']+=1;yearly[day[:4]]['events']+=1
    with app.lock:
        logs=[json.loads(r[0]) for r in app.db.execute('SELECT data FROM logs')]
    for log in logs:
        record_id=log.get('record_id','')
        attributed_club=log.get('club_id') or (record_id if record_id==club_id else proposal_clubs.get(record_id) or grant_clubs.get(record_id))
        if attributed_club!=club_id:
            continue
        action_counts[log.get('action','unknown')]+=1
        day=local_day(log['timestamp']);cell=activity(day);cell['count']+=1
        cell['actions'].append({k:log.get(k,'') for k in ('timestamp','action','actor_name','record_id')})
        monthly[day[:7]]['actions']+=1;yearly[day[:4]]['actions']+=1
    income=expenses=0
    for entry in entries:
        day=local_day(entry['approved_at']);key='income' if entry['kind']=='income' else 'expenses';amount=entry['amount_cents']
        monthly[day[:7]][key]+=amount;yearly[day[:4]][key]+=amount
        if key=='income':income+=amount
        else:expenses+=amount
    def series(groups,balance=False):
        current=running;result=[]
        for period,row in sorted(groups.items()):
            current+=row['income']-row['expenses']
            item=dict(period=period,income=money(row['income']),expenses=money(row['expenses']),net=money(row['income']-row['expenses']),events=row['events'],scheduled_events=row['scheduled_events'],actions=row['actions'])
            if balance:item['balance']=money(current)
            result.append(item)
        return result
    events=[]
    for report in app.all('finance_report'):
        if report['club_id']==club_id:report_statuses[report['status']]+=1
    for proposal in proposals:
        if proposal['club_id']!=club_id:continue
        report=report_for(app,proposal['id'])
        events.append(dict(proposal_id=proposal['id'],title=proposal.get('title') or 'Untitled event',date=proposal.get('date',''),status=proposal['status'],
                           planned_income=money(planned(proposal,'revenue')),planned_expenses=money(planned(proposal,'expenses')),
                           actual_income=report.get('actual_income','0.00') if report else '0.00',actual_expenses=report.get('actual_expenses','0.00') if report else '0.00',
                           report_status=report['status'] if report else 'not_started',report_id=report['id'] if report else None))
    return dict(club_id=club_id,club_name=club['name'],currency='MYR',opening_balance=money(running),opening_set=bool(opening),balance=money(running+income-expenses),
                approved_income=money(income),approved_expenses=money(expenses),monthly=series(monthly,True),yearly=series(yearly),activity_days=sorted(days.values(),key=lambda r:r['date']),
                events=events,entries=entries,activity_summary=dict(logged_actions=sum(action_counts.values()),by_action=dict(sorted(action_counts.items())),proposal_statuses=dict(proposal_statuses),finance_report_statuses=dict(report_statuses)),
                can_prepare=app.editable(club,user),can_admin=user['role']=='sld')


def save_report(app,user,data):
    incoming=data.get('report')
    if not isinstance(incoming,dict):raise FinanceError('An actual financial report is required.')
    proposal_id=text(incoming.get('proposal_id',''),100);proposal,club,_=context(app,user,proposal_id,True)
    old=report_for(app,proposal_id)
    if old:
        if incoming.get('id')!=old['id'] or incoming.get('revision')!=old['revision']:raise FinanceError('This account has changed. Reload before saving.',409)
        if old['status'] not in ('draft','returned'):raise FinanceError('Submitted or approved accounts cannot be edited.',409)
    elif incoming.get('id'):raise FinanceError('The financial report does not exist.',404)
    rows=incoming.get('rows',[])
    if not isinstance(rows,list) or len(rows)>100:raise FinanceError('A report supports up to 100 transactions.')
    clean=[];totals={'income':0,'expense':0}
    for row in rows:
        if not isinstance(row,dict) or row.get('kind') not in totals:raise FinanceError('Choose income or expense for each transaction.')
        description=text(row.get('description',''),1000)
        amount=cents(row.get('amount') or '0.00')
        ref=text(row.get('budget_ref','unplanned'),100)
        if ref!='unplanned':
            match=re.fullmatch(r'(revenue|expenses):(\d+)',ref)
            key='revenue' if row['kind']=='income' else 'expenses'
            if not match or match[1]!=key or int(match[2])>=len(proposal.get(key,[])):raise FinanceError('Select a matching proposal budget item or mark this transaction unplanned.')
        evidence=row.get('evidence_ids',[])
        if not isinstance(evidence,list) or len(evidence)>20 or any(not isinstance(v,str) for v in evidence) or len(set(evidence))!=len(evidence):raise FinanceError('Evidence references are invalid.')
        for rid in evidence:
            if app.get('receipt',rid)['proposal_id']!=proposal_id:raise FinanceError('Evidence must belong to this event.',403)
        clean.append(dict(kind=row['kind'],description=description,amount=money(amount),amount_cents=amount,budget_ref=ref,evidence_ids=evidence));totals[row['kind']]+=amount
    stamp=auth.now();report=dict(id=old['id'] if old else secrets.token_hex(12),proposal_id=proposal_id,club_id=club['id'],revision=old['revision']+1 if old else 1,
        status='draft',rows=clean,variance_reason=text(incoming.get('variance_reason',''),5000),actual_income=money(totals['income']),actual_expenses=money(totals['expense']),
        created_at=old['created_at'] if old else stamp,created_by=old['created_by'] if old else user['email'],updated_at=stamp,updated_by=user['email'],history=old.get('history',[]) if old else [])
    app.put('finance_report',report);app.log(user,'finance_draft_saved',proposal_id,club['id'])
    return {'report':report}


def transition(app,user,report_id,data,review=False):
    report=app.get('finance_report',report_id);proposal,club,_=context(app,user,report['proposal_id'],not review)
    if data.get('revision')!=report['revision']:raise FinanceError('The financial report changed. Reload it before continuing.',409)
    stamp=auth.now()
    if review:
        if user['role']!='sld':raise FinanceError('Only SLD may review actual accounts.',403)
        if report['status']!='pending_sld':raise FinanceError('This financial report is not awaiting SLD review.',409)
        action=data.get('action');comment=text(data.get('comment',''),5000);reviewer=app.reviewer_profile(user,'sld');name=reviewer['name']
        if action not in ('approve','return') or (action=='return' and not comment):raise FinanceError('Choose a review decision and provide a reason when returning a report.')
        if action=='approve':
            try:
                end=datetime.fromisoformat((proposal.get('end_date') or proposal['date'])+'T'+proposal['end_time']).replace(tzinfo=MYT)
                if datetime.fromisoformat(stamp)<end:raise FinanceError('Actual accounts can be approved only after the event ends.')
            except (KeyError,ValueError):raise FinanceError('The approved event needs a valid end schedule before its accounts can be approved.')
            import evidence
            try:evidence.require_photos(app,'proposal',proposal['id'],2)
            except Exception as exc:
                from server import APIError
                if isinstance(exc,APIError):raise FinanceError(str(exc),exc.status,exc.code,exc.fields)
                raise
        report['status']='approved' if action=='approve' else 'returned'
        history=dict(action=action,actor=user['email'],name=name,designation=reviewer['designation'],department=reviewer['department'],timestamp=stamp,comment=comment,revision=report['submitted_revision'],digest=report['submitted_digest'])
        report['history'].append(history)
        if action=='approve':
            report['approved_at']=stamp;report['approved_by']=user['email']
            ledger=[]
            for index,row in enumerate(report['rows']):
                ledger.append(('ledger_entry',dict(row,id=report_id+'-'+str(index),report_id=report_id,proposal_id=proposal['id'],club_id=club['id'],approved_at=stamp,approved_by=user['email'])))
        else:ledger=[]
    else:
        if report['status'] not in ('draft','returned'):raise FinanceError('The report has already been submitted.',409)
        if data.get('confirm_submission') is not True:raise FinanceError('Confirm the financial report before sending it to SLD.',code='CONFIRMATION_REQUIRED')
        if not report['rows'] or any(not row['description'] or row['amount_cents']<=0 or not row['evidence_ids'] for row in report['rows']):
            raise FinanceError('Each transaction needs a description, a positive amount and receipt or supporting evidence.')
        assigned=defaultdict(int)
        for row in report['rows']:assigned[row['budget_ref']]+=row['amount_cents']
        item_variance=any(assigned[key+':'+str(i)]!=planned({key:[item]},key) for key in ('revenue','expenses') for i,item in enumerate(proposal.get(key,[])))
        differing=(cents(report['actual_income'])!=planned(proposal,'revenue') or cents(report['actual_expenses'])!=planned(proposal,'expenses') or item_variance or any(r['budget_ref']=='unplanned' for r in report['rows']))
        if differing and not report['variance_reason']:raise FinanceError('Explain the difference between proposed and actual accounts, including unplanned transactions.',fields={'variance_reason':'Explain the budget variance.'})
        report.update(status='pending_sld',submitted_at=stamp,submitted_revision=report['revision'],submitted_by=user['email'])
        snapshot={k:report[k] for k in ('proposal_id','club_id','rows','variance_reason','actual_income','actual_expenses','submitted_at','submitted_revision','submitted_by')}
        report['submitted_snapshot']=snapshot;report['submitted_digest']=hashlib.sha256(json.dumps(snapshot,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        ledger=[('finance_version',dict(id=report_id+'-'+str(report['revision']),report_id=report_id,snapshot=snapshot,digest=report['submitted_digest']))]
    report['revision']+=1;report['updated_at']=stamp;report['updated_by']=user['email']
    app.put_batch([('finance_report',report)]+ledger);app.log(user,'finance_'+('approved' if report['status']=='approved' else 'returned' if review else 'submitted'),proposal['id'],club['id'])
    return {'report':report}


def upload(app,user,data):
    proposal,club,_=context(app,user,text(data.get('proposal_id',''),100),True)
    existing=report_for(app,proposal['id'])
    if existing and existing['status'] not in ('draft','returned'):raise FinanceError('Evidence is locked while the report is submitted or approved.',409)
    filename=text(data.get('filename',''),180).replace('\\','/').split('/')[-1]
    filename=re.sub(r'[^\w .()-]','_',filename)
    if not filename or filename.startswith('.'):raise FinanceError('Choose a valid evidence filename.')
    mime=data.get('mime');encoded=data.get('content_base64','')
    if not isinstance(encoded,str) or len(encoded)>2800000:raise FinanceError('Evidence must be 2 MB or smaller.')
    try:raw=base64.b64decode(encoded,validate=True)
    except ValueError:raise FinanceError('The evidence encoding is invalid.')
    valid={'application/pdf':raw.startswith(b'%PDF-'),'image/png':raw.startswith(b'\x89PNG\r\n\x1a\n'),'image/jpeg':raw.startswith(b'\xff\xd8\xff'),'image/webp':raw.startswith(b'RIFF') and raw[8:12]==b'WEBP'}
    if not valid.get(mime) or len(raw)>2*1024*1024:raise FinanceError('Upload a PDF, PNG, JPEG or WebP file, no larger than 2 MB.')
    receipt=dict(id=secrets.token_hex(12),proposal_id=proposal['id'],club_id=club['id'],filename=filename,mime=mime,size=len(raw),content_base64=encoded,
                 sha256=hashlib.sha256(raw).hexdigest(),uploaded_at=auth.now(),uploaded_by=user['email'])
    app.put('receipt',receipt);app.log(user,'finance_evidence_uploaded',proposal['id'],club['id']);return {'receipt':receipt_metadata(receipt)}


def opening(app,user,data):
    if user['role']!='sld':raise FinanceError('Only SLD may approve an opening balance.',403)
    club=app.get('club',text(data.get('club_id',''),100))
    if club['status']!='approved':raise FinanceError('Approve the club registration before entering an opening balance.')
    if any(r['club_id']==club['id'] for r in app.all('finance_opening')):raise FinanceError('The opening balance has already been recorded and cannot be overwritten.',409)
    reason=text(data.get('reason',''),5000)
    if not reason:raise FinanceError('Provide the source and reason for the opening balance.')
    amount=cents(data.get('amount','0.00'),signed=True)
    record=dict(id=club['id'],club_id=club['id'],amount_cents=amount,amount=money(amount),reason=reason,approved_by=user['email'],approved_at=auth.now())
    app.put('finance_opening',record);app.log(user,'finance_opening_approved',club['id'],club['id']);return club_view(app,user,club['id'])


def handle_get(app,user,path,query):
    if path=='/api/finance':return club_view(app,user,(query.get('club_id') or [''])[0])
    match=re.fullmatch(r'/api/proposals/([\w-]+)/finance',path)
    if match:return event_view(app,user,match[1])
    match=re.fullmatch(r'/api/receipts/([\w-]+)',path)
    if match:
        receipt=app.get('receipt',match[1]);context(app,user,receipt['proposal_id'])
        return base64.b64decode(receipt['content_base64']),receipt['mime'],receipt['filename']
    match=re.fullmatch(r'/api/finance/reports/([\w-]+)/export/pdf',path)
    if match:
        report=app.get('finance_report',match[1]);proposal,club,_=context(app,user,report['proposal_id'])
        import exports
        return exports.finance_pdf(report,proposal,club),'application/pdf','event-financial-report.pdf'


def handle_post(app,user,path,data):
    if path=='/api/finance/reports':return save_report(app,user,data)
    if path=='/api/receipts':return upload(app,user,data)
    if path=='/api/finance/opening':return opening(app,user,data)
    match=re.fullmatch(r'/api/finance/reports/([\w-]+)/(submit|review)',path)
    if match:return transition(app,user,match[1],data,match[2]=='review')
