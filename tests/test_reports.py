"""Real HTTP four-stage reports, identity/version guards and explicit AGM handover."""
import copy,hashlib,json,pathlib,sys,tempfile,threading,uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
import auth,server,club_reports,exports
from test_registration import Client
from proposal_fixture import drawn_signature


def fixture_club(cid='club',category='Cultural'):
 people=[auth.preview_user(p) for p in ('student','vice','secretary','treasurer')]
 return dict(id=cid,name='Report Society '+cid,owner_email=people[0]['email'],advisor_email='demo.advisor@qiu.edu.my',committee=[dict(position=position,email=person['email'],name=person['name'],university_id=person['university_id']) for position,person in zip(club_reports.POSITIONS,people)],category=category,semester='October 2026',bio='Report test club',logo='',status='approved',revision=1,history=[],created_at=auth.now(),updated_at=auth.now())


def report_fields(**changes):
 return dict(dict(type='weekly',club_id='club',title='Weekly committee meeting',semester='October 2026',date='2026-10-08',start_time='10:00',end_time='11:00',venue='QIU Hall',activity_kind='meeting',summary='Review student activities',objectives=['Coordinate student activities'],minutes='Discussed club activities and assigned tasks.',attendance=[dict(email='demo.student@qiu.edu.my',status='present'),dict(email='demo.vice@qiu.edu.my',status='absent')],decisions=[],next_meeting={}),**changes)


