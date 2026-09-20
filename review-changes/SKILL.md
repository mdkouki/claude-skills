---
name: review-changes
description: >
  Opens a visual, side-by-side review of the code changes made during the current
  session — a page served entirely from localhost (no cloud, no upload of the
  diff anywhere) with a file tree of everything touched, an old-block
  arrow-new-block diff view per hunk (with a toggle to see the full file for
  context), and approve/reject controls at the hunk, file, or whole-review level.
  Use this after finishing an implementation task, before the user commits, to
  offer them a merge-request-style review instead of reading a raw diff in the
  terminal. Triggers include "/review-changes", "let me review this visually",
  "show me a visual diff", "open a review page for these changes", or any request
  to review AI-made edits the way a pull request would be reviewed. After the user
  submits their decisions on the page, this skill reads them back and applies
  approve/reject at hunk granularity — reverting only the rejected parts, keeping
  the rest — without touching git (no add/commit/checkout/reset), so the user
  still stages and commits everything themselves.
---

# Review changes

A merge-request-style visual review for AI-made edits, entirely local: file
tree → per-hunk old-block/new-block diff with a connecting arrow →
approve/reject at hunk, file, or global level → decisions read back over
localhost and applied to disk. The diff content never leaves the machine —
no claude.ai artifact, no cloud storage, just a Python stdlib HTTP server
bound to `127.0.0.1` and the user's own browser pointed at it.

## When to use this

Offer it once you've finished a chunk of implementation work and before the
user is expected to commit — "Want to review these changes visually before we
wrap up?" Don't force it; if the user says no or just says "looks good",
proceed normally. Also invoke directly when the user asks by name or asks to
review changes visually.

## Step 1 — Know exactly which files you touched

Only review files *you* edited or created in this session, not incidental
uncommitted changes already sitting in the repo. Keep a mental list of paths
as you go (every `Edit`/`Write` call), and use that explicit list — don't rely
on `git status` picking up "everything uncommitted."

## Step 2 — Extract the diff data (read-only)

```
python3 <skill_dir>/scripts/build_review_data.py <scratchpad>/review-data.json --paths <file1> <file2> ...
```

This only runs `git status`/`git diff`/`git show` — never mutates anything.
It classifies each file as `modified` / `added` / `deleted`, and for text
files breaks the diff into hunks with old-side and new-side line arrays
(context lines appear on both sides). Binary files and files over ~300KB skip
inline content but are still listed.

If the resulting `files` array is empty, tell the user there's nothing to
review (no uncommitted changes in the files you touched) and stop here.

## Step 3 — Build the review page

```
python3 <skill_dir>/scripts/build_review_page.py <skill_dir>/assets/template.html <scratchpad>/review-data.json <scratchpad>/review.html
```

Always use this script rather than hand-splicing the JSON into the template.
The diff data can itself contain literal `</script>` text (e.g. when
reviewing an HTML/JS file), which would otherwise truncate the page's own
`<script>` block in the browser and silently blank the review — the script
escapes for that.

## Step 4 — Serve it locally and wait for the submission

```
python3 <skill_dir>/scripts/serve_review.py <scratchpad>/review.html <scratchpad>/decisions.json <scratchpad>/server.url
```

Run this with the Bash tool's `run_in_background: true` — it's a stdlib-only
HTTP server bound to `127.0.0.1` (never `0.0.0.0`, never reachable off the
machine), so nothing about the diff or the repo touches the network. It:

- writes the local URL to `<scratchpad>/server.url` and opens it in the
  user's default browser automatically,
- blocks while the page is open,
- on **Submit review**, writes the decision JSON to `<scratchpad>/decisions.json`
  and exits on its own.

You'll get a completion notification when it exits — that's the "the user
submitted" signal; don't poll for it. Tell the user the review page opened in
their browser (mention the URL from `server.url` in case the auto-open
didn't work) and briefly explain the controls: click a file on the left;
each hunk shows old → new with Approve/Reject; the view toggle switches to
the full file; global Approve all/Reject all and Submit review live in the
toolbar.

## Step 5 — Apply the decision (no git writes)

```
python3 <skill_dir>/scripts/apply_review.py <scratchpad>/review-data.json <scratchpad>/decisions.json <repo_root>
```

This only reads/writes plain files on disk (and can delete a rejected new
file). It never calls git — the user still stages and commits everything
themselves, per their own no-git-writes rule. It prints a JSON summary of
what was kept as-is, reverted, partially reverted, restored (a rejected
deletion), or deleted (a rejected new file).

Read the summary back to the user in one or two sentences: what was kept vs.
reverted, file by file. If a hunk was partially rejected inside a file, say
so explicitly so they know to double check that file.

## Notes

- Never run `git add`, `git commit`, `git checkout`, `git reset`, or any other
  mutating git command anywhere in this flow — steps 2 and 5 are read-only
  git / plain-filesystem operations only.
- A hunk or file missing from the decisions doc is treated as **accepted** —
  the page only needs to record overrides, but the scripts default safe (to
  "keep what was written") rather than silently reverting something the user
  never looked at.
- If the user wants changes to a file that isn't a clean per-hunk revert
  (e.g. "keep the idea but write it differently"), don't try to force that
  through the approve/reject mechanism — just make the edit normally after
  applying the decision.
