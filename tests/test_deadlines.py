"""Fixed-server-clock checks of policy access, deadline boundaries and metadata ownership."""
import pathlib,sys,tempfile,threading
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
import server,auth
from test_registration import Client
from proposal_fixture import complete_proposal,drawn_signature

def run():
 with tempfile.TemporaryDirectory() as td,patch.object(auth,'now',return_value='2026-10-08T02:00:00+00:00'):
  srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);base='http://127.0.0.1:'+str(srv.server_port)
  srv.app=server.App(pathlib.Path(td)/'test.sqlite3',True,base)
  srv.app.put('club',{'id':'club','name':'Test Society','owner_email':'demo.student@qiu.edu.my','advisor_email':'demo.advisor@qiu.edu.my',
    'committee':[dict(position='President',email='demo.student@qiu.edu.my',name='Demo Student')],'category':'Cultural','semester':'October 2026','bio':'Fixture','logo':'','status':'approved','revision':1,'history':[],
    'created_at':auth.now(),'updated_at':auth.now()})
  threading.Thread(target=srv.serve_forever,daemon=True).start()
  try:
   student=Client(base,'student');advisor=Client(base,'advisor');sld=Client(base,'sld')
   settings=student.call('/api/bootstrap')['settings'];assert settings['event_proposal_lead_days']==14
   for actor in (student,advisor):actor.call('/api/settings',{'event_proposal_lead_days':1,'revision':settings['revision']},403)
   for invalid in (0,366,True,'2',1.5):sld.call('/api/settings',{'event_proposal_lead_days':invalid,'revision':settings['revision']},400)
   fields=complete_proposal()
   def save(**changes):return student.call('/api/proposals',{'proposal':dict(fields,**changes)})['proposal']
   spoof={'created_at':'2000-01-01','updated_at':'2000-01-01','submitted_at':'2000-01-01','deadline_at':'2099-01-01',
      'event_starts_at':'2099-01-01','policy_weeks_at_submission':0,'status':'approved','history':[{'timestamp':'fake'}],
      'owner_email':'demo.sld@qiu.edu.my','prepared_by_name':'Forged signer'}
   p=save(environment='Outdoor',**spoof);assert p['environment']=='Outdoor';assert p['status']=='draft' and p['created_at']==auth.now() and p['updated_at']==auth.now()
   assert not p.get('submitted_at') and not p.get('deadline_at') and p.get('history',[])!=spoof['history']
   assert p['owner_email']=='demo.student@qiu.edu.my' and p['prepared_by_name']=='Demo Student'
   def submit(p,status=200):return student.call('/api/proposals/'+p['id']+'/submit',{'revision':p['revision'],'signature':drawn_signature()},status)
   late=save(start_time='09:59');submit(late,400)
   boundary=submit(p)['proposal'];assert boundary['status']=='pending_advisor' and boundary['submitted_at']==auth.now()
   assert boundary['policy_days_at_submission']==14
   student.call('/api/proposals',{'proposal':dict(boundary,date='2026-10-23',submitted_at='fake')},409)
   submit(boundary,409)
   incomplete=save(start_time='');submit(incomplete,400)
   invalid=save(date='2026-02-30');submit(invalid,400)
   backward=save(end_time='09:00');submit(backward,400)
   one_week=save(date='2026-10-15',end_date='2026-10-15');submit(one_week,400)
   updated=sld.call('/api/settings',{'event_proposal_lead_days':7,'revision':settings['revision'],'updated_at':'fake'})['settings']
   assert updated['updated_at']==auth.now() and updated['updated_by']=='demo.sld@qiu.edu.my'
   sld.call('/api/settings',{'event_proposal_lead_days':21,'revision':settings['revision']},409)
   student.call('/api/proposals/'+one_week['id']+'/submit',{'revision':one_week['revision'],'settings_revision':settings['revision'],'signature':drawn_signature()},409)
   admitted=submit(one_week)['proposal'];assert admitted['policy_days_at_submission']==7
   assert srv.app.get('proposal',boundary['id'])['policy_days_at_submission']==14
   past=save(date='2026-10-07',end_date='2026-10-07');submit(past,400)
   persisted=server.App(pathlib.Path(td)/'test.sqlite3',True,base)
   assert persisted.bootstrap({'csrf':'test','user':auth.preview_user('sld')})['settings']['event_proposal_lead_days']==7
   persisted.db.close()
   print('PASS: immutable server timestamps, metadata tampering, planned dates, exact 14-day MYT boundary, late/invalid submission, SLD-only revisioned settings and persisted policy snapshots.')
  finally:srv.shutdown();srv.server_close();srv.app.db.close()

if __name__=='__main__':run()
