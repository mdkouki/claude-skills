#!/usr/bin/env python3
"""
Build a JSON description of the current uncommitted git changes (working tree
vs HEAD), broken into hunks with old/new line arrays, so it can be embedded
into the review-changes artifact page.

Read-only: only ever runs `git status`, `git diff` and `git show`. Never
mutates the repo or the index.

Usage: build_review_data.py [output.json] [--paths path1 path2 ...]
       (output defaults to stdout; --paths restricts the review to those
       files instead of every uncommitted change in the repo — pass the
       exact files you edited so pre-existing, unrelated uncommitted work
       in the repo doesn't show up in the review)
"""
import json
import re
import subprocess
import sys
from pathlib import Path

MAX_FILE_BYTES = 300_000  # skip embedding full content past this size


def run(args, cwd):
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    return result


def repo_root():
    r = run(["rev-parse", "--show-toplevel"], cwd=".")
    if r.returncode != 0:
        print("error: not inside a git repository", file=sys.stderr)
        sys.exit(1)
    return r.stdout.strip()


def porcelain_entries(root):
    r = run(["status", "--porcelain=v1", "-uall"], cwd=root)
    entries = []
    for line in r.stdout.splitlines():
        if not line:
            continue
        code = line[:2]
        rest = line[3:]
        path = rest
        old_path = None
        if " -> " in rest:
            old_path, path = rest.split(" -> ", 1)
        entries.append((code, old_path, path))
    return entries


def classify(code):
    x, y = code[0], code[1]
    if code == "??":
        return "added"
    if x == "D" or y == "D":
        return "deleted"
    if x == "A" or x == "R" or x == "C":
        return "modified"  # new/renamed file we can still diff against HEAD
    return "modified"


def show_head(root, path):
    r = run(["show", f"HEAD:{path}"], cwd=root)
    if r.returncode != 0:
        return None
    return r.stdout


def read_working(root, path):
    p = Path(root) / path
    try:
        if p.stat().st_size > MAX_FILE_BYTES:
            return None, True
        return p.read_text(errors="replace"), False
    except (FileNotFoundError, IsADirectoryError, OSError):
        return None, False


HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def parse_hunks(diff_text):
    lines = diff_text.splitlines()
    hunks = []
    i = 0
    while i < len(lines):
        m = HUNK_RE.match(lines[i])
        if not m:
            i += 1
            continue
        old_start = int(m.group(1))
        old_len = int(m.group(2) or "1")
        new_start = int(m.group(3))
        new_len = int(m.group(4) or "1")
        i += 1
        old_side, new_side = [], []
        old_ln, new_ln = old_start, new_start
        while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("diff --git"):
            l = lines[i]
            if l.startswith("\\ No newline"):
                i += 1
                continue
            if l.startswith(" "):
                old_side.append({"ln": old_ln, "type": "ctx", "text": l[1:]})
                new_side.append({"ln": new_ln, "type": "ctx", "text": l[1:]})
                old_ln += 1
                new_ln += 1
            elif l.startswith("-"):
                old_side.append({"ln": old_ln, "type": "del", "text": l[1:]})
                old_ln += 1
            elif l.startswith("+"):
                new_side.append({"ln": new_ln, "type": "add", "text": l[1:]})
                new_ln += 1
            i += 1
        hunks.append(
            {
                "oldStart": old_start,
                "oldLines": old_len,
                "newStart": new_start,
                "newLines": new_len,
                "old": old_side,
                "new": new_side,
            }
        )
    return hunks


def is_binary_diff(diff_text):
    # anchor to line starts: a text file that merely mentions "Binary files"
    # (like this skill's own SKILL.md) must not be mistaken for a binary diff
    return any(l.startswith(("Binary files ", "GIT binary patch")) for l in diff_text.splitlines())


def build_modified_or_deleted(root, path, change_type):
    r = run(["diff", "-U3", "HEAD", "--", path], cwd=root)
    diff_text = r.stdout
    binary = is_binary_diff(diff_text)

    old_content = show_head(root, path)
    if change_type == "deleted":
        new_content, new_truncated = None, False
    else:
        new_content, new_truncated = read_working(root, path)

    hunks = [] if binary else parse_hunks(diff_text)
    for idx, h in enumerate(hunks):
        h["id"] = f"h{idx}"

    additions = sum(1 for h in hunks for l in h["new"] if l["type"] == "add")
    deletions = sum(1 for h in hunks for l in h["old"] if l["type"] == "del")

    return {
        "path": path,
        "changeType": change_type,
        "binary": binary,
        "additions": additions,
        "deletions": deletions,
        "oldContent": old_content,
        "newContent": new_content,
        "oldTruncated": False,
        "newTruncated": new_truncated,
        "hunks": hunks,
    }


def build_added(root, path):
    content, truncated = read_working(root, path)
    binary = False
    if content is not None and "\x00" in content:
        binary = True
        content = None
    lines = content.splitlines() if content is not None else []
    new_side = [{"ln": i + 1, "type": "add", "text": t} for i, t in enumerate(lines)]
    hunk = {
        "id": "h0",
        "oldStart": 0,
        "oldLines": 0,
        "newStart": 1,
        "newLines": len(lines),
        "old": [],
        "new": new_side,
    }
    return {
        "path": path,
        "changeType": "added",
        "binary": binary,
        "additions": len(lines),
        "deletions": 0,
        "oldContent": None,
        "newContent": content,
        "oldTruncated": False,
        "newTruncated": truncated,
        "hunks": [] if binary or not lines else [hunk],
    }


def main():
    argv = sys.argv[1:]
    out_path = None
    restrict_paths = None
    if "--paths" in argv:
        idx = argv.index("--paths")
        restrict_paths = set(argv[idx + 1:])
        argv = argv[:idx]
    if argv:
        out_path = argv[0]

    root = repo_root()
    entries = porcelain_entries(root)
    if restrict_paths is not None:
        entries = [e for e in entries if e[2] in restrict_paths]
    files = []
    for code, old_path, path in entries:
        # ignore this skill's own scratch/output artifacts if ever run inside itself
        change_type = classify(code)
        try:
            if change_type == "added":
                files.append(build_added(root, path))
            else:
                files.append(build_modified_or_deleted(root, path, change_type))
        except Exception as e:  # keep going even if one file is odd (submodule, symlink, etc.)
            files.append(
                {
                    "path": path,
                    "changeType": change_type,
                    "binary": True,
                    "additions": 0,
                    "deletions": 0,
                    "oldContent": None,
                    "newContent": None,
                    "oldTruncated": False,
                    "newTruncated": False,
                    "hunks": [],
                    "error": str(e),
                }
            )

    data = {
        "generatedAt": subprocess.run(
            ["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True
        ).stdout.strip(),
        "repo": Path(root).name,
        "files": files,
    }

    out = json.dumps(data, indent=None, separators=(",", ":"))
    if out_path:
        Path(out_path).write_text(out)
    else:
        print(out)


if __name__ == "__main__":
    main()
