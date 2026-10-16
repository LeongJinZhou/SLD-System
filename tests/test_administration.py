"""Scoped admin controls, complete drafts, directory imports and recovery boundaries."""
import io,json,pathlib,sys,tempfile,threading,time,urllib.parse
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
import auth,server
from test_registration import Client
from proposal_fixture import complete_proposal,drawn_signature
from tools.backup import backup,verify_restore

def run():
 with tempfile.TemporaryDirectory() as td,patch.object(auth,'now',return_value='2026-10-08T02:00:00+00:00'):
  srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);base='http://127.0.0.1:'+str(srv.server_port)
  srv.app=server.App(pathlib.Path(td)/'live.sqlite3',True,base)
  def club(cid,owner,advisor):
   members=[dict(position=position,name=person['name'],email=person['email'],university_id=person['university_id']) for position,person in zip(('President','Vice President','Secretary','Treasurer'),[auth.PREVIEW_PEOPLE[i] for i in (0,3,4,5)])]
   if cid!='club':members=[dict(position='President',name='Other',email=owner)]
   return dict(id=cid,name='Society '+cid,owner_email=owner,advisor_email=advisor,committee=members,category='Cultural',semester='October 2026',bio='Fixture',logo='',status='approved',revision=1,history=[],created_at=auth.now(),updated_at=auth.now())
  for item in [club('club','demo.student@qiu.edu.my','demo.advisor@qiu.edu.my'),club('foreign','foreign@qiu.edu.my','foreign.advisor@qiu.edu.my')]:srv.app.put('club',item)
  threading.Thread(target=srv.serve_forever,daemon=True).start()
  try:
   student,advisor,sld=[Client(base,p) for p in ('student','advisor','sld')]
   clients=[Client(base,p) for p in ('vice','secretary','treasurer')]
   for client in clients:
    b=client.call('/api/bootstrap');assert b['user']['role']=='student' and b['user']['photo'].startswith('/web/avatars/')
    assert b['clubs'][0]['can_edit_proposals']
   settings=sld.call('/api/bootstrap')['settings']
   assert settings['event_proposal_lead_days']==14
   # Partial entries autosave without a title; progress measures actual requirements.
   draft=student.call('/api/proposals',{'proposal':{'club_id':'club','summary':'Started writing'}})['proposal']
   assert 0<draft['progress']['percent']<100 and draft['progress']['total']==len([entry for entry in draft['progress']['checklist'] if entry.get('required',True)])
   incomplete=student.call('/api/proposals/'+draft['id']+'/submit',{'revision':draft['revision'],'signature':drawn_signature()},400)
   assert incomplete['fields'] and incomplete['code']=='VALIDATION_ERROR'
   for value in ('4',[4],['18'],['4','4'],['custom']):
    rejected=student.call('/api/proposals',{'proposal':dict(complete_proposal(),sdgs=value)},400);assert 'sdgs' in rejected['fields']
   p=student.call('/api/proposals',{'proposal':complete_proposal(date='2026-10-10',end_date='2026-10-10')})['proposal'];path='/api/proposals/'+p['id']
   assert p['progress']['percent']==100
   malformed=student.call('/api/proposals',{'proposal':complete_proposal(activities=[{'name':None,'description':'Text'}])})['proposal']
   assert malformed['progress']['percent']<100
   student.call('/api/proposals/'+malformed['id']+'/submit',{'revision':malformed['revision'],'signature':drawn_signature()},400)
   error=student.call(path+'/submit',{'revision':p['revision'],'signature':drawn_signature()},400);assert error['code']=='DEADLINE_PASSED'
   grant=dict(revision=0,enabled=True,reason='Approved urgent university activity',expires_at='2026-10-09T10:00:00+08:00',updated_at='fake',updated_by='fake')
   for actor in (student,advisor,*clients):actor.call('/api/clubs/club/deadline-exception',grant,403)
   sld.call('/api/clubs/club/deadline-exception',dict(grant,expires_at='2026-10-08T01:59:00+00:00'),400)
   sld.call('/api/clubs/club/deadline-exception',dict(grant,expires_at='2026-10-09T10:00:00'),400)
   exception=sld.call('/api/clubs/club/deadline-exception',grant)['deadline_exception']
   assert exception['updated_at']==auth.now() and exception['updated_by']=='demo.sld@qiu.edu.my'
   sld.call('/api/clubs/club/deadline-exception',grant,409)
   submitted=student.call(path+'/submit',{'revision':p['revision'],'signature':drawn_signature()})['proposal'];assert submitted['deadline_exception_used']['revision']==exception['revision']
   assert submitted['deadline_exception_used']['reason']==grant['reason'] and submitted['policy_days_at_submission']==14
   p2=clients[0].call('/api/proposals',{'proposal':complete_proposal(title='Another event',date='2026-10-10',end_date='2026-10-10')})['proposal']
   sld.call('/api/clubs/club/deadline-exception',dict(enabled=False,reason='Urgent window closed',revision=exception['revision']))
   versions=srv.app.all('deadline_exception_version');assert any(v['snapshot']['reason']==grant['reason'] and v['snapshot']['enabled'] for v in versions)
   assert any(v['snapshot']['reason']=='Urgent window closed' and not v['snapshot']['enabled'] for v in versions)
   clients[0].call('/api/proposals/'+p2['id']+'/submit',{'revision':p2['revision'],'signature':drawn_signature()},400)
   # Expired grants and a grant to another club cannot bypass current policy.
   sld.call('/api/clubs/foreign/deadline-exception',dict(grant,revision=0))
   clients[0].call('/api/proposals/'+p2['id']+'/submit',{'revision':p2['revision'],'signature':drawn_signature()},400)
   current=sld.call('/api/bootstrap')['deadline_exceptions'];rev=next(g['revision'] for g in current if g['id']=='club')
   sld.call('/api/clubs/club/deadline-exception',dict(grant,revision=rev))
   with patch.object(auth,'now',return_value='2026-10-09T03:00:00+00:00'):
    clients[0].call('/api/proposals/'+p2['id']+'/submit',{'revision':p2['revision'],'signature':drawn_signature()},400)
   past=student.call('/api/proposals',{'proposal':complete_proposal(date='2026-10-07',end_date='2026-10-07')})['proposal']
   student.call('/api/proposals/'+past['id']+'/submit',{'revision':past['revision'],'signature':drawn_signature()},400)
   # Grouped audit details only contain that proposal and chosen club.
   for _ in range(3):srv.app.log(auth.preview_user('student'),'proposal_draft_saved',p2['id'],'club')
   groups=student.call('/api/activity?club_id=club&grouped=1')['groups'];assert any(g['record_id']==p['id'] for g in groups)
   detail=student.call('/api/activity?club_id=club&record_id='+p2['id']);assert detail['total']>=4 and all(e['record_id']==p2['id'] for e in detail['entries'])
   assert student.call('/api/activity?club_id=foreign&grouped=1')['total']==0
   for actor in (student,advisor,*clients):
    actor.call('/api/contacts',status=403);actor.call('/api/contacts/import',{},403)
   imported=sld.call('/api/contacts/import',{});assert imported['imported']==len(auth.PREVIEW_PEOPLE)
   detail=sld.call('/api/activity?group_key='+urllib.parse.quote('system:directory_contacts_imported'))
   assert detail['total']==1 and all(e['action']=='directory_contacts_imported' for e in detail['entries'])
   contacts=sld.call('/api/contacts?club_id=club&intake_year=2026&intake_month=10');assert contacts['total']==4
   person=contacts['contacts'][0];result=sld.call('/api/contacts?student_id='+person['student_id']);assert result['total']==1 and result['contacts'][0]['photo_status']=='available'
   assert auth.student_id_fields('QIU-202404-007157')==dict(intake_year=2024,intake_month=4,student_id_last4='7157',student_id_valid=True)
   assert not auth.student_id_fields('QIU-202413-007157')['student_id_valid']
   # Live integration remains unavailable without configuration; records survive failed imports.
   previous=srv.app.all('contact');srv.app.preview=False
   sld.call('/api/contacts/import',{},503);assert srv.app.all('contact')==previous
   for session in srv.app.sessions.values():
    if session.get('user',{}).get('email')=='demo.sld@qiu.edu.my':session['token']='fictional-token'
   with patch.object(auth,'directory_enabled',return_value=True),patch.object(auth,'list_directory',side_effect=ValueError('Second page unavailable')):
    error=sld.call('/api/contacts/import',{},503);assert error['code']=='DIRECTORY_IMPORT_FAILED' and srv.app.all('contact')==previous
   srv.app.preview=True
   # Legacy week settings retain their numerical meaning when read as days.
   srv.app.put('system_settings',dict(id='operational',revision=2,event_proposal_lead_weeks=3))
   assert sld.call('/api/bootstrap')['settings']['event_proposal_lead_days']==21
   no_sdgs=clients[1].call('/api/proposals',{'proposal':complete_proposal(sdgs=[],date='2026-11-20',end_date='2026-11-20')})['proposal'];assert no_sdgs['progress']['percent']==100
   student.call('/api/proposals/'+no_sdgs['id']+'/submit',{'revision':no_sdgs['revision'],'signature':drawn_signature()})
   # Expired POST sessions report authentication recovery before CSRF, not misleading 403.
   for session in srv.app.sessions.values():
    if session.get('user',{}).get('email')=='demo.student@qiu.edu.my':session['expires']=0
   failed=student.call('/api/proposals',{'proposal':dict(p2,summary='Unsaved entry')},401);assert failed['code']=='SESSION_EXPIRED'
   student.call('/api/activity',status=401)
   backup_path=backup(pathlib.Path(td)/'live.sqlite3',pathlib.Path(td)/'backup.sqlite3')
   restored=verify_restore(backup_path);assert restored['records']>0 and restored['logs']>0
   try:backup(pathlib.Path(td)/'live.sqlite3',backup_path);raise AssertionError('Backup overwrote a file')
   except ValueError:pass
   print('PASS: established persona permissions, partial draft progress, controlled SDGs, day policies, scoped/expired/revoked exceptions, grouped activity, contact filters/ID/photo and import failure retention, expired session recovery, SQLite backup/restore.')
  finally:srv.shutdown();srv.server_close();srv.app.db.close()

