"""Read-only deployment diagnostic. Never print secrets or initialize a database."""
import argparse
import importlib.util
import json
import os
import pathlib
import sys
from urllib.parse import urlsplit

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def check(connect=False):
    results=[]
    def add(name,passed,detail):
        results.append({'check':name,'status':'pass' if passed else 'required','detail':detail})
    add('Python runtime',sys.version_info>=(3,12),'Use Python 3.12 or newer; current '+sys.version.split()[0])
    for module in ('pymysql','cryptography','lxml','openpyxl','reportlab','PIL','google.auth','requests'):
        try:available=importlib.util.find_spec(module) is not None
        except ModuleNotFoundError:available=False
        add('Dependency '+module,available,'Install requirements.txt in the hosting Python environment.')
    url=urlsplit(os.getenv('SLD_APP_URL',''))
    add('HTTPS origin',url.scheme=='https' and bool(url.hostname) and not url.username and not url.password
        and url.path in ('','/') and not url.query and not url.fragment,'Use a dedicated domain/subdomain root, not a /sld path.')
    add('Production mode',os.getenv('SLD_ENV')=='production','Set SLD_ENV=production; preview access must be disabled.')
    add('MySQL storage',os.getenv('SLD_STORAGE')=='mysql','Set SLD_STORAGE=mysql and university-owned database credentials.')
    for name in ('MYSQL_HOST','MYSQL_DATABASE','MYSQL_USER','MYSQL_PASSWORD','SLD_SESSION_ENCRYPTION_KEY',
                 'GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET','SLD_ADMIN_EMAILS'):
        add('Configured '+name,bool(os.getenv(name)),'Value required; intentionally not displayed.')
    import exports
    add('Original-template PDF renderer',exports.pdf_available(),'Host must permit installed LibreOffice/soffice; set SOFFICE_PATH if needed.')
    add('Proposal source template',exports.TEMPLATE.is_file(),'Retain templates/event-proposal.docx in the application directory.')
    data=pathlib.Path(os.getenv('SLD_DATA_DIR',str(ROOT/'data')))
    public_names={'public_html','httpdocs','htdocs'}
    add('Private data directory',data.exists() and os.access(data,os.W_OK) and not public_names.intersection(data.resolve().parts),
        'Requires writable directory outside common public roots; IT must also confirm the actual web-server document root.')
    if connect:
        try:
            import pymysql
            import storage
            config=storage.mysql_config()
            config.update(read_timeout=10,write_timeout=10)
            connection=pymysql.connect(**config)
            try:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT VERSION()');version=cursor.fetchone()[0]
                    cursor.execute('SHOW TABLES');tables={row[0] for row in cursor.fetchall()}
                add('Database connection',True,'Server version '+version)
                add('Application schema',{'records','logs','sessions'}.issubset(tables),'Run the documented schema/migration step before enabling the application.')
            finally:connection.close()
        except Exception:
            add('Database connection',False,'Connection failed. Check credentials, permissions and server reachability privately; no raw error/secret displayed.')
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--connect',action='store_true',help='Also perform read-only database connectivity/schema checks.')
    args=parser.parse_args();results=check(args.connect)
    print(json.dumps({'checks':results,'provider_wsgi_enabled':'Requires confirmation in the Exabytes account panel.',
                      'live_deployment_verified':False},indent=2))
    sys.exit(0 if all(r['status']=='pass' for r in results) else 1)
