# Mermaid diagram syntax quick reference

Pick the type by content shape (see the table in SKILL.md), then use the minimal syntax below.
Keep labels short; put detail in the walkthrough text, not crammed into node labels.

---

## Flowchart — process, hierarchy, cause/effect

```mermaid
flowchart TD
  A[Start] --> B{Decision?}
  B -->|yes| C[Do X]
  B -->|no| D[Do Y]
  C --> E[End]
  D --> E
```

- `TD` (top-down) for sequential/hierarchical reading order; `LR` for wide/parallel structures.
- Shapes: `[Rectangle]` a step, `{Diamond}` a decision, `([Rounded])` a start/end,
  `((Circle))` a small terminal node, `[[Subroutine]]` a call-out to another process.
- Label every edge that isn't an obvious "then": `-->|calls|`, `-->|depends on|`.
- Group related nodes with `subgraph Name ... end` when a diagram spans distinct zones (e.g.
  "Client" vs "Server").

## Sequence diagram — interactions over time between actors/systems

```mermaid
sequenceDiagram
  participant U as User
  participant S as Server
  U->>S: request(payload)
  S-->>U: response(200, data)
  Note over S: validates payload first
```

- `->>` solid arrow = a call/request; `-->>` dashed = a response/return.
- Use `Note over X` / `Note over X,Y` to attach a fact that doesn't fit as a message.
- Use `alt`/`else`/`end` for branching interactions, `loop`/`end` for repetition.

## State diagram — lifecycle / status transitions

```mermaid
stateDiagram-v2
  [*] --> Draft
  Draft --> InReview: submit
  InReview --> Approved: approve
  InReview --> Draft: request changes
  Approved --> [*]
```

- `[*]` marks start/end.
- Label every transition with the trigger/event that causes it.

## ER diagram — entities and relationships (data model, system components)

```mermaid
erDiagram
  USER ||--o{ ORDER : places
  ORDER ||--|{ LINE_ITEM : contains
```

- Cardinality tokens: `||` exactly one, `o{` zero-or-many, `|{` one-or-many, `o|` zero-or-one.
- Use for genuine entity-relationship content (data models, ownership structures) — not as a
  generic substitute for a flowchart.

## Timeline — chronology / history

```mermaid
timeline
  title Project history
  2023 : Initial design
  2024 : v1 launch : first customers
  2025 : v2 rewrite
```

- One section per time point; multiple events at the same point are colon-separated.

## Mindmap-style hierarchy (when a nested outline works better than a tree flowchart)

```mermaid
mindmap
  root((Topic))
    Branch A
      Detail 1
      Detail 2
    Branch B
      Detail 3
```

- Good for taxonomies/categorizations where the "flow" framing of a flowchart feels forced.

## When not to use Mermaid at all

- **Comparisons across items on shared dimensions** → a plain Markdown table almost always beats
  a diagram.
- **Pure prose argument (claim + support)** → a nested bullet outline is more faithful than
  bending it into boxes and arrows.
- **Real quantitative data** (measurements, trends) → don't fake a chart in Mermaid; either use a
  table or, if a real chart is warranted, follow the `dataviz` skill's guidance.
