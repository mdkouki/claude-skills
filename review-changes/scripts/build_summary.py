#!/usr/bin/env python3
"""
Build the final decision table from review-data.json (with `cls` merged in)
and the submitted decisions.json, and print it as a markdown table for the
LLM to paste into the terminal. Optionally also write it as JSON.

Usage: build_summary.py <review-data.json> <decisions.json> [<summary.json>]

Each row: one hunk (modified file) or one whole file (added/deleted), with the
LLM-written short title, importance, final decision, and who decided it
("user" or "llm"; a user decision that differs from the LLM's verdict on a
minor item is flagged as an override).

Read-only apart from the optional summary.json. Never calls git.
"""
import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) not in (3, 4):
        print("usage: build_summary.py <review-data.json> <decisions.json> [<summary.json>]", file=sys.stderr)
        sys.exit(1)

    data = json.loads(Path(sys.argv[1]).read_text())
    decisions = json.loads(Path(sys.argv[2]).read_text()).get("files", {})

    rows = []
    for f in data["files"]:
        if f.get("binary") or f.get("error"):
            continue
        dec = decisions.get(f["path"], {})
        by = dec.get("decidedBy", {})
        if f["changeType"] in ("added", "deleted"):
            targets = [("file", f.get("cls"), dec.get("file", "accept"))]
        else:
            targets = [(h["id"], h.get("cls"), dec.get("hunks", {}).get(h["id"], "accept")) for h in f["hunks"]]
        for ident, cls, decision in targets:
            cls = cls or {"importance": "important", "reasons": ["unclassified"], "title": f"{f['path']} {ident}"}
            decided_by = by.get(ident, "user")
            rows.append({
                "path": f["path"],
                "id": ident,
                "title": cls["title"],
                "importance": cls["importance"],
                "reasons": cls.get("reasons", []),
                "decision": decision,
                "decidedBy": decided_by,
                "override": (
                    cls["importance"] == "minor"
                    and decided_by == "user"
                    and decision != cls.get("llmDecision")
                ),
            })

    counts = {
        "total": len(rows),
        "accepted": sum(r["decision"] == "accept" for r in rows),
        "rejected": sum(r["decision"] == "reject" for r in rows),
        "important": sum(r["importance"] == "important" for r in rows),
        "minor": sum(r["importance"] == "minor" for r in rows),
        "overrides": sum(r["override"] for r in rows),
    }
    if len(sys.argv) == 4:
        Path(sys.argv[3]).write_text(json.dumps({"rows": rows, "counts": counts}, indent=2))

    print("| # | Change | File | Importance | Decision | Decided by |")
    print("|---|--------|------|------------|----------|------------|")
    for i, r in enumerate(rows, 1):
        imp = "important (" + ", ".join(r["reasons"]) + ")" if r["importance"] == "important" else "minor"
        who = "user (override)" if r["override"] else r["decidedBy"]
        print(f"| {i} | {r['title']} | {r['path']} | {imp} | {r['decision']} | {who} |")
    print()
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
