"""Durable recipient-specific workflow notifications, rechecked against current assignments."""
import hashlib
import os
import auth


def assigned(club,email):
    return email==club.get('advisor_email') or any(p.get('email')==email for p in club.get('committee',[]))


def permitted(app,user,n):
    if not user or n.get('recipient')!=user['email']:
        return False
    try:
        if n['record_type']=='grant':
            grant=app.get('registration_grant',n['record_id'])
            return user['role']=='sld' or user['email'] in (grant['president_email'],grant['advisor_email'])
        club=app.get('club',n['club_id'])
        if user['role']=='sld' or assigned(club,user['email']):
            return True
        if n['record_type'] in ('proposal','finance_report','event_completion'):
            proposal_id=n['record_id'] if n['record_type']=='proposal' else n.get('proposal_id')
            if not proposal_id:
                proposal_id=app.get('finance_report',n['record_id'])['proposal_id']
            return bool(app.event_roles(app.get('proposal',proposal_id),user))
    except Exception as error:
        from server import APIError
        if isinstance(error,APIError) and error.status==404:
            return False
        raise
    return False


def list_for(app,user,offset=0,limit=25):
    rows=[n for n in app.all('notification') if permitted(app,user,n)]
    rows.sort(key=lambda n:(n['created_at'],n['id']),reverse=True)
    safe=[{k:v for k,v in n.items() if k!='recipient'} for n in rows[offset:offset+limit]]
    return dict(notifications=safe,total=len(rows),unread_count=sum(not n.get('read_at') for n in rows),offset=offset,limit=limit)


def mark_read(app,user,record_id):
    from server import APIError
    n=app.get('notification',record_id)
    if not permitted(app,user,n):
        raise APIError('Notification not found.',404)
    if not n.get('read_at'):
        n['read_at']=auth.now();app.put('notification',n)
    return dict(notification={k:v for k,v in n.items() if k!='recipient'},unread_count=list_for(app,user,0,1)['unread_count'])


