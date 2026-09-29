---
name: review-changes
description: >
  A smart review board for the code changes made during the current session,
  served entirely from localhost (no cloud, no upload of the diff anywhere).
  The LLM first triages every change: IMPORTANT ones (they change behavior,
  change architecture, or have a side effect) go to the user for an explicit
  decision as side-by-side old → new diffs; MINOR ones (renames, formatting,
  comments, behavior-preserving refactors) are pre-reviewed and decided by the
  LLM, and the user may optionally flip any of those decisions. Once every
  change has a decision, the LLM writes a table (short title + decision per
  change) and the user gives a final green light (apply) or red light (reject
  every modification). Use this after finishing an implementation task, before
  the user commits, instead of making them read a raw diff. Triggers include
  "/review-changes", "let me review this visually", "show me a visual diff",
  "open a review page for these changes", or any request to review AI-made
  edits the way a pull request would be reviewed. Decisions are applied at hunk
  granularity — reverting only the rejected parts, keeping the rest — without
  touching git (no add/commit/checkout/reset), so the user still stages and
  commits everything themselves.
---

# Review changes — the review board

Entirely local: `git diff` data → **LLM triage** (important vs. minor) →
**board page** (user decides important changes, may veto/flip minor ones;
the page closes on submit) → **LLM-written decision table in the terminal** →
**green/red light, asked in the terminal** → decisions applied to disk. The diff never leaves the machine — a Python stdlib HTTP server bound to
`127.0.0.1` and the user's own browser pointed at it.

## When to use this

Offer it once you've finished a chunk of implementation work and before the
user is expected to commit — "Want to run these changes through the review
board before we wrap up?" Don't force it; if the user says no or just says
"looks good", proceed normally. Also invoke directly when the user asks by name.

Set `<scratchpad>` to the session scratchpad directory. Delete any stale
`decisions.json` there before starting.

## Step 1 — Know exactly which files you touched

Only review files *you* edited or created in this session, not incidental
uncommitted changes already sitting in the repo. Keep a list of paths as you go
(every `Edit`/`Write` call) and use that explicit list — don't rely on
`git status` picking up "everything uncommitted."

## Step 2 — Extract the diff data (read-only)

```
python3 <skill_dir>/scripts/build_review_data.py <scratchpad>/review-data.json --paths <file1> <file2> ...
```

Only runs `git status`/`git diff`/`git show`. Classifies each file as
`modified` / `added` / `deleted` and breaks text diffs into hunks (ids `h0`,
`h1`, … per file). If `files` is empty, tell the user there's nothing to review
and stop.

## Step 3 — Triage every change (this is your job, not a script's)

Read `review-data.json` and write `<scratchpad>/classification.json`, one entry
per hunk of a modified file (key `"<path>::<hunkId>"`) and one entry per
added/deleted file (key `"<path>"`). Binary files are skipped.

```json
{ "items": {
  "src/pay.py::h0": { "importance": "important", "reasons": ["behavior"],
      "title": "Retry failed charges 3 times", "rationale": "A failed charge used to raise immediately." },
  "src/pay.py::h1": { "importance": "minor", "title": "Rename tmp to charge_result",
      "rationale": "Local variable rename, no behavior change.",
      "llmDecision": "accept", "llmWhy": "Clearer name, all usages updated." }
} }
```

**Important** = the change does at least one of:
- `behavior` — alters what the code does for some input, output, condition,
  default, error path, or public contract;
- `architecture` — adds/removes/moves a module, layer, dependency, interface,
  or shifts a responsibility;
- `side-effect` — touches I/O, network, database, filesystem, global/shared
  state, config, env, permissions, scheduling, or deletes something.

**Minor** = none of the above: renames of locals, formatting/whitespace,
comments and docs, import ordering, dead-code removal that provably changes
nothing, behavior-preserving refactors, typo fixes in strings nobody parses.

