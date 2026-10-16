"""HTTP safe public projections and annual AGM constraints."""
import pathlib,sys,tempfile,threading
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
import server,auth,profiles
from test_registration import Client
from test_reports import fixture_club,report_fields

def run():
 with tempfile.TemporaryDirectory() as td,patch.object(auth,'now',return_value='2026-10-09T04:00:00+00:00'):
  srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);base='http://127.0.0.1:'+str(srv.server_port);srv.app=server.App(pathlib.Path(td)/'profiles.db',True,base)
  club=fixture_club();srv.app.put('club',club);srv.app.put('club',dict(fixture_club('secret'),status='draft'))
  threading.Thread(target=srv.serve_forever,daemon=True).start()
  try:
   visitor,president,sld=[Client(base,p) for p in ('visitor','student','sld')]
   clubs=visitor.call('/api/public-clubs')['clubs'];assert len(clubs)==1 and clubs[0]['id']=='club'
   public=visitor.call('/api/public-clubs/club')['club'];assert public['hierarchy'][0]['photo'].endswith('student.svg')
   assert not {'email','university_id','advisor_email','committee','history','signatures'}&set(public)
   assert all(not {'email','university_id'}&set(row) for row in public['hierarchy'])
   visitor.call('/api/public-clubs/secret',status=404)
   own=president.call('/api/profile')['profile'];assert own['email']=='demo.student@qiu.edu.my' and own['university_id']
   identity=visitor.call('/api/public-students/'+own['profile_id'])['profile'];assert identity['name']=='Demo Student' and identity['clubs'][0]['positions']==['President']
   assert not {'email','university_id','directory_title','history'}&set(identity)
   visitor.call('/api/agm-tracker?year=2026',status=403)
   assert sld.call('/api/agm-tracker?year=2026')['summary']['missing']==1
   fields=report_fields(type='agm',report_year=2026)
   report=president.call('/api/club-reports',{'report':fields})['report'];assert report['report_year']==2026
   assert report['signer_profile']['designation']==club['name']+' · President'
   president.call('/api/club-reports',{'report':fields},status=409)
   assert sld.call('/api/agm-tracker?year=2026')['summary']['draft']==1
   legacy=dict(report);legacy.pop('report_year');srv.app.put('club_report',legacy)
   historic={'id':report['id']+'-legacy','snapshot':{'type':'agm','date':'2026-10-08'},'digest':'immutable'};srv.app.put('club_report_version',historic)
   projected=next(r for r in president.call('/api/bootstrap')['club_reports'] if r['id']==report['id']);assert projected['report_year']==2026
   assert 'report_year' not in srv.app.get('club_report',report['id']) and srv.app.get('club_report_version',historic['id'])==historic

   second=president.call('/api/club-reports',{'report':dict(fields,report_year=2025)})['report'];assert second['report_year']==2025
   assert sld.call('/api/agm-tracker?year=2027')['summary']['missing']==1
   prior_version={'id':report['id']+'-r0','snapshot':{'old_committee':club['committee'],'signatures':{'president':{'name':'Historic signer'}}},'digest':'historical'};srv.app.put('club_report_version',prior_version)
   changed=dict(club,committee=[dict(row,position='Vice President' if row['position']=='President' else 'President' if row['position']=='Vice President' else row['position']) for row in club['committee']]);srv.app.put('club',changed)
   stale=president.call('/api/club-reports/'+report['id'])['report'];assert stale['can_rebase'] and not stale['can_sign']
   refreshed=president.call('/api/club-reports/'+report['id']+'/rebase',{'revision':report['revision']})['report'];assert refreshed['old_committee']==changed['committee'] and not refreshed['can_rebase']
   president.call('/api/club-reports/'+report['id']+'/rebase',{'revision':report['revision']},status=409)
   assert srv.app.get('club_report_version',prior_version['id'])==prior_version
   visitor.call('/api/club-reports/'+report['id']+'/rebase',{'revision':refreshed['revision']},status=403)
   locked=dict(refreshed,status='pending_secretary');srv.app.put('club_report',locked)
   president.call('/api/club-reports/'+report['id']+'/rebase',{'revision':locked['revision']},status=403)
   srv.app.put('club_report',refreshed);srv.app.put('club',club)
   president.call('/api/club-reports',{'report':dict(fields,report_year='2024')},status=400)
   weekly=president.call('/api/club-reports',{'report':report_fields(report_year=2026)})['report'];assert weekly['report_year'] is None
   srv.app.put('club_report',dict(weekly,status='approved',minutes='PRIVATE MINUTES',history=[{'signature':'PRIVATE'}]))
   summary=visitor.call('/api/public-clubs/club')['club']['weekly_summaries'];assert len(summary)==1 and 'minutes' not in summary[0] and 'history' not in summary[0]
   for rid,status,day,clock,venue in [('planned','approved','2026-10-10','10:00','Meeting Hall'),('duplicate','approved','2026-10-10','10:00:00','meeting hall'),('old','approved','2026-10-08','10:00','Meeting Hall'),('unsigned','draft','2026-10-11','10:00','Private Hall'),('invalid','approved','2026-10-12','99:00','Hall')]:
    srv.app.put('club_report',dict(weekly,id=rid,status=status,next_meeting=dict(date=day,time=clock,venue=venue),minutes='PRIVATE'))
   planned=visitor.call('/api/public-clubs/club')['club']['upcoming_weekly_activities'];assert len(planned)==1 and planned[0]['date']=='2026-10-10' and planned[0]['time']=='10:00' and planned[0]['occurrence']=='scheduled'
   assert set(planned[0])=={'report_id','title','date','time','venue','occurrence'} and planned[0]['report_id']=='duplicate'
   visitor.call('/api/weekly-tracker?week_start=2026-10-08',status=403)
   tracker=sld.call('/api/weekly-tracker?week_start=2026-10-08');assert tracker['week_start']=='2026-10-05' and tracker['week_end']=='2026-10-11'
   assert tracker['clubs'][0]['status']=='draft' and tracker['clubs'][0]['report_count']==6 and tracker['clubs'][0]['approved_count']==5
   assert sld.call('/api/weekly-tracker?week_start=2026-11-01')['summary']['missing']==1
   sld.call('/api/weekly-tracker?week_start=2026-13-01',status=400)
   srv.app.put('club_report',dict(weekly,id='pending-weekly',status='pending_sld'))
   tracker=sld.call('/api/weekly-tracker?week_start=2026-10-05');assert tracker['clubs'][0]['status']=='pending_sld' and tracker['clubs'][0]['report_id']=='pending-weekly' and tracker['summary']['pending']==1
   person=auth.preview_user('student');person['photo']='https://lh3.googleusercontent.com/refreshed';srv.app.put('user',person)
   assert visitor.call('/api/public-students/'+own['profile_id'])['profile']['photo']==person['photo']
   assert srv.app.bootstrap({'user':auth.preview_user('sld'),'csrf':'test'})['api_version']=='1.7'
   print('PASS safe approved clubs/self/public profiles, trusted refreshed photos, annual AGM constraints/year tracker, contextual signer identity.')
  finally:srv.shutdown();srv.server_close();srv.app.db.close()
if __name__=='__main__':run()
