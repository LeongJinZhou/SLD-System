"""Revisioned weekly/AGM reports with four distinct bound signatories."""
import copy,hashlib,json,re,secrets,uuid
from datetime import datetime,date,time,timezone,timedelta
import auth
MYT=timezone(timedelta(hours=8))
FIELDS=frozenset(('type','report_year','club_id','title','semester','date','start_time','end_time','venue','activity_kind','summary','objectives','attendance','minutes','decisions','next_meeting','new_committee','opening_speech','agenda','election_summary','outgoing_activities','adjournment','member_count'))
STAGES={'pending_secretary':'secretary','pending_advisor':'advisor','pending_sld':'sld'}
POSITIONS=('President','Vice President','Secretary','Treasurer')


def error(message,status=400,code=None,fields=None):
 from server import APIError
 raise APIError(message,status,code,fields)


def visible(app,user,club):
 return bool(user and (user['role']=='sld' or club.get('advisor_email')==user['email'] or any(p.get('email')==user['email'] for p in club.get('committee',[]))))


def committee(user,club):
 return any(p.get('email')==user['email'] for p in club.get('committee',[]))


def roster(members):
 return sorted((member.get('email',''),member.get('position','').lower()) for member in members)


def position_email(club,position):
 found=[p.get('email') for p in club.get('committee',[]) if p.get('position','').lower()==position.lower()]
 return found[0] if len(found)==1 else None


def schedule(report):
 try:
  if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',report.get('date','')):raise ValueError()
  day=date.fromisoformat(report['date'])
  times=[]
  for key in ('start_time','end_time'):
   value=report.get(key,'')
   if not re.fullmatch(r'\d{2}:\d{2}(?::\d{2})?',value):raise ValueError()
   times.append(datetime.combine(day,time.fromisoformat(value),MYT))
  if times[1]<=times[0]:raise ValueError()
  return tuple(times)
 except (ValueError,TypeError,KeyError):return None


def canonical(app,source,club):
 from server import bounded,text
 r=bounded({key:value for key,value in source.items() if key in FIELDS})
 if r.get('type','weekly') not in ('weekly','agm'):error('Choose weekly or AGM report.',fields={'type':'Choose a report type.'})
 r['type']=r.get('type','weekly');r['club_id']=club['id']
 if r['type']=='agm':
  default_year=int(str(source.get('date',''))[:4]) if re.fullmatch(r'\d{4}-\d{2}-\d{2}',source.get('date','')) else datetime.fromisoformat(auth.now()).astimezone(MYT).year
  r['report_year']=source.get('report_year',default_year)
  if type(r['report_year']) is not int or not 1900<=r['report_year']<=2100:error('Choose a valid annual report year.',fields={'report_year':'Choose a year from 1900 to 2100.'})
 else:r['report_year']=None
 for key in ('title','semester','date','start_time','end_time','venue','summary','minutes','opening_speech','election_summary','outgoing_activities','adjournment'):
  r[key]=text(r.get(key,club.get('semester','') if key=='semester' else ''),20000 if key in ('minutes','summary','outgoing_activities') else 5000)
 r['activity_kind']=r.get('activity_kind','meeting')
 if r['activity_kind'] not in ('meeting','training','activity'):error('Choose a valid activity kind.',fields={'activity_kind':'Choose meeting, training or activity.'})
 identities={p['email']:p for p in app.contacts()+app.all('directory_identity')+app.all('user') if p.get('email')}
 if app.preview:identities.update({p['email']:auth.preview_user(p['id'].removeprefix('preview-')) for p in auth.PREVIEW_PEOPLE})
 objectives=r.get('objectives',[])
 if isinstance(objectives,str):objectives=objectives.splitlines()
 if not isinstance(objectives,list) or len(objectives)>30 or any(not isinstance(item,str) for item in objectives): error('Objectives must be a list.',fields={'objectives':'Use an objective list.'})
 r['objectives']=[text(item,2000) for item in objectives if isinstance(item,str) and item.strip()]
 for key,limit in (('attendance',2000),('decisions',100),('new_committee',30),('agenda',100)):
  rows=r.get(key,[])
  if not isinstance(rows,list) or len(rows)>limit or any(not isinstance(row,dict) for row in rows):error('Invalid '+key+' rows.',fields={key:'Check the row format.'})
  r[key]=[]
  seen=set()
  for row in rows:
   if key=='attendance':
    email=text(row.get('email',''),250).lower();status=row.get('status','present')
    if email and not auth.university_email(email):error('Attendance requires QIU email addresses.',fields={key:'Check QIU addresses.'})
    if email and email in seen:error('Attendance identities must be unique.',fields={key:'Remove duplicate students.'})
    if status not in ('present','absent'):error('Attendance status must be present or absent.',fields={key:'Choose an attendance status.'})
    person=identities.get(email,{})
    r[key].append(dict(email=email,name=person.get('name') or text(row.get('name',''),250),status=status,university_id=person.get('university_id',''),programme=person.get('programme','')));seen.add(email)
   elif key=='new_committee':
    email=text(row.get('email',''),250).lower();position=text(row.get('position',''),100)
    if email and not auth.university_email(email):error('New committee requires QIU email addresses.',fields={key:'Choose QIU identities.'})
    person=identities.get(email,{})
    r[key].append(dict(email=email,position=position,name=person.get('name',''),university_id=person.get('university_id','')))
   else:
    keys=('task','person','deadline') if key=='decisions' else ('start','end','agenda')
    r[key].append({k:text(row.get(k,''),2000) for k in keys})
 next_meeting=r.get('next_meeting',{})
 if not isinstance(next_meeting,dict):error('Invalid next meeting fields.')
 r['next_meeting']={k:text(next_meeting.get(k,''),500) for k in ('date','time','venue')}
 if 'member_count' in r and r['member_count'] not in ('',None):
  if type(r['member_count']) is not int or not 0<=r['member_count']<=10000:error('Member count must be a nonnegative whole number.',fields={'member_count':'Enter a whole member count.'})
 else:r['member_count']=None
 return r


