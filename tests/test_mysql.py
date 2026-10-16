"""Explicit loopback-only integration against an isolated MySQL-compatible QA server.

Creates uniquely named disposable database/account, never targets university data.
Run with --port for the portable QA instance; do not use this against hosting.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import io
import json
import hashlib
import os
import pathlib
import secrets
import sys
import sqlite3
import subprocess
import tempfile
import time
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
import auth,finance,server,storage,wsgi
from proposal_fixture import complete_proposal
import pymysql
from cryptography.fernet import Fernet


def run(port):
    database='sld_root_qa_'+secrets.token_hex(5)
    password=secrets.token_urlsafe(28)
    admin=pymysql.connect(host='127.0.0.1',port=port,user='root',password=os.getenv('SLD_QA_ROOT_PASSWORD',''),autocommit=True)
    apps=[]
    with admin.cursor() as cursor:
        cursor.execute('CREATE DATABASE `'+database+'` CHARACTER SET utf8mb4')
        cursor.execute('CREATE USER %s@%s IDENTIFIED BY %s',(database,'127.0.0.1',password))
        cursor.execute('GRANT ALL ON `'+database+'`.* TO %s@%s',(database,'127.0.0.1'))
    environment={'SLD_ENV':'production','SLD_STORAGE':'mysql','MYSQL_HOST':'127.0.0.1','MYSQL_PORT':str(port),
        'MYSQL_DATABASE':database,'MYSQL_USER':database,'MYSQL_PASSWORD':password,
        'SLD_SESSION_ENCRYPTION_KEY':Fernet.generate_key().decode(),'SLD_ADMIN_EMAILS':'demo.sld@qiu.edu.my'}
    try:
        with patch.dict(os.environ,environment),tempfile.TemporaryDirectory() as directory:
            store=storage.MySQLStore(initialize=True);store.close()
            source=pathlib.Path(directory)/'source.sqlite3'
            connection=sqlite3.connect(source)
            connection.executescript('CREATE TABLE records(kind TEXT,id TEXT,data TEXT,PRIMARY KEY(kind,id));CREATE TABLE logs(id INTEGER PRIMARY KEY,data TEXT);')
            connection.execute('INSERT INTO records VALUES(?,?,?)',('qa','counter',json.dumps({'id':'counter','value':0,'text':'中文'})))
            connection.commit();connection.close()
            digest=hashlib.sha256(source.read_bytes()).hexdigest()
            migration=subprocess.run([sys.executable,str(ROOT/'tools/migrate_mysql.py'),'--sqlite',str(source)],capture_output=True,text=True)
            assert migration.returncode==0,migration.stderr
            assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
            apps=[server.App(pathlib.Path(directory)/'unused.sqlite3',False,'https://sld.qiu.edu.my') for _ in range(2)]
            first,second=apps
            assert second.get('qa','counter')['text']=='中文'
            refused=subprocess.run([sys.executable,str(ROOT/'tools/migrate_mysql.py'),'--sqlite',str(source)],capture_output=True,text=True)
            assert refused.returncode!=0 and first.get('qa','counter')['value']==0
            try:
                with first.mutation():
                    first.put('qa',{'id':'counter','value':999})
                    raise ValueError('abort test transaction')
            except ValueError:pass
            assert second.get('qa','counter')['value']==0
            def increment(app):
                for _ in range(15):
                    with app.mutation():
                        row=app.get('qa','counter');row['value']+=1;app.put('qa',row)
            with ThreadPoolExecutor(max_workers=3) as pool:
                list(pool.map(increment,[first,first,second]))
            assert second.get('qa','counter')['value']==45
            first.db.connection.close()
            assert first.get('qa','counter')['value']==45
            token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(32)
            session={'csrf':csrf,'expires':time.time()+3600,'user':auth.preview_user('sld'),'private_qa_token':'not-plaintext'}
            first.db.save_session(token,session)
            assert second.db.load_session(token)['csrf']==csrf
            encrypted=first.db.execute('SELECT data FROM sessions').fetchone()[0]
            assert 'not-plaintext' not in encrypted and 'demo.sld' not in encrypted
            adapters=[wsgi.make_application(lambda app=app:app) for app in apps]
            def call(worker,path,data=None):
                body=b'' if data is None else json.dumps(data).encode();result=[]
                env={'REQUEST_METHOD':'GET' if data is None else 'POST','PATH_INFO':path,'QUERY_STRING':'',
                    'wsgi.input':io.BytesIO(body),'CONTENT_LENGTH':str(len(body)),'CONTENT_TYPE':'application/json',
                    'HTTP_COOKIE':'sld_session='+token,'HTTP_ORIGIN':first.base_url,'HTTP_X_CSRF_TOKEN':csrf}
                raw=b''.join(adapters[worker](env,lambda status,headers:result.append(status)))
                return int(result[0].split()[0]),json.loads(raw)
            assert call(1,'/api/bootstrap')[1]['user']['role']=='sld'
            status,answer=call(0,'/api/assistant/query',{'question':'Upcoming events'})
            assert status==200 and answer.get('history_id'),answer
            status,saved=call(1,'/api/assistant/history')
            assert status==200 and saved['total']==1 and saved['entries'][0]['id']==answer['history_id'],saved
            status,deleted=call(1,'/api/assistant/history/delete',{'id':answer['history_id']})
            assert status==200 and deleted['deleted']==1 and call(0,'/api/assistant/history')[1]['total']==0
            club=dict(id='club',name='MySQL 财务协会',status='approved',advisor_email='demo.advisor@qiu.edu.my',
                committee=[dict(position='President',email='demo.student@qiu.edu.my',name='Demo Student')],revision=1,
                created_at=auth.now(),updated_at=auth.now(),history=[])
            first.put('club',club)
            proposal=dict(complete_proposal(date='2026-10-01',end_date='2026-10-01',revenue=[],
                expenses=[dict(description='Materials',price='10',quantity='1')]),id='event',status='approved',revision=1,
                created_at=auth.now(),updated_at=auth.now(),history=[])
            first.put('proposal',proposal)
            from PIL import Image
            import evidence
            for colour in ('navy','red'):
                photo_stream=io.BytesIO();Image.new('RGB',(24,24),colour).save(photo_stream,format='PNG')
                status,uploaded=call(0,'/api/photos',dict(target_type='proposal',target_id='event',name=colour+'.png',data_url='data:image/png;base64,'+base64.b64encode(photo_stream.getvalue()).decode()))
                assert status==200,uploaded
            photo_metadata=evidence.view(second,session['user'],'proposal','event')['photos'];assert len(photo_metadata)==2 and all('content_base64' not in row for row in photo_metadata)
            status,response=call(0,'/api/receipts',dict(proposal_id='event',filename='proof.pdf',mime='application/pdf',
                content_base64=base64.b64encode(b'%PDF-1.4\nQA evidence').decode()))
            assert status==200,response
            receipt=response['receipt']
            metadata=finance.event_receipts(second,'event');assert len(metadata)==1 and 'content_base64' not in metadata[0]
            status,response=call(0,'/api/finance/reports',dict(report=dict(proposal_id='event',rows=[dict(kind='expense',
                description='Materials',amount='10.00',budget_ref='expenses:0',evidence_ids=[receipt['id']])],variance_reason='')))
            assert status==200,response
            report=response['report'];url='/api/finance/reports/'+report['id']
            status,response=call(1,url+'/submit',{'revision':report['revision'],'confirm_submission':True});assert status==200,response
            report=response['report']
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=list(pool.map(lambda worker:call(worker,url+'/review',dict(revision=report['revision'],action='approve',name='QA SLD')),range(2)))
            assert sorted(status for status,_ in results)==[200,409],results
            assert len(second.all('ledger_entry'))==1 and second.get('finance_report',report['id'])['status']=='approved'
            second.db.revoke_session(token)
            first.db.save_session(token,session)
            assert first.db.load_session(token) is None
            status,response=call(0,url+'/review',{'revision':1,'action':'approve','name':'QA SLD'})
            assert status==401 and response['code']=='SESSION_EXPIRED'
            print('PASS: actual MariaDB/MySQL-protocol safe migration/source preservation/nonempty-target refusal, Unicode, rollback, three-thread/two-worker serialization, reconnect, encrypted shared WSGI sessions, scoped receipt metadata, exactly-once concurrent financial approval and revoked-session rejection.')
    finally:
        for app in apps:app.db.close()
        try:
            with admin.cursor() as cursor:
                cursor.execute('DROP DATABASE `'+database+'`')
                cursor.execute('DROP USER %s@%s',(database,'127.0.0.1'))
        except Exception:
            print('QA teardown needs operator cleanup of '+database+'; no university database was used.')
        admin.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,required=True)
    args=parser.parse_args();run(args.port)
