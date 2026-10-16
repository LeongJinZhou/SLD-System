"""Independent lifecycle boundaries; exporter stubs avoid concurrent PDF renders."""
import base64,io,json,pathlib,sys,tempfile,zipfile
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from PIL import Image
import auth,server,evidence,exports,finance
from test_reports import fixture_club
from proposal_fixture import complete_proposal,drawn_signature

def photo(colour):
    out=io.BytesIO();Image.new('RGB',(8,8),colour).save(out,format='PNG')
    return 'data:image/png;base64,'+base64.b64encode(out.getvalue()).decode()

def reject(fn,status):
    try:fn()
    except (server.APIError,finance.FinanceError) as error:assert error.status==status,(error.status,status,str(error))
    else:raise AssertionError('Expected rejection '+str(status))

def run():
    with tempfile.TemporaryDirectory() as td,patch.object(auth,'now',return_value='2026-10-09T04:00:00+00:00') as clock:
        app=server.App(pathlib.Path(td)/'review.db',True,'http://127.0.0.1:8765')
        try:
            club=fixture_club();app.put('club',club)
            event=complete_proposal(id='event',club_id='club',title='../ Private event',status='approved',date='2026-10-08',end_date='2026-10-08',start_time='10:00',end_time='11:00',committee=[])
            app.put('proposal',event)
            organiser=auth.preview_user('student');visitor=auth.preview_user('visitor');sld=auth.preview_user('sld')
            reject(lambda:evidence.view(app,visitor,'proposal','event'),403)
            first=evidence.upload(app,organiser,dict(target_type='proposal',target_id='event',name='../../one.png',data_url=photo('red')))
            reject(lambda:evidence.upload(app,organiser,dict(target_type='proposal',target_id='event',name='duplicate.png',data_url=photo('red'))),409)
            assert first['count']==1 and 'content_base64' not in first['photos'][0]
            report=evidence.save_completion(app,organiser,{'report':dict(proposal_id='event',summary='Completed outcomes',creation_key='review')})['report']
            submit=lambda:evidence.transition_completion(app,organiser,report['id'],'submit',dict(revision=report['revision'],confirm_submission=True))
            reject(submit,400)
            uploaded=evidence.upload(app,organiser,dict(target_type='proposal',target_id='event',completion_revision=report['revision'],name='two.png',data_url=photo('blue')))
            report=app.get('event_completion',report['id']);assert uploaded['count']==2
            reject(lambda:evidence.upload(app,organiser,dict(target_type='proposal',target_id='event',completion_revision=report['revision']-1,name='stale.png',data_url=photo('green'))),409)
            report=submit()['report']
            reject(lambda:evidence.delete_photo(app,organiser,first['photo']['id'],dict(completion_revision=report['revision'])),403)
            # An empty image must never satisfy the SLD drawn-signature requirement.
            reject(lambda:evidence.transition_completion(app,sld,report['id'],'review',dict(revision=report['revision'],action='approve',signature='')),400)
            report=evidence.transition_completion(app,sld,report['id'],'review',dict(revision=report['revision'],action='approve',signature=drawn_signature(),name='FORGED',signed_at='1900-01-01'))['report']
            assert report['signature']['name']==sld['name'] and report['signature']['signed_at']==auth.now()
            reject(lambda:evidence.photo_zip(app,organiser,'proposal','event'),403)
            raw,_,_=evidence.photo_zip(app,sld,'proposal','event')
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                assert all(not pathlib.PurePosixPath(name).is_absolute() and '..' not in pathlib.PurePosixPath(name).parts for name in z.namelist())
                assert len(z.namelist())==len(set(z.namelist()))
            # Original proposal-version records carry identity in snapshot, not a top-level proposal_id.
            historic=dict(id='event-r2',snapshot=dict(event,revision=2),digest='frozen-proposal-digest')
            app.put('proposal_version',historic)
            app.put('club_report',dict(id='agm',club_id='club',type='agm',title='Annual',date='2026-10-08',report_year=2026,status='approved',handover_applied_at=auth.now()))
            reject(lambda:evidence.annual_archive(app,visitor,'club',2026),403)
            with patch.object(exports,'club_pdf',return_value=b'PDF'),patch.object(exports,'club_report_pdf',return_value=b'PDF'),patch.object(exports,'export_proposal',return_value=(b'PDF','application/pdf','p.pdf')),patch.object(evidence,'completion_pdf',return_value=b'PDF'):
                raw,_,_=evidence.annual_archive(app,sld,'club',2026)
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                names=z.namelist();version_path=next((name for name in names if name.endswith('/Audit/proposal_version.json')),None)
                assert version_path,'Annual archive omitted immutable proposal versions'
                assert json.loads(z.read(version_path))==[historic]
            incoming=dict(email='incoming@qiu.edu.my',name='Incoming President',role='student')
            incoming_roster=[dict(club['committee'][0],email=incoming['email'],name=incoming['name'])]+club['committee'][1:]
            app.put('club',dict(club,committee_handover=dict(starts_at=auth.now(),ends_at='2026-10-16T04:00:00+00:00',outgoing=club['committee'],incoming=incoming_roster)))
            overlap=app.get('club','club')
            assert app.assigned_roles(overlap,incoming)==['Pending President']
            assert app.preparer_profile(overlap,incoming) is None
            assert evidence.view(app,incoming,'proposal','event')['count']==2
            frozen=app.get('proposal_version','event-r2')
            clock.return_value='2026-10-16T04:00:00+00:00'
            # A direct evidence call at the boundary must revoke access without a bootstrap first.
            reject(lambda:evidence.view(app,organiser,'proposal','event'),403)
            assert evidence.view(app,incoming,'proposal','event')['count']==2
            assert app.preparer_profile(app.get('club','club'),incoming)['designation'].endswith('President')
            assert app.get('proposal_version','event-r2')==frozen
            print('PASS independent photo scope/count/revisions, signed completion, safe ZIP, annual versions and direct exact-time evidence access revocation.')
        finally:app.db.close()

if __name__=='__main__':run()
