"""Actual HTTP financial lifecycle, evidence privacy and event-only access."""
import base64,copy,pathlib,sys,tempfile,threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
import auth,server,finance,exports
from test_registration import Client
from proposal_fixture import complete_proposal

def run():
 with tempfile.TemporaryDirectory() as td,patch.object(auth,'now',return_value='2026-10-08T02:00:00+00:00'):
  srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);base='http://127.0.0.1:'+str(srv.server_port);srv.app=server.App(pathlib.Path(td)/'test.sqlite3',True,base)
  club=dict(id='club',name='Finance Society',status='approved',owner_email='demo.student@qiu.edu.my',advisor_email='demo.advisor@qiu.edu.my',committee=[dict(position='President',name='Demo Student',email='demo.student@qiu.edu.my')],history=[],revision=1,created_at=auth.now(),updated_at=auth.now())
  srv.app.put('club',club)
  p=dict(complete_proposal(date='2026-10-01',end_date='2026-10-01',committee=[dict(email='demo.vice@qiu.edu.my',name='Demo Vice President',role='Logistics',responsibility='Coordinate')],revenue=[dict(description='Tickets',price='10.00',quantity='10')],expenses=[dict(description='Materials',price='2.50',quantity='10')]),id='event',status='approved',revision=1,created_at=auth.now(),updated_at=auth.now(),history=[])
  srv.app.put('proposal',p);srv.app.put('proposal',dict(p,id='hidden',committee=[],title='Other private event'))
  threading.Thread(target=srv.serve_forever,daemon=True).start()
  try:
   president=Client(base,'student');member=Client(base,'vice');stranger=Client(base,'treasurer');advisor=Client(base,'advisor');sld=Client(base,'sld')
   boot=member.call('/api/bootstrap');assert boot['clubs']==[] and [x['id'] for x in boot['proposals']]==['event'];assert boot['event_clubs'][0]['id']=='club'
   member.call('/api/finance?club_id=club',status=403);stranger.call('/api/proposals/event/finance',status=403);member.call('/api/proposals/hidden/finance',status=403)
   initial=president.call('/api/finance?club_id=club');assert initial['balance']=='0.00' and not initial['opening_set'] and len(initial['events'])==2
   draft=dict(p,id='draft_event',status='draft',date='2026-10-09',end_date='2026-10-09',committee=[]);srv.app.put('proposal',draft)
   srv.app.log(auth.preview_user('student'),'club_draft_saved','club')
   srv.app.log(auth.preview_user('student'),'proposal_draft_saved','draft_event')
   srv.app.log(auth.preview_user('student'),'proposal_draft_saved','foreign_event','foreign_club')
   coverage=president.call('/api/finance?club_id=club');assert coverage['activity_summary']['logged_actions']==2 and coverage['activity_summary']['proposal_statuses']=={'draft':1,'approved':2}
   assert coverage['monthly'][0]['scheduled_events']==3 and coverage['monthly'][0]['events']==2 and coverage['balance']=='0.00'
   assert next(d for d in coverage['activity_days'] if d['date']=='2026-10-09')['event_statuses']['draft_event']=='draft'
   president.call('/api/finance/opening',dict(club_id='club',amount='50.00',reason='Confirmed cash'),403)
   balance=sld.call('/api/finance/opening',dict(club_id='club',amount='50.00',reason='Confirmed opening cash',approved_at='fake'));assert balance['balance']=='50.00'
   sld.call('/api/finance/opening',dict(club_id='club',amount='999.00',reason='Override'),409)
   for invalid in ('NaN','0.001','-1.00',True,1.25):
    try:finance.cents(invalid);raise AssertionError('Invalid money accepted')
    except finance.FinanceError:pass
   evidence=dict(proposal_id='event',filename='bank.pdf',mime='application/pdf',content_base64=base64.b64encode(b'%PDF-1.4\nfixture evidence').decode())
   member.call('/api/receipts',dict(evidence,mime='image/svg+xml'),400)
   receipt=member.call('/api/receipts',evidence)['receipt'];assert 'content_base64' not in receipt and receipt['uploaded_at']==auth.now()
   original_all=srv.app.all
   def no_receipt_blobs(kind):
    assert kind!='receipt','Event metadata must not load all uploaded file bodies'
    return original_all(kind)
   with patch.object(srv.app,'all',side_effect=no_receipt_blobs):
    metadata=member.call('/api/proposals/event/finance')['receipts']
    assert len(metadata)==1 and 'content_base64' not in metadata[0]
   stranger.call('/api/receipts/'+receipt['id'],status=403)
   assert member.opener.open(base+'/api/receipts/'+receipt['id']).read().startswith(b'%PDF-')
   rows=[dict(kind='income',description='Ticket collections',amount='100.00',budget_ref='revenue:0',evidence_ids=[receipt['id']]),dict(kind='expense',description='Materials paid',amount='25.00',budget_ref='expenses:0',evidence_ids=[receipt['id']])]
   report=member.call('/api/finance/reports',dict(report=dict(proposal_id='event',rows=rows,created_at='fake')))['report'];rid=report['id'];url='/api/finance/reports/'+rid
   assert report['created_at']==auth.now() and report['actual_income']=='100.00'
   advisor.call('/api/finance/reports',dict(report=report),403)
   member.call('/api/finance/reports',dict(report=dict(report,revision=0)),409)
   malformed=copy.deepcopy(report);malformed['rows'][0]['evidence_ids']=[{}];member.call('/api/finance/reports',dict(report=malformed),400)
   foreign=president.call('/api/receipts',dict(evidence,proposal_id='hidden'))['receipt'];bad=copy.deepcopy(report);bad['rows'][0]['evidence_ids']=[foreign['id']];member.call('/api/finance/reports',dict(report=bad),403)
   assert president.call('/api/finance?club_id=club')['balance']=='50.00'
   member.call(url+'/submit',dict(revision=report['revision']),400)
   report=member.call(url+'/submit',dict(revision=report['revision'],confirm_submission=True))['report'];assert report['status']=='pending_sld'
   member.call('/api/finance/reports',dict(report=report),409);member.call('/api/receipts',evidence,409)
   assert president.call('/api/finance?club_id=club')['balance']=='50.00'
   advisor.call(url+'/review',dict(revision=report['revision'],action='approve',name='Advisor'),403)
   returned=sld.call(url+'/review',dict(revision=report['revision'],action='return',name='Forged reviewer',designation='Forged title',department='Forged department',comment='Clarify evidence'))['report']
   review_identity=returned['history'][-1]
   assert review_identity['name']=='Demo SLD Officer' and review_identity['designation']=='SLD Officer' and review_identity['department']=='Student Life Division'
   notices=member.call('/api/notifications')['notifications']
   assert any(n['record_type']=='finance_report' and n['record_id']==rid for n in notices),'Event-only organiser needs financial correction notice'
   varied=copy.deepcopy(returned);varied['rows'][1]['amount']='20.00';varied=member.call('/api/finance/reports',dict(report=varied))['report']
   member.call(url+'/submit',dict(revision=varied['revision'],confirm_submission=True),400)
   varied=member.call('/api/finance/reports',dict(report=dict(varied,variance_reason='Materials cost less than planned.')))['report']
   submitted=member.call(url+'/submit',dict(revision=varied['revision'],confirm_submission=True))['report']
   from test_evidence import photo
   for colour in ('red','blue'):
    member.call('/api/photos',dict(target_type='proposal',target_id='event',name=colour+'.png',data_url=photo(colour)))
   # A failed ledger insert must roll back report approval, not create an approved report with missing postings.
   with srv.app.lock:
    srv.app.db.execute("CREATE TRIGGER fail_ledger BEFORE INSERT ON records WHEN NEW.kind='ledger_entry' BEGIN SELECT RAISE(ABORT,'test ledger failure'); END");srv.app.db.commit()
   sld.call(url+'/review',dict(revision=submitted['revision'],action='approve',name='SLD'),500)
   assert srv.app.get('finance_report',rid)['status']=='pending_sld' and not srv.app.all('ledger_entry')
   with srv.app.lock:srv.app.db.execute('DROP TRIGGER fail_ledger');srv.app.db.commit()
   other_sld=Client(base,'sld')
   with ThreadPoolExecutor(max_workers=2) as pool:
    outcomes=list(pool.map(lambda client:client.call(url+'/review',dict(revision=submitted['revision'],action='approve',name='SLD',timestamp='fake'),(200,409)),(sld,other_sld)))
   assert sum('report' in result for result in outcomes)==1
   approved=next(result['report'] for result in outcomes if 'report' in result);assert approved['approved_at']==auth.now() and approved['history'][-1]['digest']==submitted['submitted_digest']
   sld.call(url+'/review',dict(revision=approved['revision'],action='approve',name='SLD'),409)
   member.call('/api/finance/reports',dict(report=approved),409)
   final=president.call('/api/finance?club_id=club');assert final['balance']=='130.00' and len(final['entries'])==2 and final['monthly'][0]['income']=='100.00'
   assert len(srv.app.all('finance_version'))==2
   activity=member.call('/api/activity');assert all(e['record_id']=='event' for e in activity['entries'])
   raw=member.opener.open(base+url+'/export/pdf').read();assert raw.startswith(b'%PDF')
   qa=ROOT/'.agency'/'qa';qa.mkdir(parents=True,exist_ok=True);(qa/'event-financial-report.pdf').write_bytes(raw)
   long_report=copy.deepcopy(approved);long_report['rows'][0]['description']=('line\n'*190).strip();long_report['variance_reason']=('Explanation\n'*300).strip();long_report['history'][0]['comment']=('Review\n'*500).strip()
   long_pdf=exports.finance_pdf(long_report,p,club);assert long_pdf.startswith(b'%PDF');(qa/'event-financial-report-long.pdf').write_bytes(long_pdf)
   # Future planned events can have draft evidence but cannot post actual accounts before their end.
   future=dict(p,id='future',date='2026-11-01',end_date='2026-11-01');srv.app.put('proposal',future)
   freceipt=member.call('/api/receipts',dict(evidence,proposal_id='future'))['receipt'];frows=[dict(rows[0],evidence_ids=[freceipt['id']])]
   future_report=member.call('/api/finance/reports',dict(report=dict(proposal_id='future',rows=frows,variance_reason='No expenses.')))['report'];furl='/api/finance/reports/'+future_report['id']
   future_report=member.call(furl+'/submit',dict(revision=future_report['revision'],confirm_submission=True))['report'];sld.call(furl+'/review',dict(revision=future_report['revision'],action='approve',name='SLD'),400)
   assert president.call('/api/finance?club_id=club')['balance']=='130.00'
   assert b'Connect QIU Google sign-in' in president.opener.open(base+'/setup/google').read()
   css=president.opener.open(base+'/setup/google.css');assert css.status==200 and b'background:' in css.read();policy=css.headers['Content-Security-Policy'];assert "style-src-attr 'unsafe-inline'" in policy and "script-src 'self'" in policy
   print('PASS: exact cents, SLD opening, event-only access, private evidence, draft/return/variance/version guards, post-event SLD approval, once-only ledger and finance PDF.')
  finally:srv.shutdown();srv.server_close();srv.app.db.close()

if __name__=='__main__':run()
