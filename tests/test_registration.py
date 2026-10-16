"""HTTP regression checks for SLD-issued registrations and first-open review locks."""
import base64, copy, http.cookiejar, io, json, pathlib, sys, tempfile, threading
import urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import server,auth
from PIL import Image

class Client:
    def __init__(self,base,persona):
        self.base=base;self.csrf=''
        self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.csrf=self.call('/api/bootstrap')['csrf']
        self.csrf=self.call('/api/preview/login',{'persona':persona})['csrf']
    def call(self,path,body=None,status=200):
        headers={'Origin':self.base,'X-CSRF-Token':self.csrf,'Content-Type':'application/json'} if body is not None else {}
        request=urllib.request.Request(self.base+path,json.dumps(body).encode() if body is not None else None,headers)
        try:response=self.opener.open(request)
        except urllib.error.HTTPError as error:response=error
        data=json.loads(response.read());assert response.code in (status if isinstance(status,tuple) else (status,)),(path,response.code,status,data)
        return data

def run():
    with tempfile.TemporaryDirectory() as td:
        srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        base='http://127.0.0.1:'+str(srv.server_port)
        srv.app=server.App(pathlib.Path(td)/'test.sqlite3',True,base)
        threading.Thread(target=srv.serve_forever,daemon=True).start()
        try:
            student=Client(base,'student');advisor=Client(base,'advisor');sld=Client(base,'sld')
            grant_fields={'club_name':'Assigned Society','semester':'October 2026','president_email':'demo.student@qiu.edu.my','advisor_email':'demo.advisor@qiu.edu.my'}
            student.call('/api/registration-grants',grant_fields,403)
            advisor.call('/api/registration-grants',grant_fields,403)
            student.call('/api/clubs',{'club':{}},403)
            sld.call('/api/registration-grants',dict(grant_fields,president_email='person@example.com'),400)
            grant=sld.call('/api/registration-grants',grant_fields)['registration_grant']
            sld.call('/api/registration-grants',grant_fields,409)
            assert student.call('/api/bootstrap')['registration_grants'][0]['id']==grant['id']
            pic=Image.new('RGB',(16,16),'navy');buf=io.BytesIO();pic.save(buf,format='PNG')
            signature='data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()
            people=auth.PREVIEW_PEOPLE
            club={'registration_grant_id':grant['id'],'name':grant_fields['club_name'],'semester':grant_fields['semester'],
                  'category':'Cultural','bio':'Draft biography','logo':signature,'advisor_email':grant_fields['advisor_email'],
                  'committee':[{'position':role,'name':p['name'],'email':p['email'],'university_id':p['university_id']}
                               for role,p in zip(['President','Vice President','Secretary','Treasurer'],[people[0],people[3],people[4],people[5]])]}
            advisor.call('/api/clubs',{'club':club},403)
            second_session=Client(base,'student')
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=list(pool.map(lambda client:client.call('/api/clubs',{'club':club},(200,409)),[student,second_session]))
            assert sum('club' in result for result in results)==1
            c=next(result['club'] for result in results if 'club' in result);cid=c['id'];path='/api/clubs/'+cid
            student.call('/api/clubs',{'club':dict(c,name='Unauthorized rename')},403)
            changed=copy.deepcopy(c);changed['committee'][0]['email']='demo.vice@qiu.edu.my'
            student.call('/api/clubs',{'club':changed},403)
            student.call('/api/clubs',{'club':club},409)
            assert sld.call('/api/bootstrap')['registration_grants'][0]['status']=='used'
            assert advisor.call('/api/bootstrap')['clubs'][0]['bio']=='Draft biography'
            assert not sld.call('/api/bootstrap')['clubs'][0].get('sld_review_started_at')
            original_revision=c['revision']
            c=student.call('/api/clubs',{'club':dict(c,bio='Autosaved progress')})['club']
            student.call('/api/clubs',{'club':dict(c,revision=original_revision)},409)
            assert advisor.call('/api/bootstrap')['clubs'][0]['bio']=='Autosaved progress'
            c=student.call(path+'/submit',{'revision':c['revision']})['club']
            assert c['status']=='pending_advisor'
            signed=advisor.call(path+'/review',{'action':'approve','confirm_submission':True,'name':'Demo Advisor','signature':signature,'revision':c['revision']})['club']
            assert signed['status']=='pending_sld'
            # A committee edit before SLD opens invalidates the previous signed version.
            edited=student.call('/api/clubs',{'club':dict(signed,bio='Updated before SLD opened')})['club']
            assert edited['status']=='pending_advisor'
            advisor.call(path+'/review',{'action':'approve','confirm_submission':True,'name':'Demo Advisor','signature':signature,'revision':signed['revision']},409)
            c=advisor.call(path+'/review',{'action':'approve','confirm_submission':True,'name':'Demo Advisor','signature':signature,'revision':edited['revision']})['club']
            student.call(path+'/open-review',{'revision':c['revision']},403)
            locked=sld.call(path+'/open-review',{'revision':c['revision']})['club']
            assert locked['status']=='reviewing_sld' and locked['sld_review_started_at']
            again=sld.call(path+'/open-review',{'revision':locked['revision']})['club']
            assert again['revision']==locked['revision']
            student.call('/api/clubs',{'club':dict(locked,bio='Should not save',sld_review_started_at=None)},409)
            returned=sld.call(path+'/review',{'action':'return','comment':'Clarify the biography','revision':locked['revision']})['club']
            assert returned['status']=='returned' and not returned.get('sld_review_started_at')
            c=student.call('/api/clubs',{'club':dict(returned,bio='Corrected biography')})['club']
            c=student.call(path+'/submit',{'revision':c['revision']})['club']
            # First SLD open also locks a submission still awaiting advisor acknowledgment.
            c=sld.call(path+'/open-review',{'revision':c['revision']})['club'];assert c['status']=='pending_advisor' and c['sld_review_started_at']
            student.call('/api/clubs',{'club':c},409)
            sld.call(path+'/review',{'action':'approve','confirm_submission':True,'name':'Demo SLD','signature':signature,'revision':c['revision']},403)
            c=sld.call(path+'/review',{'action':'return','comment':'Clarify before advisor signs','revision':c['revision']})['club']
            assert c['status']=='returned' and not c.get('sld_review_started_at')
            c=student.call(path+'/submit',{'revision':c['revision']})['club']
            c=sld.call(path+'/open-review',{'revision':c['revision']})['club']
            c=advisor.call(path+'/review',{'action':'approve','confirm_submission':True,'name':'Demo Advisor','signature':signature,'revision':c['revision']})['club']
            assert c['status']=='reviewing_sld'
            c=sld.call(path+'/review',{'action':'approve','confirm_submission':True,'name':'Demo SLD','signature':signature,'revision':c['revision']})['club']
            assert c['status']=='approved'
            student.call('/api/clubs',{'club':c},409)
            final=sld.call('/api/bootstrap')
            assert final['dashboard'] and final['clubs'][0]['progress']['percent']==100
            assert not final['user'].get('programme')
            persisted=server.App(pathlib.Path(td)/'test.sqlite3',True,base)
            assert persisted.get('club',cid)['status']=='approved' and persisted.get('registration_grant',grant['id'])['status']=='used'
            persisted.db.close()
            print('PASS: SLD grant authorization/one-time creation, shared progress, pending edits/re-signing, stale revisions, first-open lock, return/unlock, approval, dashboard and persistence.')
        finally:srv.shutdown();srv.server_close();srv.app.db.close()

if __name__=='__main__':run()
