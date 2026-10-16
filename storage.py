"""SQLite preview and transactional MySQL production storage."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import threading
import time


class StorageError(RuntimeError):
    pass


def mysql_config():
    required=('MYSQL_HOST','MYSQL_DATABASE','MYSQL_USER','MYSQL_PASSWORD','SLD_SESSION_ENCRYPTION_KEY')
    missing=[key for key in required if not os.getenv(key)]
    if missing:
        raise StorageError('Missing MySQL configuration: '+', '.join(missing))
    try:
        port=int(os.getenv('MYSQL_PORT','3306'))
        if not 1<=port<=65535:
            raise ValueError()
    except ValueError:
        raise StorageError('MYSQL_PORT must be a valid port.')
    config=dict(host=os.environ['MYSQL_HOST'],port=port,user=os.environ['MYSQL_USER'],password=os.environ['MYSQL_PASSWORD'],
                database=os.environ['MYSQL_DATABASE'],charset='utf8mb4',autocommit=True,connect_timeout=10,read_timeout=30,write_timeout=30)
    if os.getenv('MYSQL_SSL_CA'):
        config['ssl']={'ca':os.environ['MYSQL_SSL_CA'],'check_hostname':True}
    return config


class MySQLStore:
    def __init__(self, initialize=False):
        import pymysql
        from cryptography.fernet import Fernet
        config=mysql_config()
        try:
            self.cipher=Fernet(os.environ['SLD_SESSION_ENCRYPTION_KEY'].encode())
        except Exception:
            raise StorageError('SLD_SESSION_ENCRYPTION_KEY must be a valid Fernet key.')
        try:
            self.connection=pymysql.connect(**config)
        except Exception:
            raise StorageError('MySQL connection failed. Check hosting credentials, reachability and TLS configuration.')
        self.lock=threading.RLock()
        self.depth=0
        self.contexts=threading.local()
        self.lock_name='qiu-sld:'+hashlib.sha256(config['database'].encode()).hexdigest()[:48]
        if initialize:
            schema=(Path(__file__).parent/'mysql_schema.sql').read_text(encoding='utf-8')
            for statement in schema.split(';'):
                if statement.strip():
                    self.execute(statement)
        try:
            self.execute('SELECT kind,id,data,seq FROM records LIMIT 0')
            self.execute('SELECT id,data FROM logs LIMIT 0')
            self.execute('SELECT id,data,expires_at,revoked FROM sessions LIMIT 0')
        except Exception:
            self.connection.close()
            raise StorageError('MySQL schema is missing or incompatible. Run the explicit migration tool first.')

    def execute(self, sql, parameters=()):
        sql=sql.replace('?', '%s').replace('rowid','seq')
        if sql.startswith('INSERT OR REPLACE INTO records VALUES'):
            sql='INSERT INTO records(kind,id,data) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE data=VALUES(data)'
        elif sql.startswith('INSERT INTO records VALUES'):
            sql='INSERT INTO records(kind,id,data) VALUES (%s,%s,%s)'
        with self.lock:
            if not self.depth:
                try:
                    self.connection.ping(reconnect=True)
                except Exception:
                    raise StorageError('MySQL is unavailable. Retry shortly.')
            cursor=self.connection.cursor()
            cursor.execute(sql,parameters)
            return cursor

    def commit(self):
        if not self.depth:
            self.connection.commit()

    def flush(self):
        # Persist state and encrypted session before sending a success response.
        with self.lock:
            self.connection.commit()

    @contextmanager
    def mutation(self):
        with self.lock:
            outer=self.depth==0
            if outer:
                result=self.execute('SELECT GET_LOCK(%s,15)',(self.lock_name,)).fetchone()
                if not result or result[0]!=1:
                    raise StorageError('The database is busy. Retry your saved request shortly.')
                try:
                    self.connection.begin()
                except Exception:
                    self.execute('SELECT RELEASE_LOCK(%s)',(self.lock_name,))
                    raise
            self.depth+=1
            try:
                yield self
                if outer:
                    self.connection.commit()
            except Exception:
                if outer:
                    self.connection.rollback()
                raise
            finally:
                self.depth-=1
                if outer:
                    self.execute('SELECT RELEASE_LOCK(%s)',(self.lock_name,))

    def __enter__(self):
        context=self.mutation()
        result=context.__enter__()
        if not hasattr(self.contexts,'stack'):
            self.contexts.stack=[]
        self.contexts.stack.append(context)
        return result

    def __exit__(self,*error):
        return self.contexts.stack.pop().__exit__(*error)

    def load_session(self, token):
        key=hashlib.sha256(token.encode()).hexdigest()
        row=self.execute('SELECT data,expires_at,revoked FROM sessions WHERE id=%s',(key,)).fetchone()
        if not row or row[2] or row[1]<=time.time():
            return None
        try:
            return json.loads(self.cipher.decrypt(row[0].encode()))
        except Exception:
            return None

    def save_session(self,token,session):
        key=hashlib.sha256(token.encode()).hexdigest()
        encrypted=self.cipher.encrypt(json.dumps(session).encode()).decode()
        # Revoked tombstones prevent an older concurrent request from resurrecting a signed-out session.
        self.execute('INSERT INTO sessions(id,data,expires_at,revoked) VALUES (%s,%s,%s,0) ON DUPLICATE KEY UPDATE data=IF(revoked=0,VALUES(data),data),expires_at=IF(revoked=0,VALUES(expires_at),expires_at)',
                     (key,encrypted,session['expires']))
        self.execute('DELETE FROM sessions WHERE expires_at<%s',(time.time()-86400,))

    def revoke_session(self,token):
        key=hashlib.sha256(token.encode()).hexdigest()
        self.execute('UPDATE sessions SET revoked=1 WHERE id=%s',(key,))

    def close(self):
        self.connection.close()


def connect(db_path, preview=False):
    engine=os.getenv('SLD_STORAGE','sqlite').lower()
    production=os.getenv('SLD_ENV','local').lower()=='production'
    if preview:
        if production:
            raise StorageError('Preview identities cannot run in production.')
        engine='sqlite'
    if production and engine!='mysql':
        raise StorageError('Production requires SLD_STORAGE=mysql; SQLite is only for local review.')
    if engine=='mysql':
        return MySQLStore()
    if engine!='sqlite':
        raise StorageError('SLD_STORAGE must be sqlite or mysql.')
    db=sqlite3.connect(str(db_path),check_same_thread=False)
    db.execute('PRAGMA journal_mode=WAL')
    db.executescript('CREATE TABLE IF NOT EXISTS records (kind TEXT,id TEXT,data TEXT,PRIMARY KEY(kind,id)); CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, data TEXT);')
    db.commit()
    return db
