"""Event assignment draft collaboration and original-template conditional export."""
import base64,io,pathlib,sys,tempfile,threading,zipfile
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
import auth,server,exports
from test_registration import Client
from proposal_fixture import complete_proposal,drawn_signature

def run():
 with tempfile.TemporaryDirectory() as td,patch.object(auth,'now',return_value='2026-10-08T02:00:00+00:00'):
  srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);base='http://127.0.0.1:'+str(srv.server_port);srv.app=server.App(pathlib.Path(td)/'test.sqlite3',True,base)
  club=dict(id='club',name='Society',owner_email='demo.student@qiu.edu.my',advisor_email='demo.advisor@qiu.edu.my',committee=[dict(position='President',name='Demo Student',email='demo.student@qiu.edu.my')],status='approved',revision=1,history=[],bio='Society biography',category='Cultural',semester='October 2026',logo='',created_at=auth.now(),updated_at=auth.now())
  srv.app.put('club',club);threading.Thread(target=srv.serve_forever,daemon=True).start()
  try:
   owner=Client(base,'student');participant=Client(base,'vice');sld=Client(base,'sld');advisor=Client(base,'advisor');stranger=Client(base,'treasurer')
   fields=complete_proposal(date='2026-11-22',end_date='2026-11-22',ict_required=False,ict='Obsolete ICT',logistics_required=False,logistics='Obsolete logistics',transport='Obsolete transport',committee=[dict(email='demo.vice@qiu.edu.my',name='FORGED',university_id='FORGED',role='Coordinator',responsibility='Organise')])
   p=owner.call('/api/proposals',dict(proposal=fields))['proposal'];assert p['committee'][0]['name']=='Demo Vice President' and p['committee'][0]['university_id']!='FORGED'
   assert p['ict']==p['logistics']==p['transport']==''
   own=participant.call('/api/bootstrap')['proposals'][0];assert own['can_edit'] and not own['can_submit'] and not own['can_manage_committee']
   stranger.call('/api/proposals/'+p['id']+'/export?format=docx',status=403)
   participant.call('/api/clubs/club/export?format=pdf',status=403)
   participant.call('/api/proposals',dict(proposal=fields),403)
   participant.call('/api/proposals',dict(proposal=dict(own,committee=[])),403)
   saved=participant.call('/api/proposals',dict(proposal=dict(own,summary='Collaborative event update')))['proposal'];assert saved['summary']=='Collaborative event update'
   participant.call('/api/proposals/'+p['id']+'/submit',dict(revision=saved['revision'],signature=drawn_signature()),403)
   doc=participant.opener.open(base+'/api/proposals/'+p['id']+'/export?format=docx').read()
   with zipfile.ZipFile(io.BytesIO(doc)) as z,zipfile.ZipFile(exports.TEMPLATE) as source:
    xml=z.read('word/document.xml').decode();assert xml.count('Not applicable')>=2 and 'Obsolete' not in xml and 'Share practical learning.' in xml
    assert all(z.read(name)==source.read(name) for name in source.namelist() if name!='word/document.xml')
   # Incomplete one-objective drafts save, but cannot submit; legacy multiline inputs still normalize.
   p=owner.call('/api/proposals',dict(proposal=dict(saved,objectives=['Only one objective'])))['proposal']
   owner.call('/api/proposals/'+p['id']+'/submit',dict(revision=p['revision'],signature=drawn_signature()),400)
   p=owner.call('/api/proposals',dict(proposal=dict(p,objectives='First goal\nSecond goal')))['proposal'];assert p['objectives']==['First goal','Second goal']
   p=owner.call('/api/proposals/'+p['id']+'/submit',dict(revision=p['revision'],signature=drawn_signature()))['proposal']
   # Assignment removed through owner save on returned draft revokes event-only access immediately.
   p=advisor.call('/api/proposals/'+p['id']+'/review',dict(revision=p['revision'],action='return',comment='Revise plan'))['proposal']
   p=owner.call('/api/proposals',dict(proposal=dict(p,committee=fields['committee'][:0])))['proposal']
   assert participant.call('/api/bootstrap')['proposals']==[]
   participant.call('/api/proposals/'+p['id']+'/export?format=docx',status=403)
   print('PASS: canonical member identity, event-only draft collaboration and revoked access, no submission/assignment/club export privilege, two objectives and Not applicable original-template export.')
  finally:srv.shutdown();srv.server_close();srv.app.db.close()

if __name__=='__main__':run()
