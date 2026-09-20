#!/usr/bin/env python3
"""
Serve the review page on localhost only and wait for the submitted decision.

Fully local: stdlib only, binds to 127.0.0.1 (never 0.0.0.0), never talks to
any external service. Serves the given HTML file at '/', opens it in the
user's default browser, then blocks until a POST to /submit arrives with the
decision JSON, writes that JSON to <decisions_out>, and exits.

Usage: serve_review.py <html_file> <decisions_out.json> <url_out.txt> [--port N]

Run this in the background (it blocks on purpose) and wait for it to exit —
that's the signal the user submitted their review.
"""
import http.server
import json
import sys
import threading
import webbrowser
from pathlib import Path


def main():
    args = sys.argv[1:]
    port = 0
    if "--port" in args:
        i = args.index("--port")
        port = int(args[i + 1])
        args = args[:i]

    html_path, decisions_path, url_path = (Path(a) for a in args[:3])
    html_bytes = html_path.read_bytes()
    done = threading.Event()

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html_bytes)))
                self.end_headers()
                self.wfile.write(html_bytes)
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            if self.path != "/submit":
                self.send_response(404)
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                return
            decisions_path.write_text(json.dumps(data, indent=2))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
            done.set()

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    actual_port = server.server_address[1]
    url = f"http://127.0.0.1:{actual_port}"
    url_path.write_text(url)
    print(url, flush=True)

    webbrowser.open(url)

    while not done.is_set():
        server.handle_request()
    server.server_close()


if __name__ == "__main__":
    main()
