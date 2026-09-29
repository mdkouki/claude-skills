#!/usr/bin/env python3
"""
Serve the review board on localhost only and wait for the submitted decisions.

Fully local: stdlib only, binds to 127.0.0.1 (never 0.0.0.0), never talks to
any external service. Serves the given HTML file at '/', opens it in the
user's default browser, then blocks until a POST to /submit arrives with the
decision JSON, writes that JSON to <decisions_out>, and exits.

The exit is acknowledged, not instant: after /submit the page confirms it got
the response with a POST to /bye and the server exits on that (or after a
short timeout if the tab is gone). Exiting the moment /submit is answered
makes the browser's fetch() fail with "Failed to fetch" even though the
decisions were saved.

Usage: serve_review.py <html_file> <decisions_out.json> <url_out.txt> [--port N]

Run this in the background (it blocks on purpose) and wait for it to exit —
that's the signal the user submitted their review. The page closes itself on
submit; the LLM then writes the decision table and takes the final
green/red light in the terminal.
"""
import http.server
import json
import sys
import time
import threading
import webbrowser
from pathlib import Path


def pop_opt(args, name, cast=str):
    if name in args:
        i = args.index(name)
        val = cast(args[i + 1])
        del args[i:i + 2]
        return val
    return None


def main():
    args = sys.argv[1:]
    port = pop_opt(args, "--port", int) or 0

    html_path, decisions_path, url_path = (Path(a) for a in args[:3])
    html_bytes = html_path.read_bytes()
    done = threading.Event()

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def reply(self, code, body=b"", ctype="application/json"):
            self.send_response(code)
            if body:
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            # one request per connection: a browser reusing a socket we are
            # about to close is what makes fetch() fail intermittently
            self.send_header("Connection", "close")
            self.close_connection = True
            self.end_headers()
            if body:
                self.wfile.write(body)

        def read_json(self):
            length = int(self.headers.get("Content-Length", "0"))
            try:
                return json.loads(self.rfile.read(length))
            except json.JSONDecodeError:
                return None

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self.reply(200, html_bytes, "text/html; charset=utf-8")
            else:
                self.reply(404)

        def do_POST(self):
            data = self.read_json()
            if data is None:
                self.reply(400)
            elif self.path == "/submit":
                decisions_path.write_text(json.dumps(data, indent=2))
                self.reply(200, b'{"ok":true}')
                # safety net if the tab closes before it can say /bye
                safety = threading.Timer(10, done.set)
                safety.daemon = True
                safety.start()
            elif self.path == "/bye":
                self.reply(200, b'{"ok":true}')
                done.set()
            else:
                self.reply(404)

    # Threaded: browsers open speculative idle connections, which would block
    # a single-threaded server and can get the real request reset.
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    actual_port = server.server_address[1]
    url = f"http://127.0.0.1:{actual_port}"
    url_path.write_text(url)
    print(url, flush=True)

    webbrowser.open(url)

    threading.Thread(target=server.serve_forever, daemon=True).start()
    done.wait()
    time.sleep(0.3)  # let the /bye response leave the socket
    server.shutdown()
    server.server_close()


if __name__ == "__main__":
    main()
