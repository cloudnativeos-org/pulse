#!/usr/bin/env python3
"""Serve the built site for review, and reload open pages when a rebuild lands.

Usage: serve.py [--port 8765] [--bind 0.0.0.0] [site/out]

A page polls /__version once a second. The answer is the newest modification
time under the served directory, so any rebuild makes open pages reload.
For local review only; the published site does not include the reload script.
"""
import argparse
import functools
import http.server
import os

RELOAD = (b'<script>(function(){var v=null;setInterval(function(){fetch("/__version",{cache:"no-store"})'
          b'.then(function(r){return r.text()}).then(function(t){if(v===null)v=t;else if(t!==v)location.reload()})'
          b'.catch(function(){})},1000)})();</script>')


def newest(root):
    m = 0.0
    for d, _, files in os.walk(root):
        for f in files:
            try:
                m = max(m, os.path.getmtime(os.path.join(d, f)))
            except OSError:
                pass
    return m


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/__version":
            body = str(newest(self.directory)).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            path = os.path.join(path, "index.html")
        if path.endswith(".html") and os.path.isfile(path):
            data = open(path, "rb").read()
            data = data.replace(b"</body>", RELOAD + b"</body>", 1) if b"</body>" in data else data + RELOAD
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        super().do_GET()

    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--bind", default="127.0.0.1")
    a = ap.parse_args()
    srv = http.server.ThreadingHTTPServer((a.bind, a.port), functools.partial(Handler, directory=a.root))
    print("serving %s on http://%s:%d/site/index.html, reloading on rebuild" % (a.root, a.bind, a.port), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
