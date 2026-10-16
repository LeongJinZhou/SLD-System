"""Withdrawal workflow; authorized requests never post a provisional ledger balance."""
import base64,copy,hashlib,json,re,secrets,uuid
from datetime import datetime,timedelta
from decimal import Decimal,InvalidOperation
import auth,club_reports
STAGES={'pending_president':'president','pending_advisor':'advisor','pending_sld':'sld'}
FIELDS=('club_id','purpose','amount','bank_name','account_name','account_number','event_title','event_date','contact_name','contact_email','contact_phone')

def fail(message,status=400,code=None,fields=None):
 from server import APIError
 raise APIError(message,status,code,fields)

def allowed(app,user,r,club):return app.visible(club,user)

def slot(app,user,r,club):
 stage='treasurer' if r['status'] in ('draft','returned') else STAGES.get(r['status'])
 if stage=='sld':eligible=user['role']=='sld' and not club_reports.committee(user,club) and user['email']!=club.get('advisor_email')
 elif stage=='advisor':eligible=club.get('advisor_email')==user['email']
 elif stage:eligible=club_reports.position_email(club,stage.title())==user['email']
 else:return None
 if not eligible or any(s.get('email')==user['email'] for s in r.get('signatures',{}).values()):return None
 return stage

def profile(app,user,club,stage):
 if stage in ('treasurer','president'):return dict(name=user.get('name') or 'Unavailable',email=user['email'],designation=club['name']+' · '+stage.title(),department=club['name'])
 return app.reviewer_profile(user,stage)

def decorate(app,user,r,club):
 current=slot(app,user,r,club)
 sld=user['role']=='sld' and not club_reports.committee(user,club) and user['email']!=club.get('advisor_email')
 receipt=r['status']=='waiting_transfer' and club_reports.position_email(club,'Treasurer')==user['email']
 return dict(r,can_edit=club_reports.committee(user,club) and r['status'] in ('draft','returned'),can_sign=bool(current),signing_slot=current,signer_profile=profile(app,user,club,current) if current else (profile(app,user,club,'treasurer') if receipt else (app.reviewer_profile(user,'sld') if sld and r['status']=='pending_all_approve' else None)),can_upload_finance=sld and r['status']=='pending_finance',can_all_approve=sld and r['status']=='pending_all_approve',can_receive=receipt and bool(r.get('receipt_document_id')),can_upload_receipt=receipt,can_acknowledge=sld and r['status']=='pending_acknowledgement')

def list_for(app,user):
 clubs={c['id']:c for c in app.all('club')}
 return [decorate(app,user,r,clubs[r['club_id']]) for r in app.all('withdrawal') if r.get('club_id') in clubs and allowed(app,user,r,clubs[r['club_id']])]

def handle_get(app,user,path,query):
 if path=='/api/withdrawals':return dict(withdrawals=list_for(app,user))
 match=re.fullmatch(r'/api/withdrawals/([A-Za-z0-9_-]+)(/finance-document|/receipt-document|/export)?',path)
 if not match:return None
 r=app.get('withdrawal',match[1]);club=app.get('club',r['club_id'])
 if not allowed(app,user,r,club):fail('You cannot access this withdrawal.',403)
 if match[2] in ('/finance-document','/receipt-document'):
  document=app.get('withdrawal_document',r.get('receipt_document_id' if match[2]=='/receipt-document' else 'finance_document_id',''))
  return base64.b64decode(document['content_base64']),document['mime'],document['filename']
 if match[2]=='/export':
  import exports
  fmt=query.get('format',['pdf'])[0]
  function={'pdf':withdrawal_pdf,'docx':withdrawal_docx}.get(fmt)
  if not function:fail('Withdrawal export is not configured.',503)
  return function(r,club),'application/pdf' if fmt=='pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document','withdrawal.'+fmt
 return dict(withdrawal=decorate(app,user,r,club))