def progress(r,club):
 checks=[]
 def add(key,label,complete,step=0):checks.append(dict(field=key,label=label,complete=bool(complete),required=True,step=step))
 for key,label in (('title','Report title'),('semester','Semester'),('venue','Venue'),('summary','Purpose / summary')):add(key,label,r.get(key))
 planned=schedule(r);now=datetime.fromisoformat(auth.now())
 add('date','Completed activity date and times',planned and planned[1]<=now)
 sport='sport' in club.get('category','').lower()
 if r['type']=='agm' or sport:
  attendance=r.get('attendance',[])
  add('attendance','Present and absent attendance',attendance and all(p.get('email') and p.get('name') and p.get('status') in ('present','absent') for p in attendance),1)
 if r['type']=='weekly' and not sport:add('minutes','Meeting / activity discussion',r.get('minutes'),1)
 if r['type']=='agm':
  add('objectives','AGM objectives',r.get('objectives'),1)
  add('election_summary','Election summary',r.get('election_summary'),1)
  add('outgoing_activities','Outgoing committee accomplishments',r.get('outgoing_activities'),1)
  members=r.get('new_committee',[]);emails=[m.get('email') for m in members];positions=[m.get('position','').lower() for m in members]
  add('new_committee','Four distinct directory-verified new officers',all(positions.count(p.lower())==1 for p in POSITIONS) and len(emails)==len(set(emails)) and all(m.get('name') and m.get('email') for m in members) and club.get('advisor_email') not in emails,1)
 if r.get('decisions'):
  valid=bool(planned)
  for row in r['decisions']:
   if not planned:valid=False;break
   try:
    deadline=date.fromisoformat(row.get('deadline',''))
    valid=valid and bool(row.get('task') and row.get('person')) and deadline>=planned[0].date()
   except (ValueError,TypeError):valid=False
  add('decisions','Action items with dates on or after the activity',valid,1)
 if r['type']=='agm' and r.get('agenda'):
  valid=bool(planned);previous_end=planned[0] if planned else None
  for row in r['agenda']:
   if not planned:valid=False;break
   try:
    begin=datetime.combine(planned[0].date(),time.fromisoformat(row.get('start','')),MYT)
    finish=datetime.combine(planned[0].date(),time.fromisoformat(row.get('end','')),MYT)
    valid=valid and bool(row.get('agenda')) and begin>=previous_end and finish>begin and finish<=planned[1]
    previous_end=finish
   except (ValueError,TypeError):valid=False
  add('agenda','Chronological AGM agenda within meeting times',valid,1)
 if any(r.get('next_meeting',{}).values()):
  row=r['next_meeting'];valid=False
  try:
   next_start=datetime.combine(date.fromisoformat(row['date']),time.fromisoformat(row['time']),MYT)
   valid=bool(row['venue'] and planned and next_start>planned[1])
  except (KeyError,ValueError,TypeError):pass
  add('next_meeting','Complete next meeting scheduled after this activity',valid,1)
 if r.get('member_count') is not None:add('member_count','Member count includes the attendance list',r['member_count']>=len(r.get('attendance',[])),1)
 count=sum(c['complete'] for c in checks)
 return dict(completed=count,total=len(checks),percent=round(100*count/len(checks)),checklist=checks)


