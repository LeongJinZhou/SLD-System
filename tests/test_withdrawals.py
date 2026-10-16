"""HTTP withdrawal chain, signatures, evidence and timed access; no ledger posting."""
import base64,io,pathlib,sys,tempfile,threading,uuid,copy
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
import server,auth,withdrawals
from test_registration import Client
from test_reports import fixture_club
from proposal_fixture import drawn_signature
from concurrent.futures import ThreadPoolExecutor

def run():
 with tempfile.TemporaryDirectory() as td,patch.object(auth,'now',return_value='2026-10-09T04:00:00+00:00') as clock:
  srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);base='http://127.0.0.1:'+str(srv.server_port);srv.app=server.App(pathlib.Path(td)/'withdrawals.db',True,base);club=fixture_club();srv.app.put('club',club);threading.Thread(target=srv.serve_forever,daemon=True).start()
  try:
   president,treasurer,advisor,sld,visitor=[Client(base,p) for p in ('student','treasurer','advisor','sld','visitor')];sig=drawn_signature()
   fields=dict(club_id='club',purpose='Purchase activity supplies',amount='100',bank_name='Test Bank',account_name='Demo Treasurer',account_number='123456',items=[dict(description='Supplies',price='10',quantity='10',payment_method='Transfer')],creation_key=str(uuid.uuid4()),signatures={'sld':{'name':'FORGED'}},created_at='2000-01-01')
   visitor.call('/api/withdrawals',{'withdrawal':fields},403)
   fields['recipients']=[dict(name='Demo Treasurer',email='demo.treasurer@qiu.edu.my',contact='0123456789',bank_name='Test Bank',account_name='Demo Treasurer',account_number='123456',amount='60'),dict(name='Vendor',email='vendor@example.com',contact='',bank_name='Vendor Bank',account_name='Vendor',account_number='654321',amount='40')]
   r=president.call('/api/withdrawals',{'withdrawal':fields})['withdrawal'];assert r['signatures']=={} and r['created_at']==auth.now()
   assert president.call('/api/withdrawals',{'withdrawal':fields})['creation_replayed']
   path='/api/withdrawals/'+r['id'];president.call(path+'/submit',{'revision':r['revision'],'signature':sig},403)
   r=treasurer.call(path+'/submit',{'revision':r['revision'],'signature':sig,'name':'FORGED'})['withdrawal'];assert r['signatures']['treasurer']['name']=='Demo Treasurer'
   old=srv.app.get('withdrawal_version',r['id']+'-r'+str(r['submitted_revision']));treasurer.call('/api/withdrawals',{'withdrawal':r},409)
   r=president.call(path+'/review',{'revision':r['revision'],'action':'approve','signature':sig})['withdrawal']
   denied=advisor.call(path+'/review',{'revision':r['revision'],'action':'approve','signature':sig},409);assert denied['code']=='CONFIRMATION_REQUIRED'
   r=advisor.call(path+'/review',{'revision':r['revision'],'action':'approve','signature':sig,'confirm_submission':True})['withdrawal']
   r=sld.call(path+'/review',{'revision':r['revision'],'action':'approve','signature':sig})['withdrawal'];assert r['status']=='pending_finance'
   sld.call(path+'/all-approve',{'revision':r['revision'],'signature':sig},403)
   stream=io.BytesIO();from reportlab.pdfgen import canvas
   c=canvas.Canvas(stream);c.drawString(50,750,'Finance signed approval test');c.save();document=base64.b64encode(stream.getvalue()).decode()
   treasurer.call(path+'/finance-document',{'revision':r['revision'],'filename':'approval.pdf','content_base64':document},403)
   r=sld.call(path+'/finance-document',{'revision':r['revision'],'filename':'approval.pdf','content_base64':document})['withdrawal']
   assert sld.opener.open(base+path+'/finance-document').read()==stream.getvalue()
   r=sld.call(path+'/all-approve',{'revision':r['revision'],'signature':sig})['withdrawal'];assert r['transfer_due_at']=='2026-10-23T04:00:00+00:00'
   treasurer.call(path+'/receive',{'revision':r['revision'],'signature':sig,'confirm_submission':True},400)
   r=treasurer.call(path+'/receipt-document',{'revision':r['revision'],'filename':'Bank transfer receipt.pdf','content_base64':document})['withdrawal']
   assert treasurer.opener.open(base+path+'/receipt-document').read()==stream.getvalue()
   srv.app.put('withdrawal_document',dict(srv.app.get('withdrawal_document',r['receipt_document_id']),id='foreign-receipt',withdrawal_id='foreign'))
   treasurer.call(path+'/receive',{'revision':r['revision'],'signature':sig,'confirm_submission':True,'receipt_document_id':'foreign-receipt'},403)
   treasurer.call(path+'/receive',{'revision':r['revision'],'signature':sig},409)
   r=treasurer.call(path+'/receive',{'revision':r['revision'],'signature':sig,'confirm_submission':True,'received_at':'2000-01-01'})['withdrawal'];assert r['received_at']==auth.now()
   sld2=Client(base,'sld')
   with ThreadPoolExecutor(2) as pool:answers=list(pool.map(lambda client:client.call(path+'/acknowledge',{'revision':r['revision']},(200,409)),(sld,sld2)))
   assert sum('withdrawal' in answer for answer in answers)==1
   groups=president.call('/api/activity?grouped=1')['groups'];assert any(group['record_type']=='withdrawal' and group['record_id']==r['id'] and group['title']=='Purchase activity supplies' for group in groups)
   assert not srv.app.all('ledger_entry') and srv.app.get('withdrawal_version',old['id'])==old
   data=sld.opener.open(base+path+'/export?format=docx').read();import zipfile
   with zipfile.ZipFile(io.BytesIO(data)) as z:xml=z.read('word/document.xml');assert b'GPS Club' not in xml and b'Vendor Bank' in xml and b'Demo Treasurer' in xml and b'rIdQiuSignatureTreasurer' in z.read('word/_rels/document.xml.rels')
   import exports
   if exports.pdf_available():
    pdf=sld.opener.open(base+path+'/export?format=pdf').read();assert pdf.startswith(b'%PDF')
    out=ROOT/'.agency'/'qa';out.mkdir(parents=True,exist_ok=True);(out/'withdrawal-signed.docx').write_bytes(data);(out/'withdrawal-signed.pdf').write_bytes(pdf)
   from proposal_fixture import complete_proposal
   proposal=president.call('/api/proposals',dict(proposal=complete_proposal(date='2026-11-20',end_date='2026-11-20',expenses=[dict(description='Materials',price='100',quantity='1')])))['proposal'];proposal_path='/api/proposals/'+proposal['id']
   proposal=president.call(proposal_path+'/submit',dict(revision=proposal['revision'],signature=sig))['proposal']
   advisor.call(proposal_path+'/review',dict(revision=proposal['revision'],action='approve',signature=sig),409)
   proposal=advisor.call(proposal_path+'/review',dict(revision=proposal['revision'],action='approve',signature=sig,confirm_submission=True))['proposal']
   blocked=sld.call(proposal_path+'/review',dict(revision=proposal['revision'],action='approve',signature=sig),400);assert 'deficit_approval_reason' in blocked['fields']
   proposal=sld.call(proposal_path+'/review',dict(revision=proposal['revision'],action='approve',signature=sig,deficit_approval_reason='SLD authorises the planned educational subsidy.'))['proposal'];assert proposal['deficit_approval']['amount']=='100' and proposal['deficit_approval']['approved_by']=='demo.sld@qiu.edu.my' and proposal['deficit_approval']['approved_at']==auth.now()
   incoming=[dict(position='President',email='incoming@qiu.edu.my',name='Incoming President')]+[copy.deepcopy(row) for row in club['committee'][1:]]
   handover=dict(club,committee_handover=dict(starts_at=auth.now(),ends_at='2026-10-16T04:00:00+00:00',days=7,outgoing=club['committee'],incoming=incoming,report_id='agm'))
   srv.app.put('club',handover);assert srv.app.assigned_roles(srv.app.get('club','club'),{'email':'incoming@qiu.edu.my'})==['Pending President']
   assert srv.app.preparer_profile(srv.app.get('club','club'),{'email':'incoming@qiu.edu.my','name':'Incoming'}) is None
   clock.return_value='2026-10-16T04:00:00+00:00';president.call(path,status=403);assert srv.app.get('club','club')['owner_email']=='incoming@qiu.edu.my'
   assert all(n['record_type']!='withdrawal' for n in president.call('/api/notifications')['notifications'])
   print('PASS withdrawal ordered trusted signatures/confirmation/Finance document/all approval/receipt/ack race, immutable history, source export, zero ledger posting, exact-time pending-title handover access revocation.')
  finally:srv.shutdown();srv.server_close();srv.app.db.close()
if __name__=='__main__':run()