def handle_post(app,user,path,data):
 from server import text,image
 if path=='/api/withdrawals':
  source=data.get('withdrawal')
  if not isinstance(source,dict):fail('Withdrawal form is required.')
  previous=app.get('withdrawal',source['id']) if source.get('id') else None
  club=app.get('club',previous['club_id'] if previous else source.get('club_id',''))
  if club['status']!='approved' or not club_reports.committee(user,club):fail('Only the current approved club committee can prepare a withdrawal.',403)
  if previous and (source.get('revision')!=previous['revision'] or previous['status'] not in ('draft','returned')):fail('The withdrawal changed or is locked. Reopen its current version.',409)
  if source.get('club_id',club['id'])!=club['id']:fail('The organizing club cannot change.',403)
  mapping=None
  if not previous and source.get('creation_key'):
   try:key=str(uuid.UUID(source['creation_key']))
   except (ValueError,TypeError,AttributeError):fail('Use a valid creation key.')
   mid=hashlib.sha256((user['email']+'|'+club['id']+'|'+key).encode()).hexdigest()
   found=next((m for m in app.all('withdrawal_creation') if m['id']==mid),None)
   if found:
    existing=app.get('withdrawal',found['withdrawal_id'])
    if existing['revision']!=1:fail('The recovered withdrawal changed. Reopen its latest version.',409)
    return dict(withdrawal=decorate(app,user,existing,club),creation_replayed=True)
   mapping=dict(id=mid)
  r={key:text(source.get(key,''),5000 if key=='purpose' else 250) for key in FIELDS if key not in ('amount','club_id')};r['club_id']=club['id']
  try:amount=Decimal(str(source.get('amount') or 0))
  except InvalidOperation:fail('Enter a valid withdrawal amount.')
  if not amount.is_finite() or amount<0 or amount>Decimal('10000000') or amount.as_tuple().exponent<-2:fail('Amount must have at most two decimal places.')
  rows=source.get('items',[])
  if not isinstance(rows,list) or len(rows)>100 or any(not isinstance(row,dict) for row in rows):fail('Use valid withdrawal item rows.')
  r['items']=[]
  for row in rows:
   try:price=Decimal(str(row.get('price') or 0));quantity=Decimal(str(row.get('quantity') or 0))
   except InvalidOperation:fail('Item price and quantity must be numbers.')
   if not price.is_finite() or not quantity.is_finite() or price<0 or quantity<0 or price>10000000 or quantity>1000000 or price.as_tuple().exponent<-2 or (price*quantity).quantize(Decimal('0.01'))!=price*quantity:fail('Use nonnegative bounded item amounts.')
   r['items'].append(dict(description=text(row.get('description',''),2000),price=str(price),quantity=str(quantity),payment_method=text(row.get('payment_method',''),250)))
  recipients=source.get('recipients',[])
  if not isinstance(recipients,list) or len(recipients)>30 or any(not isinstance(row,dict) for row in recipients):fail('Use valid recipient account rows.')
  r['recipients']=[]
  for row in recipients:
   recipient={key:text(row.get(key,''),250) for key in ('name','email','contact','bank_name','account_name','account_number')}
   try:recipient_amount=Decimal(str(row.get('amount') or 0))
   except InvalidOperation:fail('Recipient amounts must be valid numbers.')
   if not recipient_amount.is_finite() or recipient_amount<0 or recipient_amount>10000000 or recipient_amount.as_tuple().exponent<-2:fail('Use nonnegative recipient amounts with at most two decimal places.')
   recipient['amount']=str(recipient_amount)
   if recipient['email'] and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',recipient['email']):fail('Enter a valid recipient email address.')
   r['recipients'].append(recipient)
  r['amount']=str(amount);stamp=auth.now();r.update(id=previous['id'] if previous else secrets.token_urlsafe(12),revision=previous['revision']+1 if previous else 1,status=previous['status'] if previous else 'draft',created_at=previous['created_at'] if previous else stamp,updated_at=stamp,owner_email=previous['owner_email'] if previous else user['email'],history=previous.get('history',[]) if previous else [],signatures={})
  records=[('withdrawal',r)]
  if mapping:mapping['withdrawal_id']=r['id'];records.append(('withdrawal_creation',mapping))
  app.put_batch(records);app.log(user,'withdrawal_draft_saved',r['id'],club['id']);return dict(withdrawal=decorate(app,user,r,club))
 match=re.fullmatch(r'/api/withdrawals/([A-Za-z0-9_-]+)/(submit|review|finance-document|receipt-document|all-approve|receive|acknowledge)',path)
 if not match:return None
 r=app.get('withdrawal',match[1]);club=app.get('club',r['club_id'])
 if not allowed(app,user,r,club):fail('You cannot access this withdrawal.',403)
 if type(data.get('revision')) is not int or data['revision']!=r['revision']:fail('The withdrawal changed. Reopen its current version.',409)
 r=copy.deepcopy(r);stage=slot(app,user,r,club);action=match[2];stamp=auth.now();records=[];signer=None
 if action=='submit':
  if stage!='treasurer':fail('Only the current Treasurer can sign and submit this draft.',403)
  required=('purpose',) if r.get('recipients') else ('purpose','bank_name','account_name','account_number')
  errors={key:'Complete this field.' for key in required if not r.get(key)}
  if r.get('recipients') and (any(any(not row.get(key) for key in ('name','bank_name','account_name','account_number')) or Decimal(row['amount'])<=0 for row in r['recipients']) or sum(Decimal(row['amount']) for row in r['recipients'])!=Decimal(r['amount'])):errors['recipients']='Complete recipient accounts and reconcile their total with the requested amount.'
  if Decimal(r['amount'])<=0:errors['amount']='Enter a positive amount.'
  if r.get('items') and (any(not row['description'] or Decimal(row['quantity'])<=0 for row in r['items']) or sum(Decimal(row['price'])*Decimal(row['quantity']) for row in r['items'])!=Decimal(r['amount'])):errors['items']='Complete item details and reconcile their total with the requested amount.'
  if errors:fail('Complete the withdrawal details.',fields=errors)
  if len({club_reports.position_email(club,'Treasurer'),club_reports.position_email(club,'President'),club.get('advisor_email')})!=3 or not club_reports.position_email(club,'President'):fail('Treasurer, President and advisor must be distinct assigned people.',409)
  r.update(status='pending_president',submitted_at=stamp,submitted_revision=r['revision']+1,signatures={})
  signer=dict(profile(app,user,club,stage),slot=stage,signature=image(data.get('signature',''),True,True),signed_at=stamp,revision=r['submitted_revision']);r['signatures'][stage]=signer
  snapshot=copy.deepcopy({k:v for k,v in r.items() if k not in ('history','submitted_digest')});snapshot['revision']=r['submitted_revision'];digest=hashlib.sha256(json.dumps(snapshot,sort_keys=True).encode()).hexdigest();r['submitted_digest']=digest;signer['digest']=digest
  records.append(('withdrawal_version',dict(id=r['id']+'-r'+str(r['submitted_revision']),withdrawal_id=r['id'],snapshot=snapshot,digest=digest)))
 elif action=='review':
  if stage not in ('president','advisor','sld'):fail('This review stage is not assigned to you.',403)
  choice=data.get('action');comment=text(data.get('comment',''),5000)
  if choice not in ('approve','return'):fail('Choose approve or return.')
  if choice=='return':
   if not comment:fail('A correction reason is required.')
   r['status']='returned';r['signatures']={}
  else:
   if stage=='advisor' and data.get('confirm_submission') is not True:fail('Confirm submission to SLD before continuing.',409,'CONFIRMATION_REQUIRED')
   required={'president':['treasurer'],'advisor':['treasurer','president'],'sld':['treasurer','president','advisor']}[stage]
   if any(r.get('signatures',{}).get(k,{}).get('digest')!=r.get('submitted_digest') for k in required):fail('Previous bound signatures are required.',409)
   signer=dict(profile(app,user,club,stage),slot=stage,signature=image(data.get('signature',''),True,True),signed_at=stamp,revision=r['submitted_revision'],digest=r['submitted_digest']);r['signatures'][stage]=signer;r['status']={'president':'pending_advisor','advisor':'pending_sld','sld':'pending_finance'}[stage]
  action=choice
 elif action in ('finance-document','receipt-document'):
  receiving=action=='receipt-document'
  if not decorate(app,user,r,club)['can_upload_receipt' if receiving else 'can_upload_finance']:fail('This document upload is not assigned to you at the current stage.',403)
  try:raw=base64.b64decode(data.get('content_base64',''),validate=True)
  except (ValueError,TypeError):fail('Upload a valid approval or fund receipt file.')
  if not raw or len(raw)>3*1024*1024:fail('Approval or receipt document must be at most3MB.')
  if raw.startswith(b'%PDF-'):
   try:
    from pypdf import PdfReader
    import io
    reader=PdfReader(io.BytesIO(raw));assert not reader.is_encrypted and len(reader.pages)>0
   except Exception:fail('Upload a readable, unencrypted PDF.')
   mime='application/pdf'
  else:
   try:
    from PIL import Image
    import io
    with Image.open(io.BytesIO(raw)) as picture:
     picture.verify();mime={'PNG':'image/png','JPEG':'image/jpeg'}.get(picture.format)
   except Exception:fail('Approval or receipt must be a PDF or PNG/JPEG image.')
   if not mime:fail('Approval or receipt must be a PDF or PNG/JPEG image.')
  filename=text(data.get('filename','Finance approval.pdf'),150);filename=re.sub(r'[^A-Za-z0-9_. -]','_',filename)
  doc=dict(id=r['id']+('-receipt-r' if receiving else '-finance-r')+str(r['revision']+1),document_type='fund_receipt' if receiving else 'finance_approval',submitted_revision=r['submitted_revision'],digest=r['submitted_digest'],withdrawal_id=r['id'],club_id=club['id'],filename=filename,mime=mime,content_base64=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest(),uploaded_at=stamp,uploaded_by=user['email'])
  records.append(('withdrawal_document',doc))
  if receiving:r.update(receipt_document_id=doc['id'],receipt_document_sha256=doc['sha256'])
  else:r.update(status='pending_all_approve',finance_document_id=doc['id'],finance_document_sha256=doc['sha256'])
 elif action=='all-approve':
  if not decorate(app,user,r,club)['can_all_approve']:fail('Only SLD can verify the completed approval package.',403)
  approval=app.get('withdrawal_document',r.get('finance_document_id',''))
  if approval.get('withdrawal_id')!=r['id'] or approval.get('document_type')!='finance_approval' or approval.get('submitted_revision')!=r['submitted_revision'] or approval.get('digest')!=r['submitted_digest'] or approval.get('sha256')!=r.get('finance_document_sha256'):fail('Finance approval must belong to this submitted withdrawal version.',409)
  signer=dict(profile(app,user,club,'sld'),slot='all_approve',signature=image(data.get('signature',''),True,True),signed_at=stamp,revision=r['submitted_revision'],digest=r['submitted_digest']);r['signatures']['all_approve']=signer
  days=app.settings()['transfer_days'];r.update(status='waiting_transfer',all_approved_at=stamp,transfer_due_at=(datetime.fromisoformat(stamp)+timedelta(days=days)).isoformat(),transfer_days_at_approval=days)
 elif action=='receive':
  if r['status']!='waiting_transfer' or club_reports.position_email(club,'Treasurer')!=user['email']:fail('Only the current Treasurer can confirm actual fund receipt.',403)
  proof_id=data.get('receipt_document_id') or r.get('receipt_document_id')
  if not proof_id:fail('Upload the actual bank-in or transfer receipt before confirming funds received.',fields={'receipt_document_id':'Upload the fund receipt.'})
  proof=app.get('withdrawal_document',proof_id)
  if proof.get('withdrawal_id')!=r['id'] or proof.get('document_type')!='fund_receipt' or proof_id!=r.get('receipt_document_id') or proof.get('sha256')!=r.get('receipt_document_sha256') or proof.get('submitted_revision')!=r['submitted_revision'] or proof.get('digest')!=r['submitted_digest']:fail('Fund receipt must belong to this withdrawal and current proof version.',403)
  if hashlib.sha256(base64.b64decode(proof['content_base64'])).hexdigest()!=proof['sha256']:fail('The stored receipt failed its integrity check.',409)
  if data.get('confirm_submission') is not True:fail('Confirm submission of fund receipt to SLD before continuing.',409,'CONFIRMATION_REQUIRED')
  signer=dict(profile(app,user,club,'treasurer'),slot='received',signature=image(data.get('signature',''),True,True),signed_at=stamp,revision=r['submitted_revision'],digest=r['submitted_digest']);r['signatures']['received']=signer;r.update(status='pending_acknowledgement',received_at=stamp)
 else:
  if not decorate(app,user,r,club)['can_acknowledge']:fail('Only SLD can acknowledge the recorded receipt.',403)
  r.update(status='acknowledged',acknowledged_at=stamp,acknowledged_by=user['email'])
 r.update(revision=r['revision']+1,updated_at=stamp);r['history'].append(dict(action=action,stage=stage,actor=user['email'],timestamp=stamp,comment=text(data.get('comment',''),5000),signer=copy.deepcopy(signer)))
 if signer:records.append(('withdrawal_signature',dict(signer,id=r['id']+'-r'+str(r['submitted_revision'])+'-'+signer['slot'],withdrawal_id=r['id'],club_id=club['id'])))
 records.append(('withdrawal',r));app.put_batch(records);app.log(user,'withdrawal_'+action,r['id'],club['id']);return dict(withdrawal=decorate(app,user,r,club),**({'document':{k:v for k,v in doc.items() if k!='content_base64'}} if action in ('finance-document','receipt-document') else {}))