def signing_slot(app,r,club,user):
 if not visible(app,user,club):return None
 if r['status'] in ('draft','returned'):
  return 'president' if position_email(club,'President')==user['email'] else None
 slot=STAGES.get(r['status']);assign=r.get('signer_assignments',{})
 if not slot:return None
 if slot=='sld':eligible=user['role']=='sld' and not committee(user,club) and user['email']!=club.get('advisor_email')
 else:eligible=assign.get(slot)==user['email'] and (position_email(club,'Secretary')==user['email'] if slot=='secretary' else club.get('advisor_email')==user['email'])
 if not eligible or any(s.get('email')==user['email'] for s in r.get('signatures',{}).values()):return None
 return slot


def handover_blocked(app,r,club):
 if club.get('handover_status')=='overlap' and club.get('committee_handover',{}).get('report_id')!=r['id']:return 'An approved committee handover is already in its overlap period.'
 if roster(r.get('old_committee',[]))!=roster(club['committee']):return 'The current committee changed. Create and approve an AGM for the current handover.'
 new_secretary=position_email({'committee':r.get('new_committee',[])},'Secretary')
 for other in app.all('club_report'):
  if other['id']!=r['id'] and other.get('club_id')==club['id'] and other.get('status')=='pending_secretary' and other.get('signer_assignments',{}).get('secretary')!=new_secretary:
   return 'The assigned Secretary must review or return pending reports before SLD can apply this handover.'
 return None


def signer_profile(app,user,club,slot):
 if slot in ('president','secretary'):
  return dict(name=user.get('name') or 'Unavailable',designation=club['name']+' · '+('President' if slot=='president' else 'Secretary'),department=club['name'],email=user['email'])
 return app.reviewer_profile(user,slot)


def decorate(app,r,user,club):
 slot=signing_slot(app,r,club,user);p=progress(r,club)
 returned=next((h for h in reversed(r.get('history',[])) if h.get('action')=='return'),None) if r['status']=='returned' else None
 next_action={'draft':'Committee completes report; President signs and submits.','returned':'Committee corrects report; President signs a new version.','pending_secretary':'Secretary reviews and signs.','pending_advisor':'Assigned advisor reviews and signs.','pending_sld':'SLD reviews and signs.','approved':'Approved completed activity report.'}[r['status']]
 stale_agm=r['type']=='agm' and r['status'] in ('draft','returned') and roster(r.get('old_committee',[]))!=roster(club['committee'])
 if stale_agm:next_action='The committee changed. Refresh the outgoing committee before completing this annual report.'
 return dict(r,report_year=report_year(r) if r['type']=='agm' else None,can_rebase=stale_agm and committee(user,club),can_edit=committee(user,club) and r['status'] in ('draft','returned'),can_sign=bool(slot) and not stale_agm,signing_slot=slot,signer_profile=signer_profile(app,user,club,slot) if slot else None,progress=p,return_context={k:returned.get(k) for k in ('stage','comment','timestamp','actor')} if returned else None,next_action=next_action,can_apply_handover=user['role']=='sld' and r['type']=='agm' and r['status']=='approved' and not r.get('handover_applied_at') and not handover_blocked(app,r,club),handover_blocked_reason=handover_blocked(app,r,club) if r['type']=='agm' and r['status']=='approved' and not r.get('handover_applied_at') else None)


