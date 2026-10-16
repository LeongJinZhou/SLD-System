"""WSGI entry point for Passenger/cPanel or a VPS WSGI server.

Reuse the existing request handlers without opening a development-server socket.
The configured application origin, never forwarded/request headers, controls auth.
"""
import io
import json
import os
import threading
from email.message import Message
from http import HTTPStatus
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import quote, urlsplit

from server import App, Handler

ROOT = Path(__file__).resolve().parent
_app = None
_init_lock = threading.Lock()


def production_app():
    global _app
    with _init_lock:
        if _app is None:
            origin = os.getenv('SLD_APP_URL', '')
            parsed = urlsplit(origin)
            if (parsed.scheme != 'https' or not parsed.hostname or parsed.username
                    or parsed.password or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
                raise RuntimeError('Set SLD_APP_URL to the public HTTPS origin, without a path.')
            if os.getenv('SLD_ENV') != 'production' or os.getenv('SLD_STORAGE') != 'mysql':
                raise RuntimeError('WSGI requires SLD_ENV=production and SLD_STORAGE=mysql.')
            data = Path(os.getenv('SLD_DATA_DIR', str(ROOT / 'data')))
            data.mkdir(parents=True, exist_ok=True)
            _app = App(data / 'sld.sqlite3', False, origin.rstrip('/'))
    return _app


class WSGIHandler(Handler):
    def send_response(self, code, message=None):
        self.result_status = f'{code} {message or HTTPStatus(code).phrase}'
        self.result_headers = []

    def send_header(self, key, value):
        self.result_headers.append((str(key), str(value)))

    def end_headers(self):
        pass

    def log_message(self, format, *args):
        # Host access logs provide operational logging; no tokens/form content.
        pass


def make_application(app_provider=production_app):
    def application(environ, start_response):
        try:
            app = app_provider()
        except Exception:
            raw = json.dumps({'error': 'The service is not configured. Contact Student Life Division.',
                              'code': 'SERVICE_UNAVAILABLE', 'fields': {}}).encode()
            start_response('503 Service Unavailable', [('Content-Type', 'application/json'),
                           ('Cache-Control', 'no-store'), ('Content-Length', str(len(raw)))])
            return [raw]
        handler = WSGIHandler.__new__(WSGIHandler)
        handler.server = SimpleNamespace(app=app)
        handler.command = environ.get('REQUEST_METHOD', 'GET').upper()
        handler.path = quote(environ.get('PATH_INFO', '/'), safe='/%:@')
        if environ.get('QUERY_STRING'):
            handler.path += '?' + environ['QUERY_STRING']
        handler.headers = Message()
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                handler.headers[key[5:].replace('_', '-')] = str(value)
        for key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            if environ.get(key):
                handler.headers[key.replace('_', '-')] = str(environ[key])
        handler.rfile = environ.get('wsgi.input', io.BytesIO())
        handler.wfile = io.BytesIO()
        handler.client_address = (environ.get('REMOTE_ADDR', ''), 0)
        handler.request_version = 'HTTP/1.1'
        if handler.command == 'GET':
            handler.do_GET()
        elif handler.command == 'POST':
            handler.do_POST()
        else:
            handler.json({'error': 'This request method is not supported.', 'code': 'METHOD_NOT_ALLOWED',
                          'fields': {}}, 405)
            handler.result_headers.append(('Allow', 'GET, POST'))
        raw = handler.wfile.getvalue()
        start_response(handler.result_status, handler.result_headers)
        return [raw]
    return application


application = make_application()
