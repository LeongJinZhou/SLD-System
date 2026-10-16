"""Isolated checks of real HTTP workflows, authorization and template preservation."""
import base64, io, json, pathlib, sys, tempfile, threading, urllib.request, urllib.error, http.cookiejar, zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import server,auth,exports
from PIL import Image

def run():
    with tempfile.TemporaryDirectory() as td:
        srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        base='http://127.0.0.1:'+str(srv.server_port)
        srv.app=server.App(pathlib.Path(td)/'test.sqlite3',True,base)
        threading.Thread(target=srv.serve_forever,daemon=True).start()
        opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        csrf=''
        def request(path,data=None,expect=200,raw=False):
            headers={}
            if data is not None:headers={'Origin':base,'X-CSRF-Token':csrf,'Content-Type':'application/json'}
            req=urllib.request.Request(base+path,json.dumps(data).encode() if data is not None else None,headers)
            try:
                r=opener.open(req);status=r.status;body=r.read()
            except urllib.error.HTTPError as r:status=r.code;body=r.read()
            assert status==expect,(path,status,body[:200])
            return body if raw else json.loads(body)
        def login(persona):
            nonlocal csrf
            csrf=request('/api/bootstrap')['csrf'];boot=request('/api/preview/login',{'persona':persona});csrf=boot['csrf'];return boot
        try:
            initial=request('/api/bootstrap');assert initial['user'] is None;csrf=initial['csrf']
            assert b'--color-ink' in request('/tokens.css',raw=True)
            assert b'Student Life' in request('/',raw=True)
            request('/api/clubs',{'club':{}},401) # anonymous prohibited
            boot=login('student');assert boot['user']['directory_status']=='preview_fixture'
            image=Image.new('RGB',(20,20),'navy');buffer=io.BytesIO();image.save(buffer,format='PNG')
            png='data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode()
            club={'name':'Chinese Society 测试','category':'Cultural','semester':'October 2026','bio':'A club for cultural exchange.','logo':png,'advisor_email':'demo.advisor@qiu.edu.my','committee':[]}
            login('sld')
            grant=request('/api/registration-grants',{'club_name':club['name'],'semester':club['semester'],'president_email':'demo.student@qiu.edu.my','advisor_email':club['advisor_email']})['registration_grant']
            login('student');club['registration_grant_id']=grant['id']
            president=auth.PREVIEW_PEOPLE[0]
            club['committee']=[{'position':'President','name':president['name'],'email':president['email'],'university_id':president['university_id']}]
            c=request('/api/clubs',{'club':club})['club'];cid=c['id']
            club['revision']=c['revision']
            request('/api/clubs/'+cid+'/submit',{'revision':c['revision']},400)
            people=auth.PREVIEW_PEOPLE;club['committee']=[{'position':role,'name':person['name'],'email':person['email'],'university_id':person['university_id']} for role,person in zip(['President','Vice President','Secretary','Treasurer'],[people[0],people[3],people[4],people[5]])]
            club['id']=cid
            bad=dict(club,advisor_email='outsider@example.com');request('/api/clubs',{'club':bad},400)
            saved=request('/api/clubs',{'club':club})['club'];request('/api/clubs',{'club':club},409);club=saved
            club=request('/api/clubs/'+cid+'/submit',{'revision':club['revision']})['club'];assert club['status']=='pending_advisor'
            request('/api/clubs/'+cid+'/review',{'action':'approve','confirm_submission':True,'name':'Forged','signature':png,'revision':club['revision']},403)
            login('advisor');assert len(request('/api/bootstrap')['clubs'])==1
            request('/api/clubs/'+cid+'/review',{'action':'return','comment':'','revision':club['revision']},400)
            assert request('/api/clubs/'+cid+'/review',{'action':'return','comment':'Clarify biography','revision':club['revision']})['club']['status']=='returned'
            boot=login('student');club=request('/api/clubs',{'club':boot['clubs'][0]})['club'];club=request('/api/clubs/'+cid+'/submit',{'revision':club['revision']})['club']
            login('advisor');club=request('/api/clubs/'+cid+'/review',{'action':'approve','confirm_submission':True,'name':'Demo Advisor','signature':png,'revision':club['revision']})['club']
            request('/api/clubs/'+cid+'/review',{'action':'approve','confirm_submission':True,'name':'Demo Advisor','signature':png,'revision':club['revision']},403)
            login('sld');club=request('/api/clubs/'+cid+'/open-review',{'revision':club['revision']})['club'];club=request('/api/clubs/'+cid+'/review',{'action':'approve','confirm_submission':True,'name':'Demo SLD','signature':png,'revision':club['revision']})['club'];assert club['status']=='approved'
            request('/api/clubs',{'club':club},409)
            proposal={'club_id':cid,'title':'Cultural exchange 文化交流','date':'2026-11-20','end_date':'2026-11-20','start_time':'09:00','end_time':'12:00','venue':'QIU Hall','duration':'3 hours','summary':'A student cultural exchange.','introduction':'Learn together and share culture.','objectives':'Build connections.','target_count':50,'eligibility':'QIU students','mode':'Physical','nature':['Social Events/Festivals'],'sdgs':['4','17'],'funding_source':['Club Fund'],'activities':[{'name':'Conversation','description':'Small group discussions'}],'itinerary':[{'start':'09:00','end':'12:00','agenda':'Exchange'}],'committee':[{'name':'Demo Student','role':'Host','responsibility':'Coordinate'}],'ict':'Projector','logistics':'Seats for 50','transport':'Not required','conclusion':'A shared learning opportunity.','revenue':[{'description':'=malicious spreadsheet formula','price':10,'quantity':50}],'expenses':[{'description':'Materials','price':2,'quantity':50}]}
            request('/api/proposals',{'proposal':dict(proposal,revenue='wrong shape')},400)
            request('/api/proposals',{'proposal':dict(proposal,expenses=[{'price':-1,'quantity':1}])},400)
            login('student');p=request('/api/proposals',{'proposal':proposal})['proposal'];pid=p['id']
            p=request('/api/proposals',{'proposal':p})['proposal'];request('/api/proposals',{'proposal':dict(p,revision=p['revision']-1)},409)
            login('sld')
            docx=request('/api/proposals/'+pid+'/export?format=docx',raw=True)
            with zipfile.ZipFile(io.BytesIO(docx)) as filled,zipfile.ZipFile(exports.TEMPLATE) as original:
                assert set(filled.namelist())==set(original.namelist())
                assert all(filled.read(n)==original.read(n) for n in original.namelist() if n!='word/document.xml')
                xml=filled.read('word/document.xml').decode();assert '文化交流' in xml and 'Chinese Society' in xml and '500.00' in xml and '400.00' in xml
                from lxml import etree
                namespaces={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                prepared=etree.fromstring(filled.read('word/document.xml')).xpath('//w:tbl',namespaces=namespaces)[5].xpath('./w:tr/w:tc',namespaces=namespaces)[0]
                prepared_text=' '.join(prepared.xpath('.//w:t/text()',namespaces=namespaces))
                assert 'Demo Student' not in prepared_text and '08/10/2026' not in prepared_text
                assert 'Jingle Toss' not in xml and 'Ticket Selling - Early Bird' not in xml
            xlsx=request('/api/proposals/'+pid+'/export?format=xlsx',raw=True)
            from openpyxl import load_workbook
            book=load_workbook(io.BytesIO(xlsx));assert book.active['B6'].data_type=='s'
            request('/api/proposals/'+pid+'/export?format=exe',expect=400)
            root=pathlib.Path(td);(root/'proposal.docx').write_bytes(docx)
            if exports.pdf_available():
                pdf=request('/api/proposals/'+pid+'/export?format=pdf',raw=True);assert pdf.startswith(b'%PDF')
            stranger=dict(auth.preview_user('student'),email='unrelated@qiu.edu.my')
            assert not srv.app.visible(srv.app.get('club',cid),stranger)
            assert not srv.app.editable(srv.app.get('club',cid),auth.preview_user('advisor'))
            persisted=server.App(root/'test.sqlite3',True,base);assert persisted.get('club',cid)['status']=='approved';persisted.db.close()
            signed=srv.app.get('club',cid);assert signed['history'][-1]['digest']==signed['submitted_digest']
            snapshot=srv.app.get('club_version',cid+'-r'+str(signed['submitted_revision']));assert snapshot['digest']==signed['submitted_digest']
            srv.app.preview=False;request('/api/preview/login',{'persona':'sld'},404)
            print('PASS: HTTP club draft/validation/return/resubmit/advisor/SLD, immutable approval, permissions, persistence, proposal validation, original package preservation, Unicode export, spreadsheet injection, preview isolation.')
        finally:srv.shutdown();srv.server_close();srv.app.db.close()

if __name__=='__main__':run()
