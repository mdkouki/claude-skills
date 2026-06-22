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
└── chameleon/
    └── SKILL.md
```

Each skill is a self-contained folder. More skills will be added here over time.

---

## Contributing

Issues and PRs are welcome. If you find a pattern Chameleon misses or a language/framework it doesn't classify correctly, open an issue with an example.

---

## License

MIT — see [LICENSE](./LICENSE).
