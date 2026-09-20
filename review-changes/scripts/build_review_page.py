#!/usr/bin/env python3
"""
Merge review-data.json into template.html to produce the self-contained
review page, escaping the data safely for embedding inside an inline
<script> block.

Why this needs escaping (not just json.dumps + string concat): the diff
data can itself contain the literal text "</script>" — e.g. when the file
being reviewed is HTML/JS, as with this skill's own template.html. The
browser's HTML parser closes a <script> element at the first "</script"
byte sequence it sees, regardless of JS string/quote context, so an
unescaped occurrence truncates the page's own script and window.__REVIEW_DATA__
never gets assigned. Escaping "</" as "<" + backslash + "/" inside the JSON
text prevents that without changing the parsed JSON value (JSON and JS both
treat a backslash-escaped "/" as just "/").

Usage: build_review_page.py <template.html> <review-data.json> <output.html>
"""
import sys
from pathlib import Path

MARKER = "<script>\n(function(){"


def main():
    template_path, data_path, out_path = (Path(a) for a in sys.argv[1:4])
    template = template_path.read_text()
    data = data_path.read_text()

    safe_data = data.replace("</", "<\\/")

    if MARKER not in template:
        print("error: template.html injection marker not found — did the template change?", file=sys.stderr)
        sys.exit(1)

    injected = f"<script>window.__REVIEW_DATA__ = {safe_data};</script>\n" + MARKER
    merged = template.replace(MARKER, injected, 1)
    out_path.write_text(merged)
    print(f"wrote {out_path} ({len(merged)} bytes)")


if __name__ == "__main__":
    main()
