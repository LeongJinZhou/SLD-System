"""Original-cell integrity checks across signed, returned and mismatched versions."""
import sys,pathlib,io,base64,copy,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
import exports,auth
from proposal_fixture import complete_proposal
from PIL import Image,ImageDraw
from lxml import etree as ET

def run():
 image=Image.new('RGBA',(600,160),'white');ImageDraw.Draw(image).line([(15,100),(50,20),(100,120),(200,40),(350,90),(550,20)],fill='navy',width=5)
 stream=io.BytesIO();image.save(stream,format='PNG');signature='data:image/png;base64,'+base64.b64encode(stream.getvalue()).decode()
 proposal=complete_proposal(status='approved',submitted_revision=3,submitted_digest='verified-digest',submitted_at='2026-10-08T02:00:00+00:00',history=[])
 proposal['signatures']={slot:dict(slot=slot,name=slot.title()+' Person',designation=slot.title(),department='Department '+slot,email=slot+'@qiu.edu.my',signature=signature,signed_at='2026-10-08T02:00:00+00:00',revision=3,digest='verified-digest') for slot in ['preparer','advisor','sld']}
 club=dict(name='Test Society',advisor_profile=dict(name='Assigned Advisor',designation='Club Advisor',department='Unavailable'))
 def read(record):
  data=exports.proposal_docx(record,club,auth.preview_user('student'))
  with zipfile.ZipFile(io.BytesIO(data)) as z,zipfile.ZipFile(exports.TEMPLATE) as original:
   xml=ET.fromstring(z.read('word/document.xml'));table=xml.xpath('//w:tbl',namespaces=exports.NS)[5]
   for name in original.namelist():
    if name not in ('word/document.xml','word/_rels/document.xml.rels','[Content_Types].xml'):assert z.read(name)==original.read(name),name
   cells=[exports._cells(exports._rows(table)[r])[c] for r,c in [(0,0),(0,1),(1,0)]]
   printed=[exports._cells(exports._rows(table)[r])[c] for r,c in [(1,1),(2,0),(2,1),(3,0),(3,1)]]
   source=ET.fromstring(original.read('word/document.xml')).xpath('//w:tbl',namespaces=exports.NS)[5]
   for cell,(r,c) in zip(printed,[(1,1),(2,0),(2,1),(3,0),(3,1)]):assert ET.tostring(cell)==ET.tostring(exports._cells(exports._rows(source)[r])[c])
   ids=[n.get('id') for n in xml.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr')];assert len(ids)==len(set(ids))
   return cells
 cells=read(proposal)
 for cell,slot in zip(cells,['preparer','advisor','sld']):
  assert len(cell.findall('.//'+exports.W+'drawing'))==1
  text=' '.join(cell.itertext());assert slot.title()+' Person' in text and '08/10/2026' in text
 pending=copy.deepcopy(proposal);pending['status']='pending_sld';pending['signatures'].pop('sld');cells=read(pending)
 assert not cells[2].findall('.//'+exports.W+'drawing') and 'Advisor Person' not in ''.join(cells[2].itertext())
 mismatch=copy.deepcopy(proposal);mismatch['signatures']['advisor']['digest']='old';cells=read(mismatch);assert not cells[1].findall('.//'+exports.W+'drawing') and 'Assigned Advisor' in ''.join(cells[1].itertext())
 for status in ('draft','returned'):
  unsigned=copy.deepcopy(proposal);unsigned['status']=status;cells=read(unsigned)
  assert all(not cell.findall('.//'+exports.W+'drawing') for cell in cells)
  assert all('08/10/2026' not in ''.join(cell.itertext()) for cell in cells)
 print('PASS: three original signature cells, pending SLD no crossover, invalid-version exclusion, unsigned dates blank, unique image IDs and unrelated package/cell preservation.')
if __name__=='__main__':run()
