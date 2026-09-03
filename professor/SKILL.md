---
name: professor
description: >
  Digest a specific piece of input — selected text, pasted content, one or more files, a paper,
  a spec, a transcript, a codebase excerpt — and turn it into a faithful, simplified explanation
  with diagrams. Every diagram element must trace back to something actually in the source; the
  goal is to compress and clarify without silently dropping information. Triggers include
  "/professor", "digest this", "summarize this into a diagram", "turn this into a mermaid
  diagram", "give me a resume of this", "break this down visually", "map this out", "diagram
  this document/file/selection", "explain this text/file simply", or any request to condense a
  concrete piece of supplied content into a summary-plus-diagram. Unlike a general "explain X"
  request (which draws on background knowledge of a topic), Professor always starts from content
  the user hands over — a selection, file(s), or pasted text — and is graded on fidelity to that
  content, not on general clarity alone.
---

# Professor 🎓

Professor takes something concrete the user handed over — a selection, a file, a folder, a
transcript, a spec — and produces two things together: a **resume** (plain-language digest) and
one or more **diagrams**, chosen to match the actual shape of the content. The standard to hold
throughout: a reader should come away *both* simpler and *not missing anything that mattered* in
the source. Simplification is a compression job, not a lossy one — if something gets cut for
clarity, say so explicitly rather than silently dropping it.

This is different from general "explain X" requests: Professor never reasons from background
knowledge about the topic. Every node, edge, and claim must be traceable to the actual input.

---

## Phase 1 — Identify and ingest the input

Figure out what was actually handed over before doing anything else:

- **Selected/pasted text** — work with it directly, in full.
- **A single file** — read it in full unless it is very large (see below).
- **Multiple files / a folder** — read each file; if the set is large, triage by relevance to
  what the user is asking to understand (don't silently skip files without saying so).
- **Something huge** (a long paper, a big log, a large codebase slice) — do not skim silently.
  Either: (a) chunk it and digest section by section, carrying forward a running outline, or
  (b) tell the user you're sampling and say which parts, so no one mistakes a partial read for
  a complete one.

State back, in one line, what you understood the scope to be ("Digesting `auth/*.py` (4 files,
~600 lines)" or "Digesting the pasted RFC excerpt"). If the scope is ambiguous (e.g. user says
"this" with nothing clearly selected), ask rather than guess.

---

## Phase 2 — Digest: find the shape of the content

Before picking a diagram, identify what *kind* of structure the content actually has. Most
inputs are dominantly one of these shapes (a long input can be more than one — that's fine, it
just means more than one diagram):

| Shape | Signal in the text | Best diagram |
|---|---|---|
| Sequential process / algorithm / procedure | steps, "first/then/finally", numbered instructions | `flowchart` (TD or LR) |
| Interaction over time between actors/systems | requests/responses, messages, API calls, a dialogue/transcript | `sequenceDiagram` |
| State machine / lifecycle | statuses, transitions, "becomes", "moves to", triggers | `stateDiagram-v2` |
| Hierarchy / taxonomy / org structure | parent-child, categories, "is a kind of", nesting | `flowchart TD` (tree shape) or a mindmap-style nested outline |
| Entities & relationships | nouns with attributes and connections (data model, system architecture, cast of characters) | `erDiagram` or `flowchart` with labeled edges |
| Timeline / history | dates, chronology, "before/after", versions over time | `timeline` or a simple ordered flowchart |
| Cause → effect chains | "because", "leads to", "as a result", dependency chains | `flowchart` with directional causal edges |
| Comparison across items | multiple things sharing dimensions (pros/cons, feature matrix) | a **table** — do not force a comparison into a diagram |
| Numeric/quantitative data | measurements, counts, trends | a table, or defer to the `dataviz` skill's guidance if a real chart is warranted |
| Argument / claims and support | thesis + supporting points + evidence | nested outline (bullets), diagram optional |

If nothing above fits cleanly, don't force a diagram — a well-structured outline or table that
stays faithful beats a diagram that distorts the content to look diagram-shaped.

---

## Phase 3 — Extract faithfully