def emit(app,user,entry,log_id):
    action=entry['action'];rid=entry.get('record_id','');club=None;proposal=None;record_type='club';record_id=rid
    meaningful={'club_registration_authorized','club_submitted','club_approve','club_return','proposal_submitted','proposal_advisor_approve','proposal_sld_approve','proposal_return','finance_submitted','finance_approved','finance_returned','late_submission_permission_granted','late_submission_permission_revoked'}
    if action.startswith('withdrawal_') and action!='withdrawal_draft_saved':
        record=app.get('withdrawal',rid);club=app.get('club',record['club_id'])
        recipients={m['email'] for m in club.get('committee',[])}|{club['advisor_email']}
        if record['status'] in ('pending_sld','pending_finance','pending_all_approve','pending_acknowledgement'):
            recipients.update(e.strip().lower() for e in os.getenv('SLD_ADMIN_EMAILS','').split(',') if e.strip())
            if app.preview:recipients.add(auth.preview_user('sld')['email'])
        title='Withdrawal '+record['status'].replace('_',' ')
        for email in recipients-{user['email']}:
            app.put('notification',dict(id=hashlib.sha256((str(log_id)+'|'+email).encode()).hexdigest(),recipient=email,title=title,message=record.get('purpose','Withdrawal')+' — '+title.lower()+'.',created_at=entry['timestamp'],read_at=None,record_type='withdrawal',record_id=rid,club_id=club['id'],club_name=club['name']))
        return
    if action.startswith('event_completion_') and action in ('event_completion_submitted','event_completion_approved','event_completion_returned'):
        record=app.get('event_completion',rid);club=app.get('club',record['club_id']);proposal=app.get('proposal',record['proposal_id'])
        recipients={m['email'] for m in club.get('committee',[])}|{m['email'] for m in proposal.get('committee',[])}|{club['advisor_email']}
        if action=='event_completion_submitted':
            recipients.update(e.strip().lower() for e in os.getenv('SLD_ADMIN_EMAILS','').split(',') if e.strip())
            if app.preview:recipients.add(auth.preview_user('sld')['email'])
        title='Event completion '+action.rsplit('_',1)[-1]
        for email in recipients-{user['email']}:
            app.put('notification',dict(id=hashlib.sha256((str(log_id)+'|'+email).encode()).hexdigest(),recipient=email,title=title,message=proposal.get('title','Event')+' — '+title.lower()+'.',created_at=entry['timestamp'],read_at=None,record_type='event_completion',record_id=rid,proposal_id=proposal['id'],club_id=club['id'],club_name=club['name']))
        return
    if action.startswith('club_report_') and action!='club_report_draft_saved':
        report=app.get('club_report',rid);club=app.get('club',report['club_id'])
        members={p['email'] for p in club.get('committee',[]) if p.get('email')}
        recipients=members|{club['advisor_email']}
        if report['status']=='pending_sld':
            recipients.update(e.strip().lower() for e in os.getenv('SLD_ADMIN_EMAILS','').split(',') if e.strip())
            if app.preview:recipients.add(auth.preview_user('sld')['email'])
        title={'club_report_submitted':'Report awaiting Secretary review','club_report_secretary_approved':'Report awaiting advisor review','club_report_advisor_approved':'Report awaiting SLD review','club_report_sld_approved':'Club activity report approved','club_report_returned':'Club report returned for correction','club_report_handover_applied':'Approved AGM committee handover applied'}.get(action)
        if not title:return
        for email in recipients-{user['email']}:
            app.put('notification',dict(id=hashlib.sha256((str(log_id)+'|'+email).encode()).hexdigest(),recipient=email,title=title,message=report['title']+' — '+title.lower()+'.',created_at=entry['timestamp'],read_at=None,record_type='club_report',record_id=rid,club_id=club['id'],club_name=club['name']))
        return
    if action in ('club_draft_saved','proposal_draft_saved'):
        kind='proposal' if action.startswith('proposal_') else 'club'
        record=app.get(kind,rid)
        club=app.get('club',record['club_id']) if kind=='proposal' else record
        marker_id=kind+'-'+rid
        previous=next((r for r in app.all('notification_assignment') if r['id']==marker_id),{'emails':[]})
        emails={p['email'] for p in record.get('committee',[]) if p.get('email')}
        if kind=='club':
            emails.add(club['advisor_email'])
        for email in emails-set(previous['emails'])-{user['email']}:
            n=dict(id=hashlib.sha256((str(log_id)+'|assignment|'+email).encode()).hexdigest(),recipient=email,title='New '+kind+' assignment',message='You have been assigned to '+(record.get('title') or club['name'])+'.',created_at=entry['timestamp'],read_at=None,record_type=kind,record_id=rid,club_id=club['id'],club_name=club['name'])
            if kind=='proposal':
                n['proposal_id']=rid
            app.put('notification',n)
        app.put('notification_assignment',{'id':marker_id,'emails':sorted(emails)})
        return
    if action not in meaningful:
        return
    recipients=set();admins={e.strip().lower() for e in os.getenv('SLD_ADMIN_EMAILS','').split(',') if e.strip()}
    if app.preview:
        admins.add(auth.preview_user('sld')['email'])
    if action=='club_registration_authorized':
        grant=app.get('registration_grant',rid);record_type='grant'
        recipients={grant['president_email'],grant['advisor_email']};name=grant['club_name'];club_id=grant.get('club_id','')
        title='Club registration authorized';message='SLD authorized the assigned president to complete this club registration.'
    else:
        if action.startswith(('proposal_','finance_')):
            proposal=app.get('proposal',rid);club=app.get('club',proposal['club_id']);record_type='proposal'
            if action.startswith('finance_'):
                report=next((r for r in app.all('finance_report') if r['proposal_id']==rid),None)
                if not report:
                    return
                record_type='finance_report';record_id=report['id']
        else:
            club=app.get('club',entry.get('club_id') or rid)
        club_id=club['id'];name=club['name'];members={p['email'] for p in club.get('committee',[]) if p.get('email')}
        if proposal:
            members.update(p['email'] for p in proposal.get('committee',[]) if p.get('email'))
        if action in ('club_submitted','proposal_submitted'):
            recipients=members|{club['advisor_email']}
        elif action=='proposal_advisor_approve' or action=='finance_submitted' or action=='club_approve' and club['status'] in ('pending_sld','reviewing_sld'):
            recipients=admins|members|{club['advisor_email']}
        else:
            recipients=members|{club['advisor_email']}
        labels={'club_submitted':'Club registration awaiting advisor review','club_approve':'Club registration review completed','club_return':'Club registration returned for correction','proposal_submitted':'Event proposal awaiting advisor review','proposal_advisor_approve':'Event proposal awaiting SLD review','proposal_sld_approve':'Event proposal approved','proposal_return':'Event proposal returned for correction','finance_submitted':'Financial report awaiting SLD review','finance_approved':'Financial report approved','finance_returned':'Financial report returned for correction','late_submission_permission_granted':'Late submission permission granted','late_submission_permission_revoked':'Late submission permission revoked'}
        title=labels[action];message=(proposal.get('title') or 'Event proposal') if proposal else name
        message+=' — '+title.lower()+'.'
    for email in recipients-{user['email']}:
        notification=dict(id=hashlib.sha256((str(log_id)+'|'+email).encode()).hexdigest(),recipient=email,title=title,message=message,created_at=entry['timestamp'],read_at=None,record_type=record_type,record_id=record_id,club_id=club_id,club_name=name)
        if proposal:
            notification['proposal_id']=proposal['id']
        app.put('notification',notification)