def run():
 with tempfile.TemporaryDirectory() as td,patch.object(auth,'now',return_value='2026-10-09T04:00:00+00:00') as clock:
  srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);base='http://127.0.0.1:'+str(srv.server_port);srv.app=server.App(pathlib.Path(td)/'reports.sqlite3',True,base)
  club=fixture_club();srv.app.put('club',club);srv.app.put('club',dict(fixture_club('foreign'),owner_email='foreign@qiu.edu.my',advisor_email='foreign.advisor@qiu.edu.my',committee=[]))
  threading.Thread(target=srv.serve_forever,daemon=True).start()
  try:
   president,vice,secretary,treasurer,advisor,sld=[Client(base,p) for p in ('student','vice','secretary','treasurer','advisor','sld')];second_secretary=Client(base,'secretary');sig=drawn_signature()
   def save(fields,client=secretary,status=200):return client.call('/api/club-reports',dict(report=fields),status)
   def submit(r,client=president,status=200,**extra):
    import evidence,base64,io
    from PIL import Image
    minimum=1 if r['type']=='agm' else 2
    while evidence.photo_count(srv.app,'club_report',r['id'])<minimum and r['status'] in ('draft','returned'):
     n=evidence.photo_count(srv.app,'club_report',r['id']);buffer=io.BytesIO();Image.new('RGB',(24,24),('navy','red')[n]).save(buffer,format='PNG')
     photo=secretary.call('/api/photos',dict(target_type='club_report',target_id=r['id'],target_revision=r['revision'],name='Activity'+str(n),data_url='data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode()))
     current=secretary.call('/api/club-reports/'+r['id'])['report'];r.clear();r.update(current)
    return client.call('/api/club-reports/'+r['id']+'/submit',dict(revision=r['revision'],signature=sig,**extra),status)
   def review(r,client,action='approve',status=200,**extra):return client.call('/api/club-reports/'+r['id']+'/review',dict(revision=r['revision'],action=action,confirm_submission=True,signature=sig,comment='Correct the report' if action=='return' else '',**extra),status)
   advisor.call('/api/club-reports',dict(report=report_fields()),403);sld.call('/api/club-reports',dict(report=report_fields()),403)
   key=str(uuid.uuid4());fields=report_fields(creation_key=key,old_committee=[{'position':'FORGED'}],created_at='2000-01-01',signatures={'sld':{}})
   r=save(fields)['report'];assert r['old_committee']==club['committee'] and r['created_at']==auth.now() and r['signatures']=={}
   assert save(fields)['creation_replayed'] and len(srv.app.all('club_report'))==1
   r=save(dict(r,minutes='Corrected discussion'))['report'];save(fields,status=409);save(dict(r,revision=1),status=409)
   future=save(report_fields(date='2026-10-10'))['report'];assert future['progress']['percent']<100;submit(future,status=400)
   later=save(report_fields(date='2026-10-09',start_time='11:30',end_time='12:30'))['report'];submit(later,status=400)
   bad_next=save(report_fields(next_meeting=dict(date='2026-10-08',time='10:30',venue='Hall')))['report'];assert 'next_meeting' in submit(bad_next,status=400)['fields']
   bad_decision=save(report_fields(decisions=[dict(task='Poster',person='Secretary',deadline='2026-10-07')]))['report'];assert 'decisions' in submit(bad_decision,status=400)['fields']
   for client in (vice,secretary,treasurer,sld):submit(r,client,403)
   president.call('/api/club-reports/'+r['id']+'/submit',dict(revision=r['revision']),400)
   r=submit(r,name='Forged President',signed_at='2000-01-01')['report'];assert r['status']=='pending_secretary' and r['signatures']['president']['name']=='Demo Student'
   first=srv.app.get('club_report_version',r['id']+'-r'+str(r['submitted_revision']));old_revision=r['submitted_revision']
   assert hashlib.sha256(json.dumps(first['snapshot'],sort_keys=True).encode()).hexdigest()==first['digest'] and 'digest' not in first['snapshot']['signatures']['president']
   save(dict(r,summary='Locked'),status=409);review(r,advisor,status=403);review(r,sld,status=403)
   with ThreadPoolExecutor(2) as pool:results=list(pool.map(lambda c:review(r,c,status=(200,409),name='Forged'),(secretary,second_secretary)))
   assert sum('report' in result for result in results)==1;r=next(result['report'] for result in results if 'report' in result)
   assert r['signatures']['secretary']['name']=='Demo Secretary' and r['status']=='pending_advisor'
   r=review(r,advisor,'return')['report'];assert r['status']=='returned' and r['signatures']=={} and r['return_context']['stage']=='advisor'
   r=save(dict(r,summary='Corrected purpose'))['report'];assert r['return_context'] and r['signatures']=={}
   r=submit(r)['report'];assert r['submitted_revision']!=old_revision and set(r['signatures'])=={'president'}
   assert srv.app.get('club_report_version',r['id']+'-r'+str(old_revision))==first
   for reviewer in (secretary,advisor,sld):r=review(r,reviewer)['report']
   assert r['status']=='approved' and set(r['signatures'])=={'president','secretary','advisor','sld'} and len(srv.app.all('club_report_signature'))==6
   review(r,sld,status=409);assert r['approved_at']==auth.now()
   boot=secretary.call('/api/bootstrap');assert any(x['id']==r['id'] for x in boot['club_reports'])
   assert secretary.call('/api/notifications')['unread_count']>0
   groups=sld.call('/api/activity?grouped=1')['groups'];assert any(g['record_type']=='club_report' and g['record_id']==r['id'] for g in groups)
   # Sports need attendance, whereas non-sports need minutes.
   srv.app.put('club',fixture_club('sport','Sports'));sport=save(report_fields(club_id='sport',attendance=[],minutes=''))['report'];submit(sport,status=400)
   # AGM new identities are canonical, mandatory officers distinct, and handover is explicitly SLD-controlled.
   srv.app.put('directory_identity',dict(id='new@qiu.edu.my',email='new@qiu.edu.my',name='New Treasurer',university_id='QIU-202609-123456'))
   new=[dict(position=p,email=e,name='FORGED') for p,e in zip(club_reports.POSITIONS,('demo.vice@qiu.edu.my','demo.secretary@qiu.edu.my','demo.treasurer@qiu.edu.my','new@qiu.edu.my'))]
   agm_fields=report_fields(type='agm',title='Annual General Meeting',election_summary='Elected new officers.',outgoing_activities='Organised three student activities.',new_committee=new,opening_speech='Welcome',agenda=[dict(start='10:00',end='11:00',agenda='Elections')],adjournment='Meeting closed.')
   bad_agenda=save(dict(agm_fields,report_year=2024,agenda=[dict(start='10:30',end='11:30',agenda='Outside meeting times')]))['report'];assert 'agenda' in submit(bad_agenda,status=400)['fields']
   agm=save(agm_fields)['report']
   assert agm['new_committee'][0]['name']=='Demo Vice President' and agm['old_committee']==club['committee']
   agm=submit(agm)['report']
   for reviewer in (secretary,advisor,sld):agm=review(agm,reviewer)['report']
   assert srv.app.get('club','club')['committee']==club['committee'],'Approval must not apply the handover implicitly'
   url='/api/club-reports/'+agm['id']+'/apply-handover';president.call(url,dict(revision=agm['revision'],club_revision=1),403);sld.call(url,dict(revision=agm['revision'],club_revision=0),409)
   rival=save(dict(agm_fields,report_year=2025))['report'];rival=submit(rival)['report']
   for reviewer in (secretary,advisor,sld):rival=review(rival,reviewer)['report']
   waiting=submit(save(report_fields(title='Awaiting Secretary'))['report'])['report']
   blocked=sld.call(url,dict(revision=agm['revision'],club_revision=1),409);assert 'Secretary' in blocked['error']
   review(waiting,secretary,'return')
   second_sld=Client(base,'sld')
   with ThreadPoolExecutor(2) as pool:
    outcomes=list(pool.map(lambda pair:pair[0].call('/api/club-reports/'+pair[1]['id']+'/apply-handover',dict(revision=pair[1]['revision'],club_revision=1),(200,409)),((sld,agm),(second_sld,rival))))
   assert sum('report' in outcome for outcome in outcomes)==1
   result=next(outcome for outcome in outcomes if 'report' in outcome);agm=result['report']
   assert result['club']['handover_status']=='overlap' and agm['handover_applied_at']==auth.now()
   clock.return_value='2026-10-17T04:00:00+00:00'
   assert srv.app.get('club','club')['committee']==agm['new_committee']
   sld.call('/api/club-reports/'+agm['id']+'/apply-handover',dict(revision=agm['revision'],club_revision=result['club']['revision']),409)
   loser=next(record for record in (rival,srv.app.get('club_report',url.split('/')[3])) if record['id']!=agm['id'])
   stale=sld.call('/api/club-reports/'+loser['id']+'/apply-handover',dict(revision=loser['revision'],club_revision=result['club']['revision']),409);assert 'current committee' in stale['error'].lower()

   submit(bad_agenda,vice,status=409)
   assert not vice.call('/api/club-reports/'+bad_agenda['id'])['report']['can_sign']
   president.call('/api/club-reports/'+agm['id'],status=403);assert all(r['club_id']!='club' for r in president.call('/api/bootstrap')['club_reports'])
   assert vice.call('/api/club-reports/'+agm['id'])['report']['signatures']==agm['signatures'],'Historical old-role signatures remain unchanged'
   if hasattr(exports,'club_report_pdf'):
    assert sld.opener.open(base+'/api/club-reports/'+agm['id']+'/export?format=pdf').read().startswith(b'%PDF')
   print('PASS: report autosave/idempotency, current roles, actual-date validation, President/Secretary/advisor/SLD chain, signature race, correction/history/digest, scoped notifications, sports fields, AGM canonical officers and explicit once-only handover.')
  finally:srv.shutdown();srv.server_close();srv.app.db.close()

if __name__=='__main__':run()
