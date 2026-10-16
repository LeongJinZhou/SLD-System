"""Real existing handlers through the WSGI entrypoint, without a socket."""
import io
import json
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server
import wsgi


def run():
    with tempfile.TemporaryDirectory() as directory:
        app = server.App(pathlib.Path(directory) / 'test.sqlite3', True, 'https://sld.qiu.edu.my')
        application = wsgi.make_application(lambda: app)
        cookie = ''
        def call(path, data=None, method=None, extra=None):
            nonlocal cookie
            raw = b'' if data is None else json.dumps(data).encode()
            env = {'REQUEST_METHOD': method or ('POST' if data is not None else 'GET'),
                   'PATH_INFO': path, 'QUERY_STRING': '', 'wsgi.input': io.BytesIO(raw),
                   'CONTENT_LENGTH': str(len(raw)), 'CONTENT_TYPE': 'application/json',
                   'HTTP_COOKIE': cookie, 'HTTP_ORIGIN': app.base_url}
            env.update(extra or {})
            response = []
            body = b''.join(application(env, lambda status, headers: response.append((status, headers))))
            for name, value in response[0][1]:
                if name == 'Set-Cookie':
                    assert 'HttpOnly' in value and 'Secure' in value and 'SameSite=Lax' in value
                    cookie = value.split(';')[0]
            return int(response[0][0].split()[0]), body, response[0][1]
        try:
            status, body, _ = call('/api/bootstrap')
            assert status == 200
            csrf = json.loads(body)['csrf']
            status, body, _ = call('/api/preview/login', {'persona': 'advisor'},
                                  extra={'HTTP_X_CSRF_TOKEN': csrf})
            assert status == 200 and json.loads(body)['user']['role'] == 'advisor'
            assert call('/api/bootstrap')[0] == 200
            status, body, _ = call('/api/proposals', {'proposal': {}},
                                  extra={'HTTP_X_CSRF_TOKEN': 'wrong'})
            assert status == 403 and json.loads(body)['code'] == 'ACCESS_DENIED'
            assert call('/')[0] == 200
            assert call('/setup/google')[0] == 200
            assert call('/../../auth.py')[0] == 404
            status, body, headers = call('/', method='DELETE')
            assert status == 405 and ('Allow', 'GET, POST') in headers
            failed = wsgi.make_application(lambda: (_ for _ in ()).throw(RuntimeError('private secret')))
            headers = []
            body = b''.join(failed({}, lambda status, values: headers.append(status)))
            assert headers == ['503 Service Unavailable'] and b'private secret' not in body
            print('PASS: WSGI delegates bootstrap/login/CSRF/static routes, HTTPS cookie, path rejection, method limits and redacted configuration failure.')
        finally:
            app.db.close()


if __name__ == '__main__':
    run()
