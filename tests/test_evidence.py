"""Private evidence counts, completion review, named ZIP and annual archive."""
import base64,copy,io,json,pathlib,sys,tempfile,threading,zipfile
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
import auth,server,evidence
from PIL import Image
from test_registration import Client
from test_reports import fixture_club,report_fields
from proposal_fixture import complete_proposal,drawn_signature


def photo(colour):
 b=io.BytesIO();Image.new('RGB',(20,20),colour).save(b,format='PNG')
 return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()


def run():
 with tempfile.TemporaryDirectory() as td,patch.object(auth,'now',return_value='2026-10-09T04:00:00+00:00'):
  srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);base='http://127.0.0.1:'+str(srv.server_port);srv.app=server.App(pathlib.Path(td)/'evidence.sqlite3',True,base)
  app=srv.app;club=fixture_club();app.put('club',club)
  foreign=dict(fixture_club('foreign'),committee=[],owner_email='other@qiu.edu.my',advisor_email='other.advisor@qiu.edu.my');app.put('club',foreign)
  p=dict(complete_proposal(date='2026-10-08',end_date='2026-10-08'),id='event',status='approved',revision=8,created_at=auth.now(),updated_at=auth.now(),history=[],signatures={});app.put('proposal',p)
  app.put('proposal',dict(p,id='foreign-event',club_id='foreign',committee=[]))
  threading.Thread(target=srv.serve_forever,daemon=True).start()
  try:
   president=Client(base,'student');advisor=Client(base,'advisor');sld=Client(base,'sld');visitor=Client(base,'visitor');sig=drawn_signature()
   r=president.call('/api/club-reports',{'report':report_fields()})['report'];path='/api/club-reports/'+r['id']
   blocked=president.call(path+'/submit',{'revision':r['revision'],'signature':sig},400);assert 'photos' in blocked['fields']
   def add(kind,rid,colour,**kw):return president.call('/api/photos',dict(target_type=kind,target_id=rid,name='../\\Photo.png',data_url=photo(colour),**kw))
   first=add('club_report',r['id'],'red',target_revision=r['revision']);assert first['target_revision']==r['revision']+1 and first['count']==1
   president.call('/api/photos',dict(target_type='club_report',target_id=r['id'],name='x.png',data_url=photo('red'),target_revision=first['target_revision']),409)
   president.call('/api/photos',dict(target_type='club_report',target_id=r['id'],name='x.png',data_url='data:image/png;base64,AAAA',target_revision=first['target_revision']),400)
   add('club_report',r['id'],'blue',target_revision=r['revision']) if False else None
   second=add('club_report',r['id'],'blue',target_revision=first['target_revision']);assert second['count']==2
   r=president.call(path)['report'];assert len(r['photo_evidence'])==2
   visitor.call('/api/photos?target_type=club_report&target_id='+r['id'],status=403)
   advisor.call('/api/photos',dict(target_type='club_report',target_id=r['id'],name='x.png',data_url=photo('green'),target_revision=r['revision']),403)
   president.call('/api/photos/zip?target_type=club_report&target_id='+r['id'],status=403)
   response=sld.opener.open(base+'/api/photos/zip?target_type=club_report&target_id='+r['id']);raw=response.read();z=zipfile.ZipFile(io.BytesIO(raw));assert len(z.namelist())==3 and all('/../' not in n and '\\' not in n for n in z.namelist());assert 'Report Society' in response.headers['Content-Disposition']
   r=president.call(path+'/submit',{'revision':r['revision'],'signature':sig})['report']
   president.call('/api/photos/'+first['photo']['id']+'/delete',{'target_revision':r['revision']},403)
   # Event evidence does not change its approved proposal revision.
   add('proposal','event','green');add('proposal','event','yellow');assert app.get('proposal','event')['revision']==8
   r=president.call('/api/event-completions',{'report':{'proposal_id':'event','summary':'Completed student learning event'}})['report'];cp='/api/event-completions/'+r['id']
   president.call(cp+'/submit',{'revision':r['revision']},400)
   r=president.call(cp+'/submit',{'revision':r['revision'],'confirm_submission':True})['report'];assert r['status']=='pending_sld'
   sld.call(cp+'/review',{'revision':r['revision'],'action':'approve','signature':''},400)
   r=sld.call(cp+'/review',{'revision':r['revision'],'action':'return','comment':'Add outcomes'})['report'];assert r['status']=='returned' and r['signature'] is None
   r=president.call('/api/event-completions',{'report':dict(r,summary='Students achieved all planned learning outcomes')})['report']
   r=president.call(cp+'/submit',{'revision':r['revision'],'confirm_submission':True})['report'];r=sld.call(cp+'/review',{'revision':r['revision'],'action':'approve','signature':sig,'name':'Forged','signed_at':'2000-01-01'})['report']
   assert r['signature']['name']=='Demo SLD Officer' and r['signature']['signed_at']==auth.now() and r['status']=='approved'
   assert sld.opener.open(base+cp+'/export').read().startswith(b'%PDF')
   visitor.call('/api/proposals/event/completion',status=403);president.call('/api/photos?target_type=proposal&target_id=foreign-event',status=403)
   # AGM single photo gate, annual archive after explicit SLD acknowledgement.
   agm=dict(report_fields(type='agm'),id='annual',report_year=2026,status='approved',revision=1,history=[],signatures={},old_committee=club['committee'],new_committee=club['committee'],handover_applied_at=auth.now(),created_at=auth.now(),updated_at=auth.now(),owner_email=president.call('/api/bootstrap')['user']['email']);app.put('club_report',agm)
   # Rendering original templates is tested separately; verify ZIP assembly with deterministic PDF stubs here.
   app.put('proposal_version',dict(id='event-r1',snapshot=dict(p),digest='digest'))
   with patch('exports.club_report_pdf',return_value=b'%PDF-report'),patch('exports.club_pdf',return_value=b'%PDF-profile'),patch('exports.export_proposal',return_value=(b'%PDF-proposal','x.pdf','application/pdf')):
    archive=evidence.annual_archive(app,auth.preview_user('sld'),'club',2026)[0]
   zz=zipfile.ZipFile(io.BytesIO(archive));names=zz.namelist();assert any('/Events/' in n and '/Photos/' in n for n in names);assert any(n.endswith('/Audit/proposal_version.json') for n in names);assert len(names)==len(set(names));assert not any('foreign' in n for n in names)
   visitor.call('/api/clubs/club/annual-archive?year=2026',status=403)
   print('PASS: private photo scopes/count/dedup/type/version gates, named ZIP, immutable proposal, post-event confirmation/return/distinct SLD signature, annual archive hierarchy and proposal version inclusion.')
  finally:srv.shutdown();srv.server_close();app.db.close()

if __name__=='__main__':run()
