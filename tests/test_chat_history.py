"""Persistent account-private chat history and revoked-source protection over HTTP."""
import pathlib,sys,tempfile,threading
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
import server,auth
from test_registration import Client

def run():
 with tempfile.TemporaryDirectory() as td:
  db=pathlib.Path(td)/'history.sqlite3';srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);base='http://127.0.0.1:'+str(srv.server_port);srv.app=server.App(db,True,base)
  club=dict(id='club',name='Private Photography Club',status='approved',semester='October 2026',revision=1,history=[],created_at=auth.now(),updated_at=auth.now(),bio='PRIVATE MEMBER DETAILS',owner_email='demo.student@qiu.edu.my',advisor_email='demo.advisor@qiu.edu.my',committee=[dict(email='demo.student@qiu.edu.my',name='Demo Student',position='President')])
  srv.app.put('club',club);threading.Thread(target=srv.serve_forever,daemon=True).start()
  try:
   member=Client(base,'student');visitor=Client(base,'visitor')
   response=member.call('/api/assistant/query',{'question':'Private Photography Club'});hid=response['history_id']
   history=member.call('/api/assistant/history');assert history['total']==1 and history['entries'][0]['available'] and history['entries'][0]['question']=='Private Photography Club'
   assert 'PRIVATE MEMBER DETAILS' in history['entries'][0]['response']['answer']
   assert visitor.call('/api/assistant/history')['total']==0
   visitor.call('/api/assistant/history/delete',{'id':hid},404)
   reopened=server.App(db,True,base);assert len(reopened.all('assistant_history'))==1;reopened.db.close()
   changed=dict(club,committee=[],owner_email='replacement@qiu.edu.my');srv.app.put('club',changed)
   hidden=member.call('/api/assistant/history')['entries'][0];assert not hidden['available'] and not hidden['response']['sources'] and 'PRIVATE MEMBER DETAILS' not in hidden['response']['answer'] and hidden['question']=='Previous question — sources changed'
   assert member.call('/api/assistant/history/delete',{'id':hid})['deleted']==1 and not member.call('/api/assistant/history')['entries']
   for question in ('Upcoming events','Next event'):visitor.call('/api/assistant/query',{'question':question})
   page=visitor.call('/api/assistant/history?limit=1');assert page['total']==2 and len(page['entries'])==1
   assert visitor.call('/api/assistant/history/delete',{'all':True})['deleted']==2
   assert visitor.call('/api/assistant/history')['total']==0
   print('PASS: persistent per-account chat, pagination, denied foreign deletion, revoked-source redaction and own deletion.')
  finally:srv.shutdown();srv.server_close();srv.app.db.close()
if __name__=='__main__':run()
