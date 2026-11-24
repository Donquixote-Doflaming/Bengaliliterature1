#!/usr/bin/env python3
"""Static server for the বাংলা সাহিত্য study site — with gzip, because the
full-text payload is ~2 MB of Bengali."""
import gzip, io, os, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

GZ_TYPES = ('.js', '.css', '.html', '.json', '.svg', '.txt', '.md')


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def guess_type(self, path):
        if path.endswith('.woff2'):
            return 'font/woff2'
        if path.endswith('.js'):
            return 'text/javascript; charset=utf-8'
        return super().guess_type(path)

    def do_GET(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            path = os.path.join(path, 'index.html')
        if not os.path.isfile(path):
            return self.send_error(404)
        ext = os.path.splitext(path)[1].lower()
        if ext not in GZ_TYPES or 'gzip' not in (self.headers.get('Accept-Encoding') or ''):
            return SimpleHTTPRequestHandler.do_GET(self)
        with open(path, 'rb') as f:
            raw = f.read()
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode='wb', compresslevel=6) as gz:
            gz.write(raw)
        body = buf.getvalue()
        self.send_response(200)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Encoding', 'gzip')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


if __name__ == '__main__':
    print('serving %s on http://0.0.0.0:%d' % (ROOT, PORT))
    ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
