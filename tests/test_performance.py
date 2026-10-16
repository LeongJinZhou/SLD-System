"""Operational calendar occurrence truth, permission boundaries and public events."""
import copy,pathlib,sys,tempfile,threading
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
import auth,server
from test_registration import Client
from test_reports import fixture_club,report_fields


def run():
 with tempfile.TemporaryDirectory() as td,patch.object(auth,'now',return_value='2026-10-09T04:00:00+00:00'):
  srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);base='http://127.0.0.1:'+str(srv.server_port);srv.app=server.App(pathlib.Path(td)/'calendar.sqlite3',True,base)
  club=fixture_club();club['committee']=[m for m in club['committee'] if m['position'] in ('President','Secretary')];srv.app.put('club',club)
  foreign=dict(fixture_club('foreign'),owner_email='foreign@qiu.edu.my',advisor_email='foreign.advisor@qiu.edu.my',committee=[]);srv.app.put('club',foreign)
  for rid,kind,status,day,cid in (('weekly','weekly','approved','2026-10-08','club'),('agm','agm','approved','2026-09-10','club'),('draft','weekly','draft','2026-10-08','club'),('pending','agm','pending_sld','2026-10-08','club'),('foreign-report','weekly','approved','2026-10-08','foreign')):
   srv.app.put('club_report',dict(report_fields(),id=rid,type=kind,status=status,date=day,club_id=cid))
  def event(eid,start,end,cid='club',status='approved',participant=False):
   srv.app.put('proposal',dict(id=eid,club_id=cid,title='Event '+eid,status=status,revision=1,created_at=auth.now(),updated_at=auth.now(),committee=[dict(email='demo.treasurer@qiu.edu.my',role='Organiser')] if participant else [],history=[{'signature':'PRIVATE-SIGNATURE'}]))
   srv.app.put('calendar_event',dict(id=eid,proposal_id=eid,club_id=cid,club_name='Report Society '+cid,title='Event '+eid,start_at=start,end_at=end,venue='QIU Hall',description='Approved event description',approved_at=auth.now()))
  event('past','2026-10-01T10:00:00+08:00','2026-10-01T12:00:00+08:00')
  event('attested','2026-10-02T10:00:00+08:00','2026-10-02T12:00:00+08:00');srv.app.put('finance_report',dict(id='actual-finance',proposal_id='attested',status='approved',receipts=['PRIVATE-RECEIPT'],amount=999))
  event('future','2026-12-31T22:00:00+08:00','2027-01-02T02:00:00+08:00',participant=True)
  event('ongoing','2026-10-09T11:00:00+08:00','2026-10-09T13:00:00+08:00')
  event('unapproved','2026-12-01T10:00:00+08:00','2026-12-01T12:00:00+08:00',status='pending_sld')
  event('foreign-event','2026-12-15T10:00:00+08:00','2026-12-15T12:00:00+08:00','foreign')
  threading.Thread(target=srv.serve_forever,daemon=True).start()
  try:
   president,advisor,sld,event_member,ordinary=[Client(base,p) for p in ('student','advisor','sld','treasurer','visitor')]
   endpoint='/api/performance?year=2026'
   result=president.call(endpoint);assert result['summary']==dict(total=6,completed=3,scheduled=1,ongoing=1,past_scheduled=1,weekly=1,agm=1,events=4,active_days=6),result['summary']
   assert {a['record_id'] for a in result['activities']}=={'weekly','agm','past','attested','future','ongoing'}
   assert next(a for a in result['activities'] if a['record_id']=='past')['occurrence']=='past_scheduled'
   assert next(a for a in result['activities'] if a['record_id']=='attested')['completion_basis']=='approved_financial_report'
   assert all(a['href'].startswith('/?task=') and 'PRIVATE' not in str(a) for a in result['activities'])
   # Administrative saves do not create calendar occurrence cells or alter counts.
   for i in range(20):srv.app.log(auth.preview_user('student'),'proposal_draft_saved','unknown','club')
   assert president.call(endpoint)['summary']==result['summary']
   assert advisor.call(endpoint)['summary']==result['summary']
   staff=sld.call(endpoint);assert staff['summary']['total']==8 and {c['id'] for c in staff['clubs']}=={'club','foreign'}
   own=event_member.call(endpoint);assert own['summary']['total']==1 and own['activities'][0]['record_id']=='future' and own['summary']['weekly']==0
   event_member.call(endpoint+'&club_id=foreign',status=403);ordinary.call(endpoint+'&club_id=club',status=403)
   assert ordinary.call(endpoint)['activities']==[]
   january=event_member.call('/api/performance?year=2027&month=1');assert [d['date'] for d in january['days']]==['2027-01-01','2027-01-02'] and january['summary']['total']==1
   month=president.call(endpoint+'&month=10');assert len(month['activities'])==4 and month['summary']['agm']==0 and month['summary']['scheduled']==0
   for suffix in ('year=oops','year=3000','year=2026&month=13'):ordinary.call('/api/performance?'+suffix,status=400)
   public=ordinary.call('/api/public-events');assert {e['id'] for e in public['events']}=={'future','ongoing','foreign-event'}
   assert all(set(e)=={'id','club_id','club_name','title','start_at','end_at','venue','description'} for e in public['events'])
   assert ordinary.call('/api/public-events/foreign-event')['event']['id']=='foreign-event'
   ordinary.call('/api/public-events/past',status=404);ordinary.call('/api/public-events/unapproved',status=404)
   ordinary.call('/api/proposals/future/export?format=docx',status=403)
   # Current event assignments are rechecked before filtering/counting private occurrence records.
   p=srv.app.get('proposal','future');p['committee']=[];srv.app.put('proposal',p);assert event_member.call(endpoint)['activities']==[]
   print('PASS: approved actual report dates, evidenced completion versus elapsed plans, sparse day/month/year counts, multiday boundary, no autosave/finance noise, SLD/club/event/ordinary scope and safe public approved events.')
  finally:srv.shutdown();srv.server_close();srv.app.db.close()

if __name__=='__main__':run()
