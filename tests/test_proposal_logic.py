"""HTTP schedule/collaboration/conditional required-section acceptance."""
import io,pathlib,sys,tempfile,threading,zipfile
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
import auth,server,exports
from test_registration import Client
from proposal_fixture import complete_proposal,drawn_signature

def run():
 with tempfile.TemporaryDirectory() as td,patch.object(auth,'now',return_value='2026-10-08T02:00:00+00:00'):
  srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);base='http://127.0.0.1:'+str(srv.server_port);srv.app=server.App(pathlib.Path(td)/'test.sqlite3',True,base)
  club=dict(id='club',name='Host Society',owner_email='demo.student@qiu.edu.my',advisor_email='demo.advisor@qiu.edu.my',committee=[dict(position='President',name='Demo Student',email='demo.student@qiu.edu.my')],status='approved',revision=1,history=[],bio='Club',category='Cultural',semester='2026',logo='',created_at=auth.now(),updated_at=auth.now())
  srv.app.put('club',club);srv.app.put('club',dict(club,id='partner',name='Partner Society',owner_email='private@qiu.edu.my',advisor_email='private.advisor@qiu.edu.my',committee=[]))
  threading.Thread(target=srv.serve_forever,daemon=True).start()
  try:
   user=Client(base,'student');catalog=user.call('/api/bootstrap')['collaboration_clubs'];assert all(set(c)=={'id','name'} for c in catalog)
   def save(**changes):return user.call('/api/proposals',dict(proposal=complete_proposal(**changes)))['proposal']
   p=save(date='2026-11-01',end_date='2026-11-02',start_time='23:00',end_time='01:30',duration='Forged duration',duration_seconds=1,collaboration_club_ids=['partner'],collaboration_other_enabled=True,collaboration_other='External NGO')
   assert p['duration_seconds']==9000 and p['duration']=='2 hours 30 minutes';assert p['collaboration']=='Partner Society; External NGO'
   assert p['progress']['percent']==100
   with zipfile.ZipFile(io.BytesIO(exports.proposal_docx(dict(p,duration='FORGED'),club,auth.preview_user('student')))) as package:
    xml=package.read('word/document.xml').decode();assert '2 hours 30 minutes' in xml and 'FORGED' not in xml and 'Partner Society; External NGO' in xml
   multi=save(date='2026-11-01',end_date='2026-11-03',start_time='08:00',end_time='10:15');assert multi['duration_seconds']==180900 and multi['duration']=='2 days 2 hours 15 minutes'
   bad=save(date='2026-11-01',end_date='2026-11-01',start_time='10:00',end_time='09:00');assert bad['duration']=='' and bad['duration_seconds'] is None and bad['step_errors']['0']
   user.call('/api/proposals/'+bad['id']+'/submit',dict(revision=bad['revision'],signature=drawn_signature()),400)
   user.call('/api/proposals',dict(proposal=complete_proposal(collaboration_club_ids=['missing'])),400)
   user.call('/api/proposals',dict(proposal=complete_proposal(collaboration_club_ids=['partner','partner'])),400)
   other=save(collaboration_other_enabled=True,collaboration_other='');assert 'collaboration_other' in other['step_errors']['0']
   user.call('/api/proposals/'+other['id']+'/submit',dict(revision=other['revision'],signature=drawn_signature()),400)
   clean=save(collaboration_other_enabled=False,collaboration_other='Irrelevant Other');assert clean['collaboration_other']=='' and clean['collaboration']==''
   inactive=save(nature=[],nature_other='Hidden obsolete nature');assert inactive['nature_other']==''
   with zipfile.ZipFile(io.BytesIO(exports.proposal_docx(dict(inactive,nature_other='Hidden obsolete nature'),club,auth.preview_user('student')))) as package:
    assert 'Hidden obsolete nature' not in package.read('word/document.xml').decode()
   ict=save(ict_required=True,ict='');assert 'ict' in ict['step_errors']['1']
   user.call('/api/proposals/'+ict['id']+'/submit',dict(revision=ict['revision'],signature=drawn_signature()),400)
   virtual=save(mode='Virtual',venue='University meeting platform',ict_required=True,ict='Livestream support',logistics_required=True,logistics='Physical chairs',transport='Bus')
   assert virtual['ict_required'] and virtual['ict']=='Livestream support' and not virtual['logistics_required'] and virtual['transport']=='' and virtual['progress']['percent']==100
   budget=save(revenue=[dict(description='',price='10',quantity='')]);assert budget['step_errors']['2']
   user.call('/api/proposals/'+budget['id']+'/submit',dict(revision=budget['revision'],signature=drawn_signature()),400)
   key='12345678-1234-4234-8234-123456789012';payload=dict(proposal=dict(complete_proposal(),creation_key=key))
   first=user.call('/api/proposals',payload)['proposal'];retry=user.call('/api/proposals',payload);assert retry['proposal']['id']==first['id'] and retry['creation_replayed']
   assert sum(record['id']==first['id'] for record in srv.app.all('proposal'))==1
   changed=user.call('/api/proposals',dict(proposal=dict(first,summary='Saved update')))['proposal'];assert changed['revision']>first['revision']
   user.call('/api/proposals',payload,409)
   user.call('/api/proposals',dict(proposal=dict(complete_proposal(),creation_key='!invalid!')),400)
   submitted=user.call('/api/proposals/'+p['id']+'/submit',dict(revision=p['revision'],signature=drawn_signature()))['proposal'];assert submitted['status']=='pending_advisor' and submitted['submitted_snapshot']['duration_seconds']==9000
   print('PASS: derived overnight/multiday duration, ignored client duration, minimal collaboration catalog, selected/Other logic, partial drafts, conditional support/budget requirements and immutable submission.')
  finally:srv.shutdown();srv.server_close();srv.app.db.close()

if __name__=='__main__':run()