def list_for(app,user):
 clubs={c['id']:c for c in app.all('club')}
 return [decorate(app,r,user,clubs[r['club_id']]) for r in app.all('club_report') if r.get('club_id') in clubs and visible(app,user,clubs[r['club_id']])]


def handle_get(app,user,path,query):
 if path=='/api/weekly-tracker':return weekly_tracker(app,user,query.get('week_start',[datetime.fromisoformat(auth.now()).astimezone(MYT).date().isoformat()])[0])
 if path=='/api/agm-tracker':
  try:year=int(query.get('year',[datetime.fromisoformat(auth.now()).astimezone(MYT).year])[0])
  except (TypeError,ValueError):error('Choose a valid year.')
  return annual_tracker(app,user,year)
 if path=='/api/club-reports':return dict(reports=list_for(app,user))
 match=re.fullmatch(r'/api/club-reports/([A-Za-z0-9_-]+)(/export)?',path)
 if not match:return None
 r=app.get('club_report',match[1]);club=app.get('club',r['club_id'])
 if not visible(app,user,club):error('You cannot access this report.',403)
 if not match[2]:return dict(report=decorate(app,r,user,club))
 import exports
 fmt=query.get('format',['pdf'])[0]
 if fmt=='pdf':return exports.club_report_pdf(r,club),'application/pdf',r['type']+'-report.pdf'
 if fmt=='docx' and hasattr(exports,'club_report_docx'):return exports.club_report_docx(r,club),'application/vnd.openxmlformats-officedocument.wordprocessingml.document',r['type']+'-report.docx'
 error('Unsupported report export format.')