Before drawing anything, build a short internal fact list: each node or edge you intend to draw,
with the piece of source it comes from (a quote, a line, a section). This is the fidelity check —
if you can't point to where something came from, it doesn't go in the diagram.

- **Never invent a relationship, step, or entity** that isn't stated or very directly implied by
  the source. If you're inferring something not explicit, mark it distinctly (e.g. a dashed edge
  or a `(inferred)` label) rather than presenting it as fact.
- **Don't over-collapse distinct things into one node** just to make the diagram tidier — that's
  the kind of loss this skill exists to avoid. If two steps are genuinely different, keep them
  different, even if it costs a little visual economy.
- **Do collapse genuine repetition** (e.g. 8 near-identical validation steps) into one
  representative node, but say in the caption that it's a representative collapse and how many
  instances it stands for.
- **Keep terminology from the source** where it's meaningful (proper nouns, named steps, specific
  values) rather than genericizing it away — genericizing precise terms is a common way clarity
  work quietly loses information.

---

## Phase 4 — Build the diagram(s)

- **Prefer Mermaid** — it renders inline in chat and in artifacts. Reach for the reference sheet
  at `references/diagram-syntax.md` for exact syntax across flowchart, sequence, state, ER,
  timeline, and mindmap-style diagrams.
- **Cap complexity per diagram at roughly 12–15 nodes.** If the content is bigger than that,
  split into an **overview diagram** (the big shape, few nodes) plus **zoom-in diagrams** for the
  parts that need detail — don't cram everything into one cluttered graph.
- **Label edges with what actually connects the nodes** (not just arrows) — "validates", "calls",
  "becomes", "depends on" — a diagram with unlabeled arrows usually means the relationships
  weren't actually pinned down yet.
- **Match diagram direction to reading order** where there is one (top-down for hierarchies and
  sequential processes are usually clearer as `TD`; wide/parallel structures often read better
  `LR`).
- If the true fidelity of the content resists a single diagram (e.g. it's simultaneously a
  hierarchy and a timeline), produce **two small diagrams**, each faithful to one dimension,
  rather than one diagram straining to show both.

---

## Phase 5 — Compose the output

Always produce these parts, in this order:

### 1. Resume
A tight plain-language digest — a short paragraph or a few bullets. This is the "what this
actually says" layer: someone who reads only this should have the accurate gist, not a vague
gloss. State the source's own conclusions/claims, not your opinion of them.

### 2. Diagram(s)
Each diagram gets a one-line caption saying what it shows and, if relevant, what it deliberately
simplifies (e.g. "collapses 8 retry attempts into one representative node — see Fidelity notes").

### 3. Walkthrough
A short explanation that walks the diagram, tying each part back to something specific in the
source (quote, section, line, file). This is what lets the reader verify the diagram against the
original rather than trust it blindly.

### 4. Fidelity notes
A short, explicit list: what was compressed, collapsed, or left out of the diagram for clarity,
and where in the source the fuller detail lives. This section is what makes "simplification
without losing information" actually true — the information isn't lost, it's one section away.
If nothing was cut, say so plainly instead of omitting the section.

---

## When to publish instead of answering inline

Default to answering directly in the chat — Mermaid renders there and that's usually the fastest
loop. Only reach for a published Artifact if the user asks for something shareable, or the
content genuinely warrants a multi-diagram reference page. If you do, load `artifact-design`
first (and `artifact-diagramming` if hand-drawn SVG diagrams are more appropriate than Mermaid for
the artifact) — don't skip straight to writing HTML.

---

## Guardrails

- **Fidelity over elegance.** A faithful, slightly less pretty diagram beats a clean one that
  quietly reshapes the source to fit.
- **No hallucinated structure.** If the source is messy or doesn't have a clean shape, say that,
  and show the closest honest approximation rather than manufacturing tidiness.
- **Don't diagram what's better as a table**, and don't tabulate what's better as a diagram —
  pick per Phase 2, not by default habit.
- **Always include the Fidelity notes section.** It's the part that keeps this skill honest.
- **Scale the output to the input.** A three-paragraph selection doesn't need five diagrams and a
  10-section report; give it a resume and one small diagram.
