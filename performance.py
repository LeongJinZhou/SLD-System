"""Operational activity calendar; draft saves and finance do not count as occurrences."""
import calendar
from datetime import datetime,date,timedelta
import auth
import club_reports


def public_events(app,event_id=None):
 now=datetime.fromisoformat(auth.now())
 result=[]
 proposals={p['id']:p for p in app.all('proposal')}
 clubs={c['id']:c for c in app.all('club')}
 for event in app.all('calendar_event'):
  proposal=proposals.get(event.get('proposal_id'))
  if not proposal or proposal.get('status')!='approved' or event.get('club_id') not in clubs:continue
  try:
   begin=datetime.fromisoformat(event['start_at']);end=datetime.fromisoformat(event['end_at'])
   if begin.tzinfo is None or end.tzinfo is None or end<=begin:continue
  except (ValueError,KeyError,TypeError):continue
  if end.tzinfo is None or end<=now:continue
  result.append({k:event.get(k,'') for k in ('id','club_id','club_name','title','start_at','end_at','venue','description')})
 result.sort(key=lambda e:(e['start_at'],e['id']))
 if event_id is not None:
  found=next((e for e in result if e['id']==event_id),None)
  if not found:club_reports.error('Upcoming approved event not found.',404)
  return dict(event=found)
 return dict(events=result)


def year_calendar(app,user,year,club_id='',month=None):
 if not 1900<=year<=2200:club_reports.error('Choose a valid calendar year.')
 if month is not None and not 1<=month<=12:club_reports.error('Choose a month from 1 to 12.')
 now=datetime.fromisoformat(auth.now());clubs={c['id']:c for c in app.all('club')}
 assigned={cid for cid,c in clubs.items() if club_reports.visible(app,user,c)}
 proposals={p['id']:p for p in app.all('proposal')}
 completed_events={r['proposal_id']:r['id'] for r in app.all('finance_report') if r.get('status')=='approved'}
 completed_post_events={r['proposal_id']:r['id'] for r in app.all('event_completion') if r.get('status')=='approved'}
 completed_events.update(completed_post_events)
 event_only={p['club_id'] for p in proposals.values() if p.get('club_id') in clubs and app.event_roles(p,user)}
 allowed=assigned|event_only
 if club_id and club_id not in allowed:club_reports.error('You cannot view this club activity calendar.',403)
 selected={club_id} if club_id else allowed
 start=date(year,month or 1,1);end=date(year,month,calendar.monthrange(year,month)[1]) if month else date(year,12,31)
 activities=[]
 for report in app.all('club_report'):
  if report.get('club_id') not in selected or report['club_id'] not in assigned or report.get('status')!='approved':continue
  times=club_reports.schedule(report)
  if not times or not start<=times[0].date()<=end:continue
  if times[1]>now:continue
  activities.append(dict(id='report-'+report['id'],kind=report['type'],club_id=report['club_id'],club_name=clubs[report['club_id']]['name'],title=report['title'],date=times[0].date().isoformat(),start_at=times[0].isoformat(),end_at=times[1].isoformat(),status='approved',occurrence='completed',record_type='club_report',record_id=report['id'],href='/?task=report&id='+report['id']))
 for event in app.all('calendar_event'):
  proposal=proposals.get(event.get('proposal_id'));cid=event.get('club_id')
  if cid not in selected or not proposal or proposal.get('status')!='approved':continue
  if cid not in assigned and not app.event_roles(proposal,user):continue
  try:
   planned_start=datetime.fromisoformat(event['start_at']);planned_end=datetime.fromisoformat(event['end_at'])
   if planned_start.tzinfo is None or planned_end.tzinfo is None:continue
   planned_start=planned_start.astimezone(club_reports.MYT);planned_end=planned_end.astimezone(club_reports.MYT)
   if planned_end<=planned_start or planned_end.date()<start or planned_start.date()>end:continue
  except (ValueError,KeyError,TypeError):continue
  occurrence=('completed' if proposal['id'] in completed_events else 'past_scheduled') if planned_end<=now else 'scheduled' if planned_start>now else 'ongoing'
  activities.append(dict(id='event-'+event['id'],kind='event',club_id=cid,club_name=clubs[cid]['name'],title=event['title'],date=planned_start.date().isoformat(),start_at=planned_start.isoformat(),end_at=planned_end.isoformat(),status='approved',occurrence=occurrence,completion_basis=('approved_post_event_report' if proposal['id'] in completed_post_events else 'approved_financial_report') if occurrence=='completed' else 'planned_schedule',record_type='proposal',record_id=proposal['id'],href='/?task=proposal&id='+proposal['id']))
 activities.sort(key=lambda a:(a['start_at'],a['id']))
 days={};months={m:dict(month=m,count=0,completed=0,scheduled=0,ongoing=0,past_scheduled=0) for m in range(1,13)}
 for activity in activities:
  first=max(start,date.fromisoformat(activity['date']));last=min(end,datetime.fromisoformat(activity['end_at']).date())
  # Midnight is the end boundary, not an additional day of activity.
  finish=datetime.fromisoformat(activity['end_at'])
  if finish.time()==datetime.min.time():last=min(last,finish.date()-timedelta(days=1))
  day=first;seen_months=set()
  while day<=last:
   key=day.isoformat();bucket=days.setdefault(key,dict(date=key,count=0,completed=0,scheduled=0,ongoing=0,past_scheduled=0,activities=[]))
   bucket['count']+=1;bucket[activity['occurrence']]+=1;bucket['activities'].append(activity)
   seen_months.add(day.month);day+=timedelta(days=1)
  for m in seen_months:months[m]['count']+=1;months[m][activity['occurrence']]+=1
 summary=dict(total=len(activities),completed=sum(a['occurrence']=='completed' for a in activities),scheduled=sum(a['occurrence']=='scheduled' for a in activities),ongoing=sum(a['occurrence']=='ongoing' for a in activities),past_scheduled=sum(a['occurrence']=='past_scheduled' for a in activities),weekly=sum(a['kind']=='weekly' for a in activities),agm=sum(a['kind']=='agm' for a in activities),events=sum(a['kind']=='event' for a in activities),active_days=len(days))
 return dict(year=year,month=month,clubs=[dict(id=cid,name=clubs[cid]['name']) for cid in sorted(allowed)],activities=activities,summary=summary,months=list(months.values()),days=[days[key] for key in sorted(days)])


def handle_get(app,user,path,query):
 if path=='/api/public-events':return public_events(app)
 if path.startswith('/api/public-events/'):
  import re
  found=re.fullmatch(r'/api/public-events/([A-Za-z0-9_-]+)',path)
  if found:return public_events(app,found[1])
 if path!='/api/performance':return None
 try:
  year=int(query.get('year',[str(datetime.fromisoformat(auth.now()).astimezone(club_reports.MYT).year)])[0]);month=int(query['month'][0]) if query.get('month') else None
 except ValueError:club_reports.error('Year and month must be whole numbers.')
 return year_calendar(app,user,year,query.get('club_id',[''])[0],month)
