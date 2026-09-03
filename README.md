# claude-skills

A collection of Claude skills — modular instruction sets that extend Claude's capabilities across Claude Code, Cursor, Windsurf, and any agent that supports the [Agent Skills](https://agentskills.io) open standard.

Install any skill with a single command:

```bash
npx openskills install mdkouki/claude-skills/chameleon
```

---

## Skills

### 🦎 Chameleon

> Reverse-engineer a codebase's conventions and produce a ready-to-commit `CONVENTIONS.md`.

Point Chameleon at any project and it reads the source to surface everything a new developer needs to know — the rules the team never wrote down, and the ones they did.

**What it detects:**

| Category | What you get |
|---|---|
| Formatting & code style | Indentation (spaces/tabs/width), line length, quotes, semicolons, trailing commas, brace style, import ordering, file naming |
| Naming conventions | Classes, functions, variables, constants, interfaces, DB tables/columns, test files |
| Design patterns | Repository, Service layer, Factory, Strategy, Observer, CQRS, Dependency Injection — with concrete file references |
| SQL & data access | Query location, ORM vs raw vs query builder, parameterisation, transactions, migrations, N+1 awareness |
| Decoupling & architecture | Layer boundaries, dependency direction, module structure, cross-cutting concerns |
| Error handling | Strategy, custom error types, propagation, logging style |
| Testing | File location, naming, scope (unit/integration/E2E), mocking strategy, fixtures |
| Convention over Configuration | Rated Heavy CoC / Balanced / Config-first, with evidence for each dimension |

**Coverage modes** — controls how many files are sampled per layer:

| Mode | How to trigger | Files per stratum |
|---|---|---|
| Quick | `"quick scan"` / `"fast"` | max 5 |
| Standard | default (say nothing) | max 10 |
| Deep | `"deep"` / `"full audit"` | max 20 |
| Custom | `"cover 40%"` | `N × target%` |
| Focused | `"focus deep on services"` | Deep on named strata only |

**Output:** a structured `CONVENTIONS.md` with a sampling coverage table, per-finding confidence markers (✅ ⚠️ 🔍), and a Quick-Reference Card of the top 10 rules for new developers.

**Install:**

```bash
npx openskills install mdkouki/claude-skills/chameleon
```

**Or install globally:**

```bash
npx openskills install mdkouki/claude-skills/chameleon --global
```

**Trigger phrases:**

```
analyse the conventions of this project
run chameleon
what design patterns does this codebase use?
generate a CONVENTIONS.md
deep audit of this project
quick scan, what's the code style here?
cover 40% and generate conventions
```

---

### 🦅 Falcon

> Fast, precise unit test generation that fills real coverage gaps — nothing more, nothing less.

Point Falcon at a package, a file, or nothing at all (it defaults to your uncommitted diff) and it audits what's untested before writing a single test.

**What it does:**

| Step | What happens |
|---|---|
| Scope detection | Named target, or `git diff` / `git status` when none is given |
| Language & framework detection | Jest/Vitest, pytest, JUnit, NUnit/xUnit, go test, RSpec, XCTest, Cargo tests — auto-detected from project files |
| Coverage audit | Cross-references source symbols against existing test files, reports gaps before generating anything |
| Test generation | AAA structure, one concern per test, mocked I/O, boundary/error/null cases, matches existing project style |
| Quality self-check | Verifies each test would fail if the implementation were deleted, has no real I/O, and follows framework conventions |

**Install:**

```bash
npx openskills install mdkouki/claude-skills/falcon
```

**Trigger phrases:**

```
write unit tests for this
check for missing test coverage
scan my uncommitted changes for untested code
generate test cases for src/auth
what needs testing here?
```

---

### 🦉 Owl

> Explain any technical concept the wise-owl way — plain language first, jargon defined on contact, depth pushed to curated links.

Ask Owl about anything technical and it always follows the same arc: an essence sentence with an analogy, a jargon-free definition and the problem it solves, 2–4 concrete recognizable examples, a Mermaid diagram showing how it fits among the components around it, then a short list of hand-searched, verified links for going deeper.

**Install:**

```bash
npx openskills install mdkouki/claude-skills/owl
```

**Trigger phrases:**

```
what is OAuth?
explain how a load balancer works
ELI5 event sourcing
help me understand CRDTs
break down how DNS resolution works
```

---

### 🎓 Professor

> Digest a specific selection, file, or document and turn it into a faithful resume plus diagrams — simplified, never lossy.

Unlike Owl (which explains a general topic from background knowledge), Professor always starts from something concrete the user hands over. It identifies the content's actual shape — process, sequence, state machine, hierarchy, entity relationships, timeline, cause/effect, comparison, argument — picks the diagram type that matches (Mermaid flowchart, sequence, state, ER, timeline, or a table/outline when a diagram would distort the content), and every node or edge it draws must trace back to something explicit in the source.

**Output:** a Resume, one or more diagrams (capped at ~12–15 nodes each, split into overview + zoom-ins when the content is bigger), a Walkthrough tying the diagram back to the source, and a Fidelity notes section listing anything compressed or collapsed for clarity — so nothing is silently lost.

**Install:**

```bash
npx openskills install mdkouki/claude-skills/professor
```

**Trigger phrases:**

```
digest this file
summarize this into a diagram
turn this into a mermaid diagram
give me a resume of this
map this out
diagram this document
```

---

## Installation

Requires [Node.js](https://nodejs.org/) 20.6+ and Git.

```bash
# Install a skill (project-local, default)
npx openskills install mdkouki/claude-skills/chameleon

# Install globally (available in all projects)
npx openskills install mdkouki/claude-skills/chameleon --global

# Install for non-Claude agents (Cursor, Windsurf, Aider…)
npx openskills install mdkouki/claude-skills/chameleon --universal

# Sync your AGENTS.md after installing
npx openskills sync
```

**Manual install (no CLI):**

```bash
git clone https://github.com/mdkouki/claude-skills.git
cp -r claude-skills/chameleon ~/.claude/skills/
```

---

## Repo structure

```
claude-skills/
├── README.md
├── LICENSE
├── chameleon/
│   └── SKILL.md
├── falcon/
│   ├── SKILL.md
│   └── references/
├── owl/
│   └── SKILL.md
└── professor/
    ├── SKILL.md
    └── references/
```

Each skill is a self-contained folder. More skills will be added here over time.

---

## Contributing

Issues and PRs are welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md) for how to add a new skill or report a pattern one of the existing skills gets wrong.

---

## License

MIT — see [LICENSE](./LICENSE).
