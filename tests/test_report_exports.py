"""Template report signatures, professional audit log and representative PDF rendering."""
import pathlib,sys,io,copy,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
import exports,auth
from proposal_fixture import drawn_signature,complete_proposal
from lxml import etree as ET

def sample(kind='agm'):
 r=dict(id='qa-'+kind,club_id='club',type=kind,title='Annual leadership review' if kind=='agm' else 'Weekly photography meeting',semester='October 2026',date='2026-10-07',start_time='15:00',end_time='16:30',venue='QIU Student Centre',activity_kind='meeting',summary='Review club activities and prepare a clear transition for the next committee.',objectives=['Review the outgoing committee accomplishments.','Elect the new committee.'],attendance=[dict(name='Demo Student',email='demo.student@qiu.edu.my',status='present',university_id='QIU-202404-007157',programme='MBBS'),dict(name='Demo Vice President',email='demo.vice@qiu.edu.my',status='absent',university_id='QIU-202404-007158',programme='Business')],member_count=2,minutes='The committee reviewed member attendance and discussed the next weekly session.\nThe advisor acknowledged the planned action items.',decisions=[dict(task='Confirm the venue',person='Demo Secretary',deadline='2026-10-15')],next_meeting=dict(date='2026-10-14',time='15:00',venue='QIU Student Centre'),opening_speech='The President welcomed members and reviewed the semester.',agenda=[dict(start='15:00',end='15:30',agenda='Attendance and opening speech'),dict(start='15:30',end='16:30',agenda='Election and handover')],outgoing_activities='Organised two approved events and four weekly meetings.',election_summary='Four mandatory positions were elected with one candidate appointed to each role.',adjournment='The meeting adjourned at 16:30 MYT.',old_committee=[dict(position=role,name='Outgoing '+role,email=role.replace(' ','').lower()+'@qiu.edu.my',university_id='QIU-202404-007157',programme='') for role in ['President','Vice President','Secretary','Treasurer']],new_committee=[dict(position=role,name='Incoming '+role,email='new.'+role.replace(' ','').lower()+'@qiu.edu.my',university_id='QIU-202404-007158',programme='') for role in ['President','Vice President','Secretary','Treasurer']],status='approved',revision=7,submitted_revision=3,submitted_digest='a'*64,submitted_at='2026-10-08T02:00:00+00:00',created_at='2026-10-07T02:00:00+00:00',updated_at='2026-10-09T02:00:00+00:00',signatures={},history=[])
 for slot,name,designation in [('president','Demo Student','President'),('secretary','Demo Secretary','Secretary'),('advisor','Demo Advisor','Club Advisor'),('sld','Demo SLD Officer','SLD Officer')]:
  if slot in ('president','secretary'):designation='Photography Society · '+designation
  signer=dict(slot=slot,name=name,designation=designation,department='Student Life Division' if slot=='sld' else 'Photography Society',email=slot+'@qiu.edu.my',signed_at='2026-10-09T02:00:00+00:00',signature=drawn_signature(),revision=3,digest='a'*64)
  r['signatures'][slot]=signer;r['history'].append(dict(action='submitted' if slot=='president' else 'approve',stage=slot,actor=signer['email'],name=name,timestamp=signer['signed_at'],revision=3,digest='a'*64,comment='Reviewed the submitted version.',signer=signer))
 return r

def run():
 out=ROOT/'.agency/qa';out.mkdir(parents=True,exist_ok=True);club=dict(name='Photography Society',category='Cultural',logo=drawn_signature())
 for kind in ('agm','weekly'):
  r=sample(kind)
  if kind=='agm':r['report_year']=2026
  data=exports.club_report_docx(r,club);(out/(kind+'-signed.docx')).write_bytes(data)
  with zipfile.ZipFile(io.BytesIO(data)) as package,zipfile.ZipFile(ROOT/'templates'/('agm-report.docx' if kind=='agm' else 'meeting-minutes.docx')) as original:
   xml=ET.fromstring(package.read('word/document.xml'));text=' '.join(xml.xpath('//w:t/text()',namespaces=exports.NS))
   assert all(label in text for label in ('Demo Student','Demo Secretary','Demo Advisor','Demo SLD Officer','Approval and verification log','Version integrity',r['submitted_digest'][:32]))
   assert len(xml.findall('.//'+exports.W+'drawing'))>=4
   for filename in original.namelist():
    if filename not in ('word/document.xml','word/_rels/document.xml.rels','[Content_Types].xml','word/header1.xml','word/_rels/header1.xml.rels'):assert package.read(filename)==original.read(filename),filename
   assert 'xxx' not in text.lower() and 'Angie' not in text
   data_tables=xml.xpath('//w:tbl',namespaces=exports.NS)[1:4] if kind=='agm' else xml.xpath('//w:tbl',namespaces=exports.NS)[:1]
   assert all(table.find(exports.W+'tr').find(exports.W+'trPr').find(exports.W+'tblHeader').get(exports.W+'val')=='1' for table in data_tables),'Data table headers repeat on continued pages'
   if kind=='agm':assert 'Attendance: Present' in text and 'POSITION' in text and 'Unavailable' in text and 'SESSION 2026' in text
  returned=copy.deepcopy(r);returned['status']='returned'
  with zipfile.ZipFile(io.BytesIO(exports.club_report_docx(returned,club))) as package:
   xml=ET.fromstring(package.read('word/document.xml'))
   embeds=[node.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed','') for node in xml.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')]
   assert not any(embed in {'rIdQiuSignature'+slot.title() for slot in ('president','secretary','advisor','sld')} for embed in embeds),'Returned report must exclude all four current signature images; its club logo remains'
  pdf=exports.club_report_pdf(r,club);assert pdf.startswith(b'%PDF');(out/(kind+'-signed.pdf')).write_bytes(pdf)
  import pdfplumber
  with pdfplumber.open(io.BytesIO(pdf)) as document:
   assert all(len(page.chars)>30 for page in document.pages),'No unintended blank body page'
   content='\n'.join(page.extract_text() or '' for page in document.pages);assert 'Club Logo' not in content
   assert all(name in content for name in ('Demo Student','Demo Secretary','Demo Advisor','Demo SLD Officer'))
   for i,page in enumerate(document.pages):
    page.to_image(resolution=90).save(str(out/(kind+'-signed-page-'+str(i+1)+'.png')))
   print(kind,'rendered pages',len(document.pages))
 r=sample('weekly');sports=dict(club,category='Sports');pdf=exports.club_report_pdf(r,sports);assert pdf.startswith(b'%PDF');(out/'weekly-sports-signed.pdf').write_bytes(pdf)
 import pdfplumber
 with pdfplumber.open(io.BytesIO(pdf)) as document:
  assert 'Approval and verification log' in '\n'.join(p.extract_text() or '' for p in document.pages)
  for i,page in enumerate(document.pages):page.to_image(resolution=90).save(str(out/('weekly-sports-page-'+str(i+1)+'.png')))
 print('PASS: AGM/minutes source sections and unchanged styles/media, four embedded version-bound signers, returned images excluded, professional audit rows and actual rendered PDFs.')
if __name__=='__main__':run()