def withdrawal_docx(report,club):
 import exports,zipfile,io
 from pathlib import Path
 template=Path(__file__).parent/'templates'/'withdrawal.docx'
 with zipfile.ZipFile(template) as archive:
  xml=exports.ET.fromstring(archive.read('word/document.xml'));body=xml.find(exports.W+'body');tables=xml.xpath('//w:tbl',namespaces=exports.NS)
  rels=exports.ET.fromstring(archive.read('word/_rels/document.xml.rels'));added={}
  exports._field(tables[1],1,1,club['name']);exports._field(tables[1],3,1,exports._date(report.get('submitted_at')))
  paragraphs=body.findall(exports.W+'p')
  exports._text(paragraphs[6],club['name']+' requests RM'+str(report.get('amount',''))+' from its club fund for '+report.get('purpose','')+'. '+('Event: '+report.get('event_title','')+'; planned date: '+report.get('event_date','')+'.' if report.get('event_title') else ''))
  recipients=report.get('recipients') or [dict(name=report.get('contact_name',''),email=report.get('contact_email',''),contact=report.get('contact_phone',''),bank_name=report.get('bank_name',''),account_name=report.get('account_name',''),account_number=report.get('account_number',''),amount=report.get('amount',''))]
  keys=('name','email','contact','bank_name','account_name','account_number','amount');labels=('Individual/Company Name','Email Address','Contact No','Bank Name','Account Holder Name','Account number','Amount')
  pattern=[copy.deepcopy(paragraph) for paragraph in paragraphs[13:20]]
  for index in range(13,20):exports._text(paragraphs[index],'')
  for index in range(21,28):exports._text(paragraphs[index],'')
  for n,recipient in enumerate(recipients):
   target=paragraphs[13:20] if n==0 else paragraphs[21:28] if n==1 else [copy.deepcopy(paragraph) for paragraph in pattern]
   for paragraph,label,key in zip(target,labels,keys):exports._text(paragraph,label+': '+str(recipient.get(key,'')))
   if n>1:
    for paragraph in target:paragraphs[28].addprevious(paragraph)

  exports._text(paragraphs[29],'A petty cash record and supporting receipts will be submitted after the activity. Any remaining funds will be returned to '+club['name']+'.')
  rows=[dict(number=i+1,item=row.get('description',''),price=row.get('price',''),quantity=row.get('quantity',''),total=str(Decimal(row.get('price','0'))*Decimal(row.get('quantity','0'))),payment_method=row.get('payment_method','')) for i,row in enumerate(report.get('items',[]))]
  rows.append(dict(item='Total',total=report.get('amount','')))
  exports._repeat(tables[2],rows,['number','item','price','quantity','total','payment_method'])
  for table,slots in [(tables[3],['treasurer','president']),(tables[4],['advisor','sld',None,'all_approve'])]:
   cells=exports._cells(exports._rows(table)[0])
   for cell,slot in zip(cells,slots):
    exports._report_signature_cell(xml,cell,'Finance signed approval document' if slot is None else slot.replace('_',' ').title(),report,slot or 'finance',archive,rels,added)
   for row in exports._rows(table)[1:]:table.remove(row)
  exports._append_block(body,exports._paragraph('Transfer and receipt verification',True))
  exports._append_block(body,exports._simple_table(['Stage','Server record'],[['Finance signed document',report.get('finance_document_sha256','')],['Transfer deadline',report.get('transfer_due_at','')],['Fund receipt document',report.get('receipt_document_sha256','')],['Treasurer received',report.get('received_at','')],['SLD acknowledged',report.get('acknowledged_at','')]], [2500,6500]))
  receipt=exports._simple_table(['Treasurer receipt signature'],[['']], [9000]);cell=exports._cells(exports._rows(receipt)[1])[0];exports._report_signature_cell(xml,cell,'Fund receipt',report,'received',archive,rels,added);exports._append_block(body,receipt)
  exports._audit_appendix(body,report)
  return exports._report_package(archive,xml,rels,added)

def withdrawal_pdf(report,club):
 import exports
 return exports.docx_pdf(withdrawal_docx(report,club))
