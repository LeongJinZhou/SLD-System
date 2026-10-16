"""Authenticated public projections, distinct from private operational records."""
import hashlib,re
import auth,performance
from datetime import datetime,date,time
from club_reports import MYT

def profile_id(email):
 return hashlib.sha256(('qiu-public-profile|'+email.lower()).encode()).hexdigest()[:32]

def identities(app):
 people={}
 for person in app.contacts()+app.all('directory_identity')+app.all('user'):
  if person.get('email'):people.setdefault(person['email'],{}).update(person)
 if app.preview:
  for person in auth.PREVIEW_PEOPLE:
   people.setdefault(person['email'],auth.preview_user(person['id'].removeprefix('preview-')))
 return people

def safe_person(person,email,position=None):
 photo=person.get('photo','')
 if not (auth.safe_photo(photo) or re.fullmatch(r'/web/avatars/(student|advisor|sld|vice|secretary|treasurer|visitor)\.svg',photo)):photo=''
 result=dict(profile_id=profile_id(email),name=person.get('name') or 'Unavailable',photo=photo)
 if position:result['position']=position
 return result

def upcoming_weekly(app,club_id):
 now=datetime.fromisoformat(auth.now());planned={}
 for report in sorted(app.all('club_report'),key=lambda r:r['id']):
  if report.get('club_id')!=club_id or report.get('type')!='weekly' or report.get('status')!='approved':continue
  meeting=report.get('next_meeting',{})
  if not isinstance(meeting,dict):continue
  try:
   day=meeting.get('date','');clock=meeting.get('time','');venue=meeting.get('venue','')
   if not isinstance(venue,str) or not venue.strip() or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',day) or not re.fullmatch(r'\d{2}:\d{2}(?::\d{2})?',clock):continue
   start=datetime.combine(date.fromisoformat(day),time.fromisoformat(clock),MYT)
   if start<=now:continue
  except (ValueError,TypeError):continue
  key=(start.isoformat(),venue.strip().casefold())
  planned.setdefault(key,dict(report_id=report['id'],title='Next club meeting',date=day,time=start.strftime('%H:%M:%S') if start.second else start.strftime('%H:%M'),venue=venue.strip(),occurrence='scheduled'))
 return [planned[key] for key in sorted(planned)]

def public_club(app,club,detail=False):
 people=identities(app);members=[]
 for member in club.get('committee',[]):
  email=member.get('email','');person=people.get(email,{})
  members.append(safe_person(person,email,member.get('position','Committee')))
 advisor=club.get('advisor_email','')
 if advisor:members.append(safe_person(people.get(advisor,{}),advisor,'Advisor'))
 result={key:club.get(key,'') for key in ('id','name','category','bio','logo')};result['hierarchy']=members
 if detail:
  people=identities(app);result['hierarchy_history']=[dict(year=h['year'],effective_at=h.get('effective_at'),hierarchy=[safe_person(dict(people.get(m.get('email'),{}),name=m.get('name') or people.get(m.get('email'),{}).get('name')),m.get('email',''),m.get('position','Committee')) for m in h.get('committee',[])],incoming_hierarchy=[safe_person(dict(people.get(m.get('email'),{}),name=m.get('name') or people.get(m.get('email'),{}).get('name')),m.get('email',''),m.get('position','Committee')) for m in h.get('incoming',[])]) for h in sorted(app.all('club_hierarchy'),key=lambda h:h.get('year',0),reverse=True) if h.get('club_id')==club['id']]
  history=[];now=datetime.fromisoformat(auth.now());proposals={r['id']:r for r in app.all('proposal')}
  complete={r.get('proposal_id') for r in app.all('event_completion') if r.get('status')=='approved'}|{r.get('proposal_id') for r in app.all('finance_report') if r.get('status')=='approved'}
  for event in app.all('calendar_event'):
   if event.get('club_id')!=club['id'] or proposals.get(event.get('proposal_id'),{}).get('status')!='approved':continue
   try:end=datetime.fromisoformat(event.get('end_at',''));start=datetime.fromisoformat(event.get('start_at',''))
   except (TypeError,ValueError):continue
   if not end.tzinfo or not start.tzinfo or end>now:continue
   history.append(dict(id=event['id'],title=event.get('title',''),date=start.astimezone(MYT).date().isoformat(),year=start.astimezone(MYT).year,venue=event.get('venue',''),kind='event',occurrence='completed' if event.get('proposal_id') in complete else 'past_scheduled'))
  for report in app.all('club_report'):
   if report.get('club_id')!=club['id'] or report.get('status')!='approved':continue
   try:day=date.fromisoformat(report.get('date',''))
   except (TypeError,ValueError):continue
   history.append(dict(id=report['id'],title=report.get('title',''),date=day.isoformat(),year=day.year,venue=report.get('venue',''),kind=report.get('type','weekly'),occurrence='completed'))
  result['activity_history']=sorted(history,key=lambda row:(row['date'],row['id']),reverse=True)
  result['upcoming_weekly_activities']=upcoming_weekly(app,club['id'])
  result['upcoming_events']=[event for event in performance.public_events(app)['events'] if event['club_id']==club['id']]
  result['weekly_summaries']=[{key:r.get(key,'') for key in ('id','title','date','summary','activity_kind')} for r in app.all('club_report') if r.get('club_id')==club['id'] and r.get('type')=='weekly' and r.get('status')=='approved']
 return result

def associations(app,email):
 clubs=[dict(id=c['id'],name=c['name'],positions=[m.get('position','Committee') for m in c.get('committee',[]) if m.get('email')==email]+(['Advisor'] if c.get('advisor_email')==email else [])) for c in app.all('club') if c.get('status')=='approved' and (c.get('advisor_email')==email or any(m.get('email')==email for m in c.get('committee',[])))]
 proposals={p['id']:p for p in app.all('proposal')}
 events=[]
 for event in performance.public_events(app)['events']:
  roles=[m.get('role','Committee') for m in proposals.get(event['id'],{}).get('committee',[]) if m.get('email')==email]
  if roles:events.append(dict(event,roles=roles))
 return clubs,events

def handle_get(app,user,path,query):
 if path=='/api/profile':
  # Current login is authoritative, including freshly captured Google photo.
  profile=dict(user);profile['profile_id']=profile_id(user['email']);profile['clubs'],profile['events']=associations(app,user['email'])
  return dict(profile=profile)
 if path=='/api/public-clubs':
  q=query.get('q',[''])[0].casefold()[:200]
  return dict(clubs=[public_club(app,c) for c in app.all('club') if c.get('status')=='approved' and q in (c.get('name','')+' '+c.get('category','')).casefold()])
 match=re.fullmatch(r'/api/public-clubs/([A-Za-z0-9_-]+)',path)
 if match:
  club=app.get('club',match[1])
  if club.get('status')!='approved':
   from server import APIError
   raise APIError('Published club not found.',404)
  return dict(club=public_club(app,club,True))
 match=re.fullmatch(r'/api/public-students/([a-f0-9]{32})',path)
 if match:
  for email,person in identities(app).items():
   if profile_id(email)==match[1]:
    clubs,events=associations(app,email)
    # A public identity must participate in an approved club or published event.
    if not clubs and not events and email!=user['email']:break
    profile=safe_person(person,email);profile.update(id=profile['profile_id'],programme=person.get('programme',''),clubs=clubs,events=events)
    return dict(profile=profile)
  from server import APIError
  raise APIError('Published profile not found.',404)
 return None