def handle_post(app,user,path,data):
 from server import image,text
 if path=='/api/club-reports':
  source=data.get('report')
  if not isinstance(source,dict):error('Report form is required.')
  for key in ('id','club_id'):
   if source.get(key) is not None and (not isinstance(source[key],str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',source[key])):error('Invalid report identifier.',fields={key:'Choose a valid report or club.'})
  if source.get('id') and type(source.get('revision')) is not int:error('Report revision must be a whole number.')
  previous=app.get('club_report',source['id']) if source.get('id') else None
  club=app.get('club',previous['club_id'] if previous else source.get('club_id',''))
  if club['status']!='approved' or not committee(user,club):error('Only current committees of approved clubs can edit reports.',403)
  if previous and source.get('club_id',club['id'])!=club['id']:error('The organizing club cannot change.',403)
  if previous and previous['status'] not in ('draft','returned'):error('Submitted report content is locked.',409)
  if previous and source.get('revision')!=previous['revision']:error('This report changed. Reopen its latest revision.',409)
  mapping=None
  if not previous and source.get('creation_key'):
   try:key=str(uuid.UUID(source['creation_key']))
   except (ValueError,TypeError,AttributeError):error('Use a valid draft creation key.')
   mapping_id=hashlib.sha256((user['email']+'|'+club['id']+'|'+key).encode()).hexdigest()
   old=next((m for m in app.all('report_creation') if m['id']==mapping_id),None)
   if old:
    existing=app.get('club_report',old['report_id'])
    if existing['revision']!=1:error('The recovered report changed. Reopen its latest revision.',409,'CREATION_REPLAY_CONFLICT')
    return dict(report=decorate(app,existing,user,club),creation_replayed=True)
   mapping=dict(id=mapping_id)
  r=canonical(app,dict(source,report_year=source.get('report_year',report_year(previous))) if previous and previous['type']=='agm' and report_year(previous) is not None else source,club)
  if previous and r['type']!=previous['type']:error('Report type cannot change.',409)
  if r['type']=='agm':
   duplicates=[other for other in app.all('club_report') if other['id']!=(previous or {}).get('id') and other.get('type')=='agm' and other.get('club_id')==club['id'] and report_year(other)==r['report_year']]
   if duplicates:error('An AGM report already exists for this club and year. Continue its existing report.',409,'ANNUAL_REPORT_EXISTS',{'report_year':'Open the existing annual report.'})
  stamp=auth.now();r.update(id=previous['id'] if previous else secrets.token_urlsafe(12),status=previous['status'] if previous else 'draft',revision=previous['revision']+1 if previous else 1,created_at=previous['created_at'] if previous else stamp,updated_at=stamp,owner_email=previous['owner_email'] if previous else user['email'],history=previous.get('history',[]) if previous else [],signatures={},old_committee=copy.deepcopy(previous['old_committee'] if previous else club['committee']),old_advisor_email=previous.get('old_advisor_email',club['advisor_email']) if previous else club['advisor_email'])
  if previous and previous.get('photo_evidence'):r['photo_evidence']=copy.deepcopy(previous['photo_evidence'])
  records=[('club_report',r)]
  if mapping:mapping['report_id']=r['id'];records.append(('report_creation',mapping))
  app.put_batch(records);app.log(user,'club_report_draft_saved',r['id'],club['id'])
  return dict(report=decorate(app,r,user,club))
 match=re.fullmatch(r'/api/club-reports/([A-Za-z0-9_-]+)/(submit|review|apply-handover|rebase)',path)
 if not match:return None
 r=app.get('club_report',match[1]);club=app.get('club',r['club_id'])
 if not visible(app,user,club):error('You cannot access this report.',403)
 if type(data.get('revision')) is not int:error('Report revision must be a whole number.')
 if data.get('revision')!=r['revision']:error('This report changed. Reopen its latest revision.',409)
 stamp=auth.now();records=[];action=match[2]
 if action=='rebase':
  if r['type']!='agm' or r['status'] not in ('draft','returned') or not committee(user,club):error('Only the current committee can refresh an editable AGM outgoing roster.',403)
  if roster(r.get('old_committee',[]))==roster(club['committee']):error('The outgoing committee is already current.',409)
  r=copy.deepcopy(r);r.update(old_committee=copy.deepcopy(club['committee']),old_advisor_email=club.get('advisor_email'),revision=r['revision']+1,updated_at=stamp,signatures={})
  r.setdefault('history',[]).append(dict(action='rebase',actor=user['email'],timestamp=stamp))
  app.put('club_report',r);app.log(user,'club_report_roster_refreshed',r['id'],club['id'])
  return dict(report=decorate(app,r,user,club))
 if action=='apply-handover':
  if user['role']!='sld':error('Only SLD can apply a committee handover.',403)
  if r['type']!='agm' or r['status']!='approved' or r.get('handover_applied_at'):error('Only an approved AGM can be applied once.',409)
  blocked=handover_blocked(app,r,club)
  if blocked:error(blocked,409)
  if type(data.get('club_revision')) is not int:error('Club revision must be a whole number.')
  if data.get('club_revision')!=club['revision']:error('The club changed. Check its current committee before applying handover.',409)
  validated=canonical(app,r,club)
  if not next(c['complete'] for c in progress(validated,club)['checklist'] if c['field']=='new_committee'):error('The approved new committee is no longer valid.')
  club=copy.deepcopy(club);days=app.settings()['handover_days'];club['committee_handover']=dict(starts_at=stamp,ends_at=(datetime.fromisoformat(stamp)+timedelta(days=days)).isoformat(),days=days,report_id=r['id'],outgoing=copy.deepcopy(club['committee']),incoming=copy.deepcopy(r['new_committee']))
  club.update(revision=club['revision']+1,updated_at=stamp)
  club.setdefault('history',[]).append(dict(action='agm_handover',report_id=r['id'],actor=user['email'],timestamp=stamp))
  r.update(handover_applied_at=stamp,handover_applied_by=user['email'],revision=r['revision']+1,updated_at=stamp)
  records=[('club',club),('club_report',r),('club_hierarchy',dict(id=club['id']+'-'+str(report_year(r)),club_id=club['id'],year=report_year(r),committee=copy.deepcopy(r['old_committee']),incoming=copy.deepcopy(r['new_committee']),report_id=r['id'],approved_at=r.get('approved_at'),effective_at=club['committee_handover']['ends_at']))];app.put_batch(records);app.log(user,'club_report_handover_applied',r['id'],club['id'])
  return dict(report=decorate(app,r,user,club),club=app.decorate_club(app.effective_club(club),user))
 if action=='review' and r['status'] in ('draft','returned','approved'):error('This report is not awaiting a review.',409)
 slot=signing_slot(app,r,club,user)
 if action=='submit':
  if slot!='president' or r['status'] not in ('draft','returned'):error('Only the current President may sign and submit a draft report.',403)
  if r['type']=='agm' and roster(r['old_committee'])!=roster(club['committee']):error('The current committee changed since this AGM draft was created. Create a fresh AGM draft.',409)
  import evidence
  evidence.require_photos(app,'club_report',r['id'],1 if r['type']=='agm' else 2)
  errors={c['field']:c['label']+' is required.' for c in progress(r,club)['checklist'] if not c['complete']}
  if errors:error('Complete the required report fields before signing.',fields=errors)
  president=position_email(club,'President');secretary=position_email(club,'Secretary');advisor=club['advisor_email']
  if not secretary or len({president,secretary,advisor})!=3:error('President, Secretary and advisor must be three distinct assigned people.',409)
  r.update(status='pending_secretary',revision=r['revision']+1,updated_at=stamp,submitted_at=stamp,signer_assignments=dict(president=president,secretary=secretary,advisor=advisor),signatures={})
  signer=dict(signer_profile(app,user,club,'president'),slot='president',signature=image(data.get('signature',''),True,True),signed_at=stamp,revision=r['revision'])
  r['signatures']={'president':signer}
  snapshot=copy.deepcopy({k:v for k,v in r.items() if k not in ('history','submitted_revision','submitted_digest')})
  digest=hashlib.sha256(json.dumps(snapshot,sort_keys=True).encode()).hexdigest();signer['digest']=digest
  r.update(submitted_revision=r['revision'],submitted_digest=digest)
  r['history'].append(dict(action='submitted',stage='president',actor=user['email'],timestamp=stamp,revision=r['submitted_revision'],digest=digest,signer=copy.deepcopy(signer)))
  records=[('club_report_version',dict(id=r['id']+'-r'+str(r['revision']),report_id=r['id'],snapshot=snapshot,digest=digest))]
 else:
  if not slot or slot=='president':error('This signing stage is not assigned to you.',403)
  choice=data.get('action');comment=text(data.get('comment',''),5000)
  if choice not in ('approve','return'):error('Choose approve or return.')
  if choice=='return' and not comment:error('A correction reason is required.')
  if choice=='approve':
   if slot=='advisor' and data.get('confirm_submission') is not True:error('Confirm submission to SLD before continuing.',409,'CONFIRMATION_REQUIRED')
   expected=['president']+(['secretary'] if slot in ('advisor','sld') else [])+(['advisor'] if slot=='sld' else [])
   if any(k not in r.get('signatures',{}) or r['signatures'][k].get('revision')!=r.get('submitted_revision') or r['signatures'][k].get('digest')!=r.get('submitted_digest') for k in expected):error('Earlier signatures are missing or not bound to this submitted version.',409,'SIGNATURE_REQUIRED')
   signer=dict(signer_profile(app,user,club,slot),slot=slot,signature=image(data.get('signature',''),True,True),signed_at=stamp,revision=r['submitted_revision'],digest=r['submitted_digest'])
   r['signatures'][slot]=signer;r['status']={'secretary':'pending_advisor','advisor':'pending_sld','sld':'approved'}[slot]
   if slot=='sld':r['approved_at']=stamp
  else:signer=None;r['status']='returned';r['signatures']={}
  r['history'].append(dict(action=choice,stage=slot,actor=user['email'],timestamp=stamp,comment=comment,signer=copy.deepcopy(signer),revision=r['submitted_revision'],digest=r['submitted_digest']))
  r.update(revision=r['revision']+1,updated_at=stamp)
 records.append(('club_report_signature',dict(signer,id=r['id']+'-r'+str(r['submitted_revision'])+'-'+slot,report_id=r['id'],club_id=club['id']))) if signer else None
 records.append(('club_report',r));app.put_batch(records);app.log(user,'club_report_'+('submitted' if action=='submit' else ('returned' if data['action']=='return' else slot+'_approved')),r['id'],club['id'])
 return dict(report=decorate(app,r,user,club))


def report_year(report):
 if type(report.get('report_year')) is int:return report['report_year']
 try:return date.fromisoformat(report.get('date','')).year
 except (ValueError,TypeError):return None

def annual_tracker(app,user,year):
 if user['role']!='sld':error('Only SLD can view annual submission tracking.',403)
 if type(year) is not int or not 1900<=year<=2100:error('Choose a year from 1900 to 2100.')
 reports=[r for r in app.all('club_report') if r.get('type')=='agm' and report_year(r)==year]
 rows=[]
 for club in app.all('club'):
  if club.get('status')!='approved':continue
  matches=[r for r in reports if r.get('club_id')==club['id']]
  selected=max(matches,key=lambda r:(r.get('status')=='approved',r.get('updated_at','')),default=None)
  rows.append(dict(club_id=club['id'],club_name=club['name'],report_year=year,status=selected['status'] if selected else 'missing',report_id=selected['id'] if selected else None))
 summary={state:sum(r['status']==state for r in rows) for state in ('missing','approved','draft','returned')}
 summary['pending']=sum(r['status'].startswith('pending_') for r in rows)
 return dict(year=year,clubs=rows,summary=summary)


def weekly_tracker(app,user,week_start):
 if user['role']!='sld':error('Only SLD can view weekly submission tracking.',403)
 try:
  if not isinstance(week_start,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',week_start):raise ValueError()
  start=date.fromisoformat(week_start);start-=timedelta(days=start.weekday());end=start+timedelta(days=6)
 except (ValueError,TypeError,OverflowError):error('Choose a valid week date.',fields={'week_start':'Use YYYY-MM-DD.'})
 priority={'pending_sld':0,'pending_advisor':1,'pending_secretary':2,'returned':3,'draft':4,'approved':5}
 reports=[]
 for report in app.all('club_report'):
  if report.get('type')!='weekly':continue
  try:day=date.fromisoformat(report.get('date',''))
  except (ValueError,TypeError):continue
  if start<=day<=end:reports.append(report)
 rows=[]
 for club in app.all('club'):
  if club.get('status')!='approved':continue
  matches=sorted([r for r in reports if r.get('club_id')==club['id']],key=lambda r:(priority.get(r.get('status'),99),r.get('date',''),r['id']))
  selected=matches[0] if matches else None
  rows.append(dict(club_id=club['id'],club_name=club['name'],status=selected['status'] if selected else 'missing',report_id=selected['id'] if selected else None,report_ids=[r['id'] for r in matches],report_count=len(matches),approved_count=sum(r.get('status')=='approved' for r in matches)))
 summary={state:sum(r['status']==state for r in rows) for state in ('missing','approved','draft','returned')}
 summary.update(pending=sum(r['status'].startswith('pending_') for r in rows),report_count=sum(r['report_count'] for r in rows),approved_count=sum(r['approved_count'] for r in rows))
 return dict(week_start=start.isoformat(),week_end=end.isoformat(),clubs=rows,summary=summary)
