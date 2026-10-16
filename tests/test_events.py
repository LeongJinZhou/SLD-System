"""Actual HTTP event review, multi-club access and calendar/export regression."""
import base64,copy,io,pathlib,sys,tempfile,threading,urllib.error
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
import auth,server,calendar_export,exports
from datetime import datetime,timezone
from PIL import Image
from test_registration import Client
from proposal_fixture import complete_proposal,drawn_signature

def run():
 with tempfile.TemporaryDirectory() as td,patch.object(auth,'now',return_value='2026-10-08T02:00:00+00:00'):
  srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);base='http://127.0.0.1:'+str(srv.server_port)
  srv.app=server.App(pathlib.Path(td)/'test.sqlite3',True,base)
  def club(cid,owner,advisor):
   return dict(id=cid,name='Society '+cid,owner_email=owner,advisor_email=advisor,committee=[dict(position='President',email=owner,name='President')],
      category='Cultural',semester='October 2026',bio='Club biography 文化',logo='',status='approved',revision=1,history=[],created_at=auth.now(),updated_at=auth.now())
  a=club('a','demo.student@qiu.edu.my','demo.advisor@qiu.edu.my');b=club('b','other@qiu.edu.my','demo.student@qiu.edu.my');c=club('c','foreign@qiu.edu.my','foreign.advisor@qiu.edu.my')
  for item in (a,b,c):srv.app.put('club',item)
  threading.Thread(target=srv.serve_forever,daemon=True).start()
  try:
   student=Client(base,'student');advisor=Client(base,'advisor');sld=Client(base,'sld')
   boot=student.call('/api/bootstrap');assert boot['user']['role']=='student'
   roles={x['id']:x['assigned_roles'] for x in boot['clubs']};assert roles=={'a':['President'],'b':['Advisor']}
   def raw(client,path):return client.opener.open(base+path).read()
   pdf=raw(student,'/api/clubs/a/export?format=pdf');assert pdf.startswith(b'%PDF')
   student.call('/api/clubs/c/export?format=pdf',status=403)
   fields=complete_proposal(club_id='a',title='Culture, arts; evening',date='2026-11-20',end_date='2026-11-20',start_time='09:00',end_time='12:00',summary='Learn together\nwith clubs')
   student.call('/api/proposals',{'proposal':dict(fields,club_id='b')},403)
   p=student.call('/api/proposals',{'proposal':fields})['proposal'];path='/api/proposals/'+p['id']
   p=student.call(path+'/submit',{'revision':p['revision'],'signature':drawn_signature()})['proposal']
   sig=drawn_signature()
   def review(client,record,action='approve',status=200):return client.call(path+'/review',dict(revision=record['revision'],action=action,confirm_submission=True,name='Verified reviewer',signature=sig,comment='Please clarify costs' if action=='return' else '',timestamp='fake'),status)
   review(sld,p,status=403);review(student,p,status=403)
   returned=review(advisor,p,'return')['proposal'];assert returned['can_edit']==False and returned['status']=='returned'
   returned=student.call('/api/proposals',{'proposal':dict(returned,summary='Clarified plan')})['proposal']
   p=student.call(path+'/submit',{'revision':returned['revision'],'signature':drawn_signature()})['proposal']
   signed=review(advisor,p)['proposal'];assert signed['status']=='pending_sld'
   review(sld,p,status=409)
   approved=review(sld,signed)['proposal'];assert approved['status']=='approved' and approved['approved_at']==auth.now()
   assert approved['history'][-1]['digest']==approved['submitted_digest'] and approved['history'][-1]['timestamp']==auth.now()
   review(sld,approved,status=409);student.call('/api/proposals',{'proposal':approved},409)
   events=sld.call('/api/bootstrap')['calendar_events'];assert len(events)==1 and events[0]['id']==p['id']
   assert datetime.fromisoformat(events[0]['start_at']).astimezone(timezone.utc).hour==1 and datetime.fromisoformat(events[0]['end_at']).astimezone(timezone.utc).hour==4
   foreign=dict(events[0],id='foreign-event',proposal_id='foreign-event',club_id='c',title='Foreign private event');srv.app.put('calendar_event',foreign)
   ics=raw(student,'/api/calendar/export').decode();assert 'DTSTART:20261120T010000Z' in ics and 'Culture\\, arts\\; evening' in ics and 'Foreign private' not in ics
   assert 'Foreign private event' in raw(sld,'/api/calendar/export').decode()
   for i in range(130):srv.app.log(auth.preview_user('student'),'proposal_draft_saved','unrelated','c')
   activity=student.call('/api/activity?offset=0&limit=2');assert len(activity['entries'])==2 and activity['total']>2
   assert all(e['club_id'] in ('a','b') and 'signature' not in e and e['summary'] for e in activity['entries'])
   all_staff=sld.call('/api/activity?limit=100');assert all_staff['total']>activity['total']+129
   assert len(student.call('/api/activity?offset=9999')['entries'])==0
   # Same student can endorse a different club as its advisor, without changing global identity.
   pb=sld.call('/api/proposals',{'proposal':dict(fields,club_id='b',committee=[{'email':'other@qiu.edu.my','name':'Other','role':'Coordinator','responsibility':'Organise the session'}])})['proposal'];pbpath='/api/proposals/'+pb['id']
   president_b=Client(base,'vice')
   b['committee']=[dict(position='President',name='Demo Vice President',email='demo.vice@qiu.edu.my')]
   b['owner_email']='demo.vice@qiu.edu.my';srv.app.put('club',b)
   pb=president_b.call(pbpath+'/submit',{'revision':pb['revision'],'signature':drawn_signature()})['proposal']
   pb=student.call(pbpath+'/review',dict(revision=pb['revision'],action='approve',confirm_submission=True,name='Demo Student',signature=sig))['proposal'];assert pb['status']=='pending_sld'
   assert student.call('/api/bootstrap')['user']['role']=='student'
   sample=dict(a,name='Chinese Society 文化',logo=sig,history=approved['history']);out=ROOT/'.agency'/'qa';out.mkdir(parents=True,exist_ok=True);(out/'club-registration.pdf').write_bytes(exports.club_pdf(sample))
   import zipfile
   document=exports.proposal_docx(dict(approved,updated_at='2026-12-01T00:00:00+00:00'),a,auth.preview_user('student'))
   with zipfile.ZipFile(io.BytesIO(document)) as package:
    xml=package.read('word/document.xml').decode()
    from lxml import etree
    text=''.join(etree.fromstring(package.read('word/document.xml')).xpath('//w:t/text()',namespaces={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}))
    assert 'Approval and verification log' in text and approved['submitted_digest'] in text and '08/10/2026' in text
   (out/'approved-proposal.docx').write_bytes(document)
   # Fold UTF-8 lines and escape content rather than permitting injected ICS properties.
   injected=dict(events[0],title='文化'*70+'\r\nBEGIN:VEVENT');data=calendar_export.calendar_ics([injected]);assert data.replace(b'\r\n ',b'').count(b'\r\nBEGIN:VEVENT\r\n')==1
   assert all(len(line)<=75 for line in data.split(b'\r\n'));data.decode('utf-8')
   print('PASS: multi-club roles, HTTP proposal correction/endorsement/approval, immutable snapshots, calendar atomicity/scoping, registration PDF, professional scoped pagination and UTF-8 ICS safety.')
  finally:srv.shutdown();srv.server_close();srv.app.db.close()

if __name__=='__main__':run()
