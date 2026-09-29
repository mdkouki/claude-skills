#!/usr/bin/env python3
"""
Merge the LLM's triage (classification.json) into review-data.json so the
page, the summary builder and the apply step all read one file.

Usage: merge_classification.py <review-data.json> <classification.json>

classification.json shape (written by the LLM):
{
  "items": {
    "<path>::<hunkId>": {            // one entry per hunk of a modified file
      "importance": "important" | "minor",
      "reasons":   ["behavior" | "architecture" | "side-effect", ...],  // important only
      "title":     "short label, ~8 words",
      "rationale": "one line: why this classification",
      "llmDecision": "accept" | "reject",   // minor only
      "llmWhy":      "one line: why the LLM decided that"   // minor only
    },
    "<path>": { ... }                // one entry for an added/deleted file
  }
}

Fail-safe: any item the LLM did not classify (or classified with junk values)
becomes `important` with reason "unclassified", so nothing is ever waved
through unseen. A minor item without a valid llmDecision also becomes
important. The result is written back into review-data.json in place: every
hunk (and every added/deleted file) gains a `cls` object.

Prints a short JSON report (counts + which items fell back to important).
"""
import json
import sys
from pathlib import Path

REASONS = {"behavior", "architecture", "side-effect"}


def normalize(entry, fallback_title):
    if not isinstance(entry, dict):
        return None
    title = str(entry.get("title") or fallback_title)[:120]
    rationale = str(entry.get("rationale") or "")
    if entry.get("importance") == "minor":
        if entry.get("llmDecision") not in ("accept", "reject"):
            return None
        return {
            "importance": "minor",
            "reasons": [],
            "title": title,
            "rationale": rationale,
            "llmDecision": entry["llmDecision"],
            "llmWhy": str(entry.get("llmWhy") or ""),
        }
    if entry.get("importance") == "important":
        reasons = [r for r in entry.get("reasons", []) if r in REASONS]
        return {
            "importance": "important",
            "reasons": reasons or ["unclassified"],
            "title": title,
            "rationale": rationale,
        }
    return None


def fallback(title):
    return {
        "importance": "important",
        "reasons": ["unclassified"],
        "title": title,
        "rationale": "Not classified by the LLM — treated as important so it gets a human look.",
    }


def main():
    if len(sys.argv) != 3:
        print("usage: merge_classification.py <review-data.json> <classification.json>", file=sys.stderr)
        sys.exit(1)

    data_path = Path(sys.argv[1])
    data = json.loads(data_path.read_text())
    items = json.loads(Path(sys.argv[2]).read_text()).get("items", {})

    fell_back = []
    counts = {"important": 0, "minor": 0}

    def resolve(key, title):
        cls = normalize(items.get(key), title)
        if cls is None:
            fell_back.append(key)
            cls = fallback(title)
        counts[cls["importance"]] += 1
        return cls

    for f in data["files"]:
        if f.get("binary") or f.get("error"):
            continue
        if f["changeType"] in ("added", "deleted"):
            f["cls"] = resolve(f["path"], f"{f['changeType']} {f['path']}")
            continue
        for h in f["hunks"]:
            h["cls"] = resolve(f"{f['path']}::{h['id']}", f"{f['path']} {h['id']}")

    data_path.write_text(json.dumps(data))
    print(json.dumps({"counts": counts, "fellBackToImportant": fell_back}, indent=2))


if __name__ == "__main__":
    main()
