"""Real HTTP signing authority, immutable identities/versions and original-cell export."""
import base64,copy,hashlib,io,json,pathlib,sys,tempfile,threading,zipfile
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
import auth,server,exports
from PIL import Image
from test_registration import Client
from proposal_fixture import complete_proposal,drawn_signature


def run():
 with tempfile.TemporaryDirectory() as td,patch.object(auth,'now',return_value='2026-10-08T02:00:00+00:00'):
  srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);base='http://127.0.0.1:'+str(srv.server_port)
  srv.app=server.App(pathlib.Path(td)/'signatures.sqlite3',True,base)
  members=[dict(position=position,email=auth.PREVIEW_PEOPLE[index]['email'],name=auth.PREVIEW_PEOPLE[index]['name']) for position,index in (('President',0),('Vice President',3),('Secretary',4),('Treasurer',5))]
  club=dict(id='club',name='Signature Society',owner_email='demo.student@qiu.edu.my',advisor_email='demo.advisor@qiu.edu.my',committee=members,status='approved',revision=1,history=[],created_at=auth.now(),updated_at=auth.now())
  srv.app.put('club',club);threading.Thread(target=srv.serve_forever,daemon=True).start()
  try:
   president,vice,secretary,treasurer,advisor,sld=[Client(base,p) for p in ('student','vice','secretary','treasurer','advisor','sld')]
   sig=drawn_signature()
   def draft(**fields):return president.call('/api/proposals',dict(proposal=complete_proposal(**dict(date="2026-11-22",end_date="2026-11-22",**fields))))['proposal']
   def submit(client,p,status=200,**fields):return client.call('/api/proposals/'+p['id']+'/submit',dict(revision=p['revision'],signature=sig,**fields),status)
   def review(client,p,action='approve',status=200,**fields):return client.call('/api/proposals/'+p['id']+'/review',dict(revision=p['revision'],action=action,confirm_submission=True,signature=sig,comment='Correct the proposal' if action=='return' else '',**fields),status)
   p=draft();path='/api/proposals/'+p['id']
   for client in (secretary,treasurer,advisor,sld):submit(client,p,403)
   president.call(path+'/submit',dict(revision=p['revision']),400)
   blank=io.BytesIO();Image.new('RGBA',(240,90),(255,255,255,0)).save(blank,format='PNG')
   for invalid in ('data:image/png;base64,iVBORw0KGgo=','data:image/png;base64,'+base64.b64encode(blank.getvalue()).decode()):
    president.call(path+'/submit',dict(revision=p['revision'],signature=invalid),400)
   assert srv.app.get('proposal',p['id'])['revision']==p['revision'],'Invalid signatures must not mutate the record'
   # Both allowed preparers race the same draft. Exactly one wins, regardless of arrival order.
   with ThreadPoolExecutor(2) as pool:
    outcomes=list(pool.map(lambda client:submit(client,p,(200,409)),(president,vice)))
   assert sum('proposal' in result for result in outcomes)==1
   p=next(result['proposal'] for result in outcomes if 'proposal' in result)
   preparer=p['signatures']['preparer'];assert preparer['name'] in ('Demo Student','Demo Vice President')
   assert (preparer['designation'] in (club['name']+' · President',club['name']+' · Vice President') or preparer['designation'] in [m.get('role') for m in p.get('committee',[]) if m.get('email')==preparer['email']]) and preparer['department']==club['name'] and preparer['signed_at']==auth.now()
   snapshot=copy.deepcopy(p['submitted_snapshot']);assert 'digest' not in snapshot['signatures']['preparer']
   assert hashlib.sha256(json.dumps(snapshot,sort_keys=True).encode()).hexdigest()==p['submitted_digest']
   assert len(srv.app.all('proposal_signature'))==1
   review(president,p,status=403);review(sld,p,status=403)
   p=review(advisor,p,name='Forged Advisor',designation='Forged Professor',department='Forged',signed_at='2000-01-01')['proposal']
   signer=p['signatures']['advisor'];assert signer['name']=='Demo Advisor' and signer['designation']=='Club Advisor' and signer['department']=='Demo faculty' and signer['signed_at']==auth.now()
   first_revision=p['submitted_revision'];first_digest=p['submitted_digest'];old_signatures=copy.deepcopy(srv.app.all('proposal_signature'))
   # Returning a signed version clears active cells, but its signature records and hashed snapshot remain intact.
   p=review(sld,p,'return')['proposal'];assert p['signatures']=={} and any(h.get('signer') for h in p['history'])
   assert srv.app.get('proposal_version',p['id']+'-r'+str(first_revision))['snapshot']==snapshot
   p=president.call('/api/proposals',dict(proposal=dict(p,summary='Corrected proposal',signatures={'sld':{'signature':sig}},submitted_at='2000-01-01')))['proposal']
   with patch.object(auth,'now',return_value='2026-10-09T03:00:00+00:00'):
    p=submit(president,p,name='Forged Student',designation='Treasurer',department='Wrong',signed_at='2000-01-01',slot='sld')['proposal']
   assert set(p['signatures'])=={'preparer'} and p['signatures']['preparer']['name']=='Demo Student' and p['signatures']['preparer']['signed_at']=='2026-10-09T03:00:00+00:00'
   assert p['submitted_revision']!=first_revision and p['submitted_digest']!=first_digest
   assert all(record in srv.app.all('proposal_signature') for record in old_signatures)
   p=review(advisor,p)['proposal'];p=review(sld,p)['proposal']
   assert set(p['signatures'])=={'preparer','advisor','sld'} and p['signatures']['sld']['name']=='Demo SLD Officer'
   assert all(s['revision']==p['submitted_revision'] and s['digest']==p['submitted_digest'] for s in p['signatures'].values())
   review(sld,p,status=409)
   # Signature images occupy only the selected source approval cells; no invented template signers.
   doc=exports.proposal_docx(p,dict(club,advisor_profile=srv.app.advisor_profile(club)),auth.preview_user('student'))
   from lxml import etree
   ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
   with zipfile.ZipFile(io.BytesIO(doc)) as package:
    xml=etree.fromstring(package.read('word/document.xml'));drawings=xml.findall('.//w:drawing',ns)
    assert {blip.get('{'+ns['r']+'}embed') for blip in xml.findall('.//a:blip',ns) if blip.get('{'+ns['r']+'}embed','').startswith('rIdQiuSignature')}=={'rIdQiuSignaturePreparer','rIdQiuSignatureAdvisor','rIdQiuSignatureSld'}
    text=' '.join(xml.xpath('//w:t/text()',namespaces=ns));assert all(name in text for name in ('Demo Student','Demo Advisor','Demo SLD Officer'))
   # Existing unsigned submissions can be returned, but must not acquire valid signatures by approval.
   legacy=dict(p,id='legacy',status='pending_advisor',revision=1,history=[],signatures={})
   srv.app.put('proposal',legacy)
   error=review(advisor,legacy,status=409);assert error['code']=='SIGNATURE_REQUIRED'
   legacy=review(advisor,legacy,'return')['proposal'];assert legacy['status']=='returned' and legacy['signatures']=={}
   # A current SLD committee member cannot endorse their own club proposal, even if another officer prepared it.
   q=draft();q=submit(president,q)['proposal'];q=review(advisor,q)['proposal']
   changed=copy.deepcopy(club);changed['committee'].append(dict(position='Support',email='demo.sld@qiu.edu.my',name='Demo SLD Officer'));srv.app.put('club',changed)
   review(sld,q,status=403)
   print('PASS: real PNG/nonblank validation, preparer race and authority, immutable profile/time/digest/slots, return/resign history, legacy rejection, self-review and original-cell images.')
  finally:srv.shutdown();srv.server_close();srv.app.db.close()

if __name__=='__main__':run()
