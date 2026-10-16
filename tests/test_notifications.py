"""Real HTTP notification workflows, recipient isolation and durable read state."""
import copy
import pathlib
import sys
import tempfile
import threading
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
import auth
import server
from proposal_fixture import complete_proposal,drawn_signature
from test_registration import Client


def run():
    with tempfile.TemporaryDirectory() as directory,patch.object(auth,'now',return_value='2026-10-08T02:00:00+00:00'):
        path=pathlib.Path(directory)/'notifications.sqlite3'
        srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        base='http://127.0.0.1:'+str(srv.server_port)
        srv.app=server.App(path,True,base)
        club=dict(id='club',name='Notification Society',status='approved',advisor_email='demo.advisor@qiu.edu.my',
                  owner_email='demo.student@qiu.edu.my',revision=1,history=[],created_at=auth.now(),updated_at=auth.now(),
                  committee=[dict(position='President',email='demo.student@qiu.edu.my',name='Demo Student'),
                             dict(position='Vice President',email='demo.vice@qiu.edu.my',name='Demo Vice President')])
        srv.app.put('club',club)
        threading.Thread(target=srv.serve_forever,daemon=True).start()
        try:
            student=Client(base,'student');vice=Client(base,'vice');event=Client(base,'treasurer')
            advisor=Client(base,'advisor');sld=Client(base,'sld');unrelated=Client(base,'secretary')
            assert advisor.call('/api/notifications')['total']==0
            sld.call('/api/registration-grants',dict(club_name='Another Society',semester='October 2026',
                     president_email='demo.student@qiu.edu.my',advisor_email='demo.advisor@qiu.edu.my'))
            assert student.call('/api/notifications')['notifications'][0]['record_type']=='grant'
            assert advisor.call('/api/notifications')['total']==1
            assert sld.call('/api/notifications')['total']==0
            p=student.call('/api/proposals',dict(proposal=complete_proposal(committee=[
                dict(email='demo.treasurer@qiu.edu.my',role='Coordinator',responsibility='Coordinate the event')])) )['proposal']
            pid=p['id']
            initial=event.call('/api/notifications');assert initial['total']==1
            assert initial['notifications'][0]['record_type']=='proposal'
            assert 'recipient' not in initial['notifications'][0]
            p=student.call('/api/proposals',dict(proposal=p))['proposal']
            assert event.call('/api/notifications')['total']==1,'Autosave must not notify again'
            student.call('/api/proposals/'+pid+'/submit',dict(revision=p['revision'],signature=drawn_signature()))
            assert vice.call('/api/notifications')['total']==1
            assert event.call('/api/notifications')['total']==2
            assert advisor.call('/api/notifications')['total']==2
            assert sld.call('/api/notifications')['total']==0,'SLD does not need advisor-stage alerts'
            p=next(p for p in advisor.call('/api/bootstrap')['proposals'] if p['id']==pid)
            advisor.call('/api/proposals/'+pid+'/review',dict(revision=p['revision'],action='approve',confirm_submission=True,name='Demo Advisor',signature=drawn_signature(),comment='Reviewed'))
            alert=sld.call('/api/notifications')['notifications'][0]
            assert alert['record_id']==pid and 'SLD review' in alert['title']
            assert unrelated.call('/api/notifications')['total']==0
            unrelated.call('/api/notifications/'+alert['id']+'/read',{},404)
            result=sld.call('/api/notifications/'+alert['id']+'/read',{'read_at':'forged'})
            assert result['notification']['read_at']==auth.now() and result['unread_count']==0
            assert sld.call('/api/notifications/'+alert['id']+'/read',{})['unread_count']==0
            restarted=server.App(path,True,base)
            try:
                import notifications
                assert notifications.list_for(restarted,auth.preview_user('sld'))['unread_count']==0
                assert notifications.list_for(restarted,auth.preview_user('sld'))['total']==1
            finally:restarted.db.close()
            # A previously assigned event participant loses historical alert access immediately.
            original=srv.app.get('proposal',pid);original['committee']=[];srv.app.put('proposal',original)
            assert event.call('/api/notifications')['total']==0
            event.call('/api/notifications/'+initial['notifications'][0]['id']+'/read',{},404)
            assert advisor.call('/api/notifications?offset=0&limit=1')['limit']==1
            advisor.call('/api/notifications?offset=-1',status=400)
            print('PASS: grant/assignment/review notifications, linked-member updates, SLD actionable queue, no autosave spam, read persistence, server dates and revoked-recipient isolation.')
        finally:
            srv.shutdown();srv.server_close();srv.app.db.close()


if __name__=='__main__':run()