Rules:
- **When in doubt, important.** A false alarm costs a click; a hidden
  behavior change costs trust. Anything you can't classify falls back to
  important automatically.
- **Never auto-reject an important change** — only minor ones get an
  `llmDecision`. For minor ones, actually review them: `accept` if correct and
  consistent with the surrounding code, `reject` if sloppy, redundant,
  out-of-scope churn, or a mistake. `llmWhy` is one honest line.
- `title` is short (~8 words), states the *change*, not the file.
- If a "minor" hunk is entangled with an important one (e.g. the rename only
  makes sense because of the new behavior), classify it important.

Then merge it in:

```
python3 <skill_dir>/scripts/merge_classification.py <scratchpad>/review-data.json <scratchpad>/classification.json
```

It prints counts and lists any item that fell back to important — fix your
classification if that list isn't empty by accident.

## Step 4 — Build the page and serve it

```
python3 <skill_dir>/scripts/build_review_page.py <skill_dir>/assets/template.html <scratchpad>/review-data.json <scratchpad>/review.html
python3 <skill_dir>/scripts/serve_review.py <scratchpad>/review.html <scratchpad>/decisions.json <scratchpad>/server.url
```

Always build with the script, never hand-splice the JSON (diff data can contain
a literal `</script>` that would blank the page). Run `serve_review.py` with
`run_in_background: true`: it binds `127.0.0.1` only, writes its URL to
`server.url`, opens the browser, and blocks until the user submits.

Tell the user the board opened (give the URL from `server.url`) and how it
works: the **Important** tab lists changes that need their decision (Submit
stays disabled until each one is decided); the **Minor** tab shows Claude's
pre-made decisions, which they can ignore or flip; **Files** shows one file at
a time with a full-file toggle.

## Step 5 — Wait for the submission

The server exits on its own as soon as the user clicks **Submit review** (the
page then closes itself, or tells the user to come back to the terminal). The
background task's completion notification is the signal — don't poll. Then
`decisions.json` exists in `<scratchpad>`.

## Step 6 — Write the decision table, then ask for the final light

```
python3 <skill_dir>/scripts/build_summary.py <scratchpad>/review-data.json <scratchpad>/decisions.json
```

Prints one row per change — your short title, importance, final decision, and
who decided (Claude, or the user, with an override flag).

**Copy the whole table into your own reply text.** The script's output is a
tool result, which the user usually does not see — a message that merely says
"here's the table" shows them nothing. Only after the table is visible in your
message, ask for the final light with `AskUserQuestion`: **Green light** (apply
the table) or **Red light** (reject every modification).

## Step 7 — Apply the final light

- **Green** → apply the table:
  ```
  python3 <skill_dir>/scripts/apply_review.py <scratchpad>/review-data.json <scratchpad>/decisions.json <repo_root>
  ```
- **Red** → reject every modification:
  ```
  python3 <skill_dir>/scripts/apply_review.py <scratchpad>/review-data.json <scratchpad>/decisions.json <repo_root> --reject-all
  ```

`apply_review.py` only reads/writes plain files (and may delete a rejected new
file or restore a rejected deletion). It never calls git. It prints a JSON
summary of what was kept, reverted, partially reverted, restored, or deleted.
Read it back in one or two sentences, file by file; flag any partially
reverted file so the user double-checks it.

## Notes

- Never run `git add`, `git commit`, `git checkout`, `git reset`, or any other
  mutating git command anywhere in this flow — steps 2 and 7 are read-only git
  / plain-filesystem operations only.
- Decision precedence: user click > Claude's minor-change verdict. Important
  changes have no default — the page won't let the user submit until each has
  an explicit decision.
- A hunk or file missing from `decisions.json` is treated as **accepted** by
  `apply_review.py` (keep what was written) rather than silently reverting
  something nobody looked at.
- If the user wants changes that aren't a clean per-hunk revert ("keep the
  idea but write it differently"), don't force it through approve/reject —
  make the edit normally after applying the decision.
