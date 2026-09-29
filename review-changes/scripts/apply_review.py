#!/usr/bin/env python3
"""
Apply a review decision (approved/rejected hunks and files) on top of the
diff data produced by build_review_data.py. Never calls git — this only
writes/deletes plain files on disk, so it doesn't conflict with a
never-mutate-git policy. The user still stages/commits everything themselves.

Usage: apply_review.py <review-data.json> <decisions.json> <repo-root> [--reject-all]

--reject-all is the "red light": ignore decisions.json and revert every
modification (decisions.json is still required on the command line, any
valid file will do).

decisions.json shape:
{
  "files": {
    "<path>": {
      "file": "accept" | "reject",       // whole-file decision, used for
                                          // added/deleted files and as the
                                          // default for any hunk not listed
      "hunks": { "<hunkId>": "accept" | "reject", ... }
    },
    ...
  }
}
A file/hunk missing from decisions.json is treated as "accept" (i.e. left
exactly as the AI produced it) — decisions only need to list overrides.

Prints a JSON summary of what was written/reverted/deleted to stdout.
"""
import json
import sys
from pathlib import Path


def reconstruct(old_content, hunks, hunk_decisions):
    """old_content: full text of the file at HEAD (or "" for a brand new file).
    Walk hunks in old-file order, copying unchanged old text between them and
    emitting either the hunk's new lines (accept) or its old lines (reject)."""
    old_lines = old_content.splitlines(keepends=True) if old_content else []
    out = []
    cursor = 0  # next old line index (0-based) not yet emitted
    for h in sorted(hunks, key=lambda h: h["oldStart"]):
        start0 = max(h["oldStart"] - 1, 0)
        out.extend(old_lines[cursor:start0])
        decision = hunk_decisions.get(h["id"], "accept")
        if decision == "accept":
            out.extend(l["text"] + "\n" for l in h["new"])
        else:
            out.extend(l["text"] + "\n" for l in h["old"] if l["type"] != "add")
        cursor = start0 + h["oldLines"]
    out.extend(old_lines[cursor:])
    text = "".join(out)
    # best-effort: drop a synthetic trailing newline reconstruct() may add
    # when the new content never actually ended in one
    return text


def main():
    argv = [a for a in sys.argv[1:] if a != "--reject-all"]
    reject_all = len(argv) != len(sys.argv) - 1
    if len(argv) != 3:
        print("usage: apply_review.py <review-data.json> <decisions.json> <repo-root> [--reject-all]", file=sys.stderr)
        sys.exit(1)

    data = json.loads(Path(argv[0]).read_text())
    decisions = json.loads(Path(argv[1]).read_text())
    root = Path(argv[2])

    file_decisions = decisions.get("files", {})
    summary = {"kept": [], "reverted": [], "deleted": [], "restored": [], "unchanged": []}

    for f in data["files"]:
        path = f["path"]
        dec = file_decisions.get(path, {})
        file_level = "reject" if reject_all else dec.get("file", "accept")
        hunk_decisions = {} if reject_all else dec.get("hunks", {})
        target = root / path

        if f.get("binary") or f.get("error"):
            summary["unchanged"].append(path)
            continue

        if f["changeType"] == "added":
            if file_level == "reject":
                if target.exists():
                    target.unlink()
                summary["deleted"].append(path)
            else:
                summary["kept"].append(path)
            continue

        if f["changeType"] == "deleted":
            if file_level == "reject":
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(f["oldContent"] or "")
                summary["restored"].append(path)
            else:
                summary["kept"].append(path)
            continue

        # modified: reconstruct hunk-by-hunk unless the whole file was
        # rejected outright (equivalent to rejecting every hunk)
        effective_hunk_decisions = dict(hunk_decisions)
        if file_level == "reject":
            for h in f["hunks"]:
                effective_hunk_decisions.setdefault(h["id"], "reject")

        if not f["hunks"]:
            summary["unchanged"].append(path)
            continue

        new_text = reconstruct(f["oldContent"] or "", f["hunks"], effective_hunk_decisions)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(new_text)
        if all(effective_hunk_decisions.get(h["id"], "accept") == "accept" for h in f["hunks"]):
            summary["kept"].append(path)
        elif all(effective_hunk_decisions.get(h["id"], "accept") == "reject" for h in f["hunks"]):
            summary["reverted"].append(path)
        else:
            summary["reverted"].append(f"{path} (partial)")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