def directory_checks():
 pages=[{'people':[{'names':[{'displayName':'First'}]}],'nextPageToken':'next'}, {'people':[{'names':[{'displayName':'Second'}]}]}]
 requests=[]
 def response(request,timeout):
  requests.append(request);return io.BytesIO(json.dumps(pages[len(requests)-1]).encode())
 with patch.object(auth.urllib.request,'urlopen',side_effect=response):
  assert len(auth.list_directory('fictional-token'))==2
 assert urllib.parse.parse_qs(urllib.parse.urlsplit(requests[1].full_url).query)['pageToken']==['next']
 assert 'DIRECTORY_SOURCE_TYPE_DOMAIN_CONTACT' in urllib.parse.parse_qs(urllib.parse.urlsplit(requests[0].full_url).query)['sources']
 assert auth.safe_photo('https://lh3.googleusercontent.com/photo') and not auth.safe_photo('http://localhost/private')
 first=server.ExclusiveHTTPServer(('127.0.0.1',0),server.Handler)
 try:
  try:
   duplicate=server.ExclusiveHTTPServer(first.server_address,server.Handler);duplicate.server_close();raise AssertionError('Two servers shared one port')
  except OSError:pass
 finally:first.server_close()
 print('PASS: mocked paginated Google directory contract and photo URL validation; no live Google call claimed.')

if __name__=='__main__':directory_checks();run()
