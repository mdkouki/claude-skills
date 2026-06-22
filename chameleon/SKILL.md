---
name: chameleon
description: >
  Analyse a codebase to detect and document its conventions — both explicit and hidden. Use this skill
  whenever the user wants to understand how a project is structured, what rules it follows, or wants to
  onboard into an unfamiliar codebase. Triggers include: "analyse my codebase", "what conventions does
  this project use", "reverse engineer the coding style", "what patterns are used here", "generate a
  CONVENTIONS.md", "what design patterns does this project follow", "how is this project organised",
  "detect code style", "understand this project's architecture", "run chameleon", or any request to
  document/discover how an existing project was built. Also trigger when a user uploads or points to
  source files and asks how the code is written, structured, or organised.
---

# Codebase Convention Analyser

Reverse-engineer a project's implicit and explicit conventions from its source code, then produce a
structured `CONVENTIONS.md` that a new developer could follow to contribute consistently.

---

## Phase 1 — Orient

Before reading any files, build a map of the project.

```bash
find . -type f | grep -v node_modules | grep -v .git | grep -v dist | grep -v __pycache__ \
  | sort | head -200
```

Also check for any existing convention/config files that give free information:

```bash
ls -1 .editorconfig .eslintrc* .prettierrc* pyproject.toml setup.cfg tslint.json \
       .flake8 .rubocop.yml phpcs.xml stylecop.json .stylelintrc* 2>/dev/null
```

And check for tool config inside package.json / composer.json / Cargo.toml etc.:
```bash
cat package.json 2>/dev/null | python3 -c "
import json,sys
d=json.load(sys.stdin)
for k in ['eslintConfig','prettier','stylelint','lint-staged']:
    if k in d: print(k,'->',json.dumps(d[k],indent=2))
" 2>/dev/null
```

From this, note:
- Primary language(s)
- Framework(s) in use
- Folder structure style (feature-based, layer-based, domain-based, flat)
- Whether a linter/formatter config already exists (if so, extract rules directly — do not guess)

---

## Phase 2 — Statistical Sampling

Conventions are only trustworthy when observed across a representative slice of the codebase, not
cherry-picked files. This phase applies stratified random sampling so every layer of the project
gets proportional coverage and no single cluster of files skews the findings.

---

### Step 2.0 — Determine coverage mode

**Before running anything**, check whether the user has specified a coverage level.

#### Recognised inputs

The user may say things like:
- `"quick scan"` / `"fast"` / `"rough idea"` → **Quick** mode
- `"standard"` / `"normal"` / `"default"` / no mention at all → **Standard** mode ← default
- `"deep"` / `"thorough"` / `"exhaustive"` / `"full audit"` → **Deep** mode
- `"30%"` / `"50%"` / `"cover at least 40%"` → **Custom** mode with explicit target
- `"focus deep on services"` / `"go deeper on tests"` → Standard overall, but override
  the named strata to Deep cap for that stratum only

If the user has not mentioned coverage, proceed with **Standard** mode silently — do not ask.
Only ask if the request is genuinely ambiguous about depth.

#### Coverage modes

| Mode | Formula per stratum | MAX cap | When to use |
|---|---|---|---|
| **Quick** | `max(2, ceil(sqrt(N) * 0.5))` | 5 files | Fast orientation, small projects, first impression |
| **Standard** | `max(3, ceil(sqrt(N)))` | 10 files | Default — good balance of speed and confidence |
| **Deep** | `max(5, ceil(sqrt(N) * 2))` | 20 files | Audits, onboarding docs, disputed conventions |
| **Custom %** | `max(3, ceil(N * target))` | N (all) | User specifies exact % e.g. `"cover 40%"` |

**Special strata that ignore the mode cap** (always read fully):
- `config` — always 100%; few files, information-dense
- `entry` — always 100%; they wire everything together
- `migration` — always first 2 + last 2 (chronological spread); if ≤ 4, read all

**Announce the mode** at the start of your response:

> 🦎 **Chameleon** — running in **Standard** mode (sqrt sampling, max 10 files/stratum).
> Say `quick`, `deep`, `cover 40%`, or `focus deep on <stratum>` to adjust.

---

### Step 2.1 — Census, sampling plan, and file selection (single pass)

Run the census, compute the sampling plan, select files, and output the final read list — all in
one script to eliminate round-trips:

```bash
python3 - << 'EOF'
import os, re, collections, json, math, hashlib

# --- Configuration (adjust MODE before running) ---
MODE           = "standard"   # quick | standard | deep | custom
CUSTOM_TARGET  = 0.40         # fraction, only used when MODE == "custom"
FOCUS_DEEP     = set()        # e.g. {"service", "test"} for per-stratum overrides

EXCLUDE = {
  'node_modules','.git','dist','build','__pycache__','.next',
  'vendor','coverage','.tox','.venv','venv','target','out',
  '.cache','*.min.js','*.min.css','*.lock','*.sum',
}

STRATA = [
  ('config',      r'(^|/)(\.[a-z]+rc|.*config\.[^/]+|.*\.toml|.*\.ini|.*\.yaml|.*\.yml|.*\.env.*)$'),
  ('test',        r'(test[s]?/|spec[s]?/|__test__|\.test\.|\.spec\.|_test\.|test_)'),
  ('migration',   r'(migrat|schema|seeds?/)'),
  ('entry',       r'(^|/)(main|index|app|server|bootstrap|cmd/[^/]+)\.[^/]+$'),
  ('model',       r'(model[s]?|entit|domain|schema[s]?)/'),
  ('repository',  r'(repo[s]?|repositor|dao|store[s]?|persist)/'),
  ('service',     r'(service[s]?|usecase[s]?|use.case[s]?|application)/'),
  ('controller',  r'(controller[s]?|handler[s]?|route[s]?|endpoint[s]?|view[s]?)/'),
  ('middleware',  r'(middleware[s]?|interceptor[s]?|filter[s]?|guard[s]?)/'),
  ('util',        r'(util[s]?|helper[s]?|shared|common|lib[s]?)/'),
  ('other',       r''),
]

SOURCE_EXT = {
  '.py','.js','.ts','.tsx','.jsx','.go','.rs','.java','.kt','.rb',
  '.php','.cs','.cpp','.c','.h','.swift','.scala','.ex','.exs','.vue',
  '.svelte','.toml','.yaml','.yml','.json','.env','.ini','.conf','.cfg',
}

ALWAYS_ALL       = {'config', 'entry'}
MIGRATION_SAMPLE = 4

# --- Helpers ---

def classify(path):
  for name, pattern in STRATA:
    if re.search(pattern, path, re.IGNORECASE):
      return name
  return 'other'

def should_exclude(path):
  parts = path.split('/')
  for ex in EXCLUDE:
    if any(p == ex or (ex.startswith('*') and p.endswith(ex[1:])) for p in parts):
      return True
  return False

def sample_size(stratum, N):
    if stratum in ALWAYS_ALL or N <= 2:
        return N
    if stratum == 'migration':
        return min(N, MIGRATION_SAMPLE)
    effective_mode = 'deep' if stratum in FOCUS_DEEP else MODE
    if effective_mode == 'quick':
        return min(5,  max(2, math.ceil(math.sqrt(N) * 0.5)))
    if effective_mode == 'standard':
        return min(10, max(3, math.ceil(math.sqrt(N))))
    if effective_mode == 'deep':
        return min(20, max(5, math.ceil(math.sqrt(N) * 2)))
    if effective_mode == 'custom':
        return min(N,  max(3, math.ceil(N * CUSTOM_TARGET)))
    return min(10, max(3, math.ceil(math.sqrt(N))))

def systematic_sample(files, n):
    files = sorted(files)
    N = len(files)
    if N <= n:
        return files
    step = N // n
    offset = int(hashlib.md5(files[0].encode()).hexdigest(), 16) % step
    return [files[(offset + i * step) % N] for i in range(n)]

def migration_sample(files):
    files = sorted(files)
    return files if len(files) <= 4 else files[:2] + files[-2:]

# --- Census ---

census = collections.defaultdict(list)
for root, dirs, files in os.walk('.'):
  dirs[:] = [d for d in dirs if not should_exclude(d)]
  for f in files:
    ext = os.path.splitext(f)[1].lower()
    if ext not in SOURCE_EXT:
      continue
    rel = os.path.relpath(os.path.join(root, f))
    if not should_exclude(rel):
      census[classify(rel)].append(rel)

# --- Sampling plan + file selection ---

plan_rows = []
selected = {}
total_pop = total_n = 0

for stratum in sorted(census.keys()):
    files = census[stratum]
    N = len(files)
    n = sample_size(stratum, N)
    pct = round(n / N * 100) if N else 0
    plan_rows.append((stratum, N, n, pct))
    total_pop += N
    total_n   += n
    if stratum == 'migration':
        selected[stratum] = migration_sample(files)
    else:
        selected[stratum] = systematic_sample(files, n)

# --- Output ---

print(f"\nSampling plan — mode: {MODE.upper()}")
print(f"{'stratum':<14} {'pop':>5} {'sample':>7} {'coverage':>9}")
print("-" * 40)
for stratum, N, n, pct in plan_rows:
    note = " <- all"  if stratum in ALWAYS_ALL else \
           " <- deep" if stratum in FOCUS_DEEP else ""
    print(f"{stratum:<14} {N:>5} {n:>7} {pct:>8}%{note}")
print("-" * 40)
total_pct = round(total_n / total_pop * 100) if total_pop else 0
print(f"{'TOTAL':<14} {total_pop:>5} {total_n:>7} {total_pct:>8}%")

print("\n--- SELECTED FILES (JSON) ---")
print(json.dumps(selected, indent=2))
EOF
```

Show the sampling plan table in your response. If overall coverage is below 10%, mention that
Deep mode would improve confidence. If above 60%, note that Standard or Quick would be faster.

---

### Step 2.2 — Read samples in parallel and record observations

**Issue all file reads in parallel.** For each stratum, fire off Read calls for every selected
file simultaneously — do not read files one at a time. Claude Code supports multiple tool calls
in a single response; use this to read all files across all strata in one batch.

If the total number of selected files exceeds what can be read in a single batch, group them
into batches of up to 15–20 parallel reads and issue each batch in a separate response.

Read budget per file (scales with mode):

| Stratum | Quick | Standard | Deep |
|---|---|---|---|
| entry, config | full file | full file | full file |
| model, repository, service | first 100 lines | first 160 lines | first 250 lines |
| controller, middleware | first 80 lines | first 120 lines | first 200 lines |
| test | first 60 lines | first 80 lines + `describe`/`beforeEach` blocks | first 120 lines |
| util, other | first 40 lines | first 60 lines | first 100 lines |

Record each observation with: stratum, file path, line range read, pattern noted.

---

### Step 2.5 — Compile coverage and confidence

Before Phase 3, compile the actual coverage table and embed it in your response.

Confidence thresholds:
- ✅ **High** — pattern seen in ≥ 60% of sampled files in that stratum
- ⚠️ **Medium** — seen in 30–59%
- 🔍 **Low** — seen in < 30%, or stratum coverage itself was < 15%

If confidence is low on an important stratum, suggest a targeted re-run:
> "Coverage on `service` was 15% (10/67 files). Run again with `deep` mode or say
> `focus deep on services` to raise confidence on that layer specifically."

---

## Phase 3 — Detect Each Convention Category

Work through each category below using only the files selected in Phase 2. For each finding:

- **Cite the evidence** — file path + line number or snippet.
- **Count occurrences** — "observed in 8/10 sampled service files" is a finding;
  "observed in 1 file" is a weak signal, note it as such.
- **Mark confidence** using the thresholds from Step 2.5.

Do not draw conclusions from a single file.

---

### 3.1 Formatting & Code Style

**Indentation**
- Count leading spaces on nested blocks across 5+ files. Is it 2, 4, or tabs?
- Check `.editorconfig` or formatter config first; if absent, infer from files.
- Note any inconsistencies (mixed tabs/spaces is itself a convention finding).

**Line length**
- Are lines generally under 80, 100, or 120 chars? Any wrapping patterns?

**Quotes**
- Single vs double quotes for strings. Any interpolation preference?

**Semicolons** (JS/TS)
- Always, never, or ASI-reliant?

**Trailing commas**
- Multi-line arrays/objects/params: trailing comma or not?

**Brace style**
- Same-line `{` vs new-line `{`? Allman vs K&R vs 1TBS?

**Blank lines**
- Between methods? Between logical sections within a method?

**Import ordering**
- stdlib → third-party → internal? Alphabetical within groups? Auto-sorted?

**File naming**
- `kebab-case`, `PascalCase`, `snake_case`, `camelCase`? Per file type?

---

### 3.2 Naming Conventions

| Symbol | What to check |
|---|---|
| Classes / types | PascalCase? Suffix patterns (e.g. `Service`, `Repository`, `Handler`, `DTO`) |
| Functions / methods | camelCase? snake_case? Verb-first? |
| Variables | camelCase? snake_case? Hungarian notation? |
| Constants | `SCREAMING_SNAKE_CASE`? `k`-prefix? |
| Interfaces / protocols | `I`-prefix? No prefix? `-able` suffix? |
| Files | Match the primary export name? |
| Database columns/tables | snake_case? PascalCase? Singular vs plural table names? |
| Test files | `.test.ts`, `_test.go`, `test_*.py`, `*Spec.js`? |

---

### 3.3 Design Patterns

Look for these structural patterns in the sampled files:

- **Repository / DAO** — Data access abstracted behind an interface; look for `find*`, `save`, `delete` methods on a dedicated class
- **Service layer** — Business logic separated from controllers; look for `*Service` classes injected into controllers
- **Factory** — Object creation centralised; `create*`, `build*`, `make*` methods or classes
- **Strategy** — Interchangeable algorithms behind a common interface
- **Observer / Event bus** — `emit`, `subscribe`, `on`, `EventEmitter`, domain events
- **Decorator / Middleware** — Wrapping behaviour; common in HTTP frameworks
- **CQRS** — Separate command and query paths; `*Command`, `*Query`, `*Handler` naming
- **Dependency Injection** — Constructor injection? Service locator? IoC container?

For each pattern found, note a concrete file/class example.

---

### 3.4 SQL & Data Access Conventions

- **Query location** — Inline in service? In dedicated repository class? In separate `.sql` files? In ORM model methods?
- **Query style** — Raw SQL strings, query builder (Knex, JOOQ, Ecto.Query), ORM (ActiveRecord, Eloquent, SQLAlchemy, TypeORM), stored procedures?
- **Parameterisation** — Named params (`:name`), positional (`$1`, `?`), or ORM-managed?
- **Naming** — Are query methods named after intent (`findActiveUsersByRegion`) or generic (`query`, `execute`)?
- **Transactions** — How are they managed? Explicit try/catch/rollback? UoW pattern? Middleware?
- **Migrations** — Present? Which tool? Naming convention for migration files?
- **N+1 awareness** — Evidence of eager loading, `JOIN` fetching, or dataloaders?

---

### 3.5 Decoupling & Architecture

- **Layer boundaries** — Are there clear layers (presentation / application / domain / infrastructure)? Do imports respect direction (inner layers don't import outer)?
- **Dependency direction** — Do high-level modules depend on abstractions? Check what gets injected vs newed-up
- **Interface usage** — Are there abstract interfaces/protocols that concrete implementations satisfy?
- **Module boundaries** — Monolith? Feature modules? Packages? Barrel exports (`index.ts`)?
- **Cross-cutting concerns** — How are logging, auth, validation, and error handling applied? Middleware? Decorators? Mixins? Explicit calls?
- **Event-driven decoupling** — Internal events, message queues, pub/sub patterns?

---

### 3.6 Error Handling

- **Strategy** — Try/catch everywhere? Error-returning functions (`Result<T, E>`)? Middleware catching all?
- **Custom error types** — Are there domain-specific error classes (`NotFoundError`, `ValidationError`)?
- **Error propagation** — Re-thrown, wrapped with context, or swallowed?
- **Logging** — Where and how? Which logger? Structured (JSON) or plain text?
- **HTTP error mapping** — If a web app, how are domain errors mapped to HTTP status codes?

---

### 3.7 Testing Conventions

- **Test location** — Co-located with source (`src/foo.test.ts`) or separate directory (`tests/`)?
- **Naming** — File naming pattern, `describe` block naming, test case naming style
- **Scope** — Mostly unit? Integration? E2E? What ratio?
- **Mocking strategy** — Manual mocks, auto-mocking, spies, stubs, fakes, in-memory implementations?
- **Fixtures / factories** — How is test data created? Factory helpers? Fixtures files? Inline literals?
- **Assertions** — Which assertion library/style? Fluent (`expect(x).toBe(y)`) or classic (`assert.equal`)?

---

### 3.8 Convention Over Configuration (CoC) Depth

This measures how much the project relies on *implicit rules* (naming/location determines behaviour)
vs *explicit configuration* (every behaviour declared).

Score each dimension:

| Dimension | CoC signals | Config signals |
|---|---|---|
| Routing | File-system routes, name-based routes | Explicit route registration |
| DB mapping | Table/column names inferred from model names | Explicit `@Column('name')` everywhere |
| DI / wiring | Auto-scanning, auto-wiring by type | Explicit provider registration |
| Module loading | Auto-discovery of plugins/modules | Explicit import and register |
| Test discovery | Runner finds tests by filename pattern | Test suite file lists tests explicitly |
| Config files | Sensible defaults; config only overrides | Every option must be declared |

**Rating scale:**
- **Heavy CoC** — Developers rarely configure; naming and location drive everything. New things "just work" if named right.
- **Balanced** — A mix; framework defaults used but significant explicit config for non-trivial things.
- **Config-first** — Explicit is preferred; nothing is magical. Everything is wired and declared.

Cite specific evidence (e.g. "routes are defined by file path in `pages/` — no router config file exists").

---

## Phase 4 — Synthesise

After completing all categories, produce the output document below.

Fill every section. If a category is genuinely not applicable (e.g. no SQL in the project), write
`N/A — [reason]` rather than omitting it.

If you found conflicting patterns (e.g. some files use 2-space indent, others use 4), report the
**dominant** pattern and note the inconsistency explicitly — that itself is a convention finding.

---

## Output Format

Produce a `CONVENTIONS.md` file with this structure:

```markdown
# Project Conventions

> Auto-generated by Chameleon · Mode: [Quick/Standard/Deep/Custom N%] · [date]
> Update this file when conventions change intentionally.

---

## Sampling Coverage

| Stratum | Population | Sampled | Coverage | Confidence |
|---|---|---|---|---|
| config | N | n | % | ✅ |
| entry | N | n | % | ✅ |
| model | N | n | % | ✅/⚠️/🔍 |
| service | N | n | % | ✅/⚠️/🔍 |
| repository | N | n | % | ✅/⚠️/🔍 |
| controller | N | n | % | ✅/⚠️/🔍 |
| test | N | n | % | ✅/⚠️/🔍 |
| migration | N | n | % | ✅/⚠️/🔍 |
| middleware | N | n | % | ✅/⚠️/🔍 |
| util | N | n | % | ✅/⚠️/🔍 |
| other | N | n | % | ✅/⚠️/🔍 |
| **TOTAL** | **N** | **n** | **%** | |

> ✅ High (≥60%) · ⚠️ Medium (30–59%) · 🔍 Low (<30% — treat as signals, not rules)
> To improve confidence: re-run with `deep` mode or `focus deep on <stratum>`.

---

## 1. Formatting & Code Style

### Indentation
[spaces/tabs, width — ✅/⚠️/🔍 — observed in N/n files]

### Line Length
[limit — ✅/⚠️/🔍 — evidence]

### Quotes, Semicolons, Trailing Commas
[findings — confidence per sub-rule]

### Brace & Block Style
[findings — ✅/⚠️/🔍]

### Import Ordering
[findings — ✅/⚠️/🔍]

### File Naming
[findings — ✅/⚠️/🔍]

---

## 2. Naming Conventions

| Symbol | Convention | Confidence | Example |
|---|---|---|---|
| Classes | ... | ✅/⚠️/🔍 | ... |
| ... | ... | ... | ... |

---

## 3. Design Patterns

### [Pattern Name]
**Confidence:** ✅/⚠️/🔍 — seen in N/n sampled files
**Usage:** [description]
**Examples:** `path/to/file.ext` — `ClassName`

---

## 4. SQL & Data Access

### Query Location — [✅/⚠️/🔍]
### Query Style — [✅/⚠️/🔍]
### Parameterisation — [✅/⚠️/🔍]
### Transactions — [✅/⚠️/🔍]
### Migrations — [✅/⚠️/🔍]

---

## 5. Decoupling & Architecture

### Layer Structure — [✅/⚠️/🔍]
### Dependency Direction — [✅/⚠️/🔍]
### Module Boundaries — [✅/⚠️/🔍]
### Cross-cutting Concerns — [✅/⚠️/🔍]

---

## 6. Error Handling

### Strategy — [✅/⚠️/🔍]
### Custom Error Types — [✅/⚠️/🔍]
### Logging — [✅/⚠️/🔍]

---

## 7. Testing

### Structure & Location — [✅/⚠️/🔍]
### Naming — [✅/⚠️/🔍]
### Mocking Strategy — [✅/⚠️/🔍]
### Test Data — [✅/⚠️/🔍]

---

## 8. Convention Over Configuration

**Rating:** [Heavy CoC / Balanced / Config-first]

**Evidence:**
- [finding — ✅/⚠️/🔍]

**What "just works" by naming/location:**
- [list]

**What requires explicit configuration:**
- [list]

---

## 9. Quick-Reference Card

> The 10 rules a new developer must internalise on day one.
> Only rules with ✅ High confidence appear here.

1. ...
2. ...
...

---

## 10. Low-Confidence Signals

> Patterns observed but not confirmed at high confidence.
> Verify manually before treating as rules.
> To promote a signal to a rule: re-run Chameleon with `focus deep on <stratum>`.

- [signal — stratum, N/n reads, what was observed]
```

---

## Notes for the Analyst

- **Sampling is not optional.** Always run the census and compute the plan before reading files.
  Ad-hoc file selection introduces bias that undermines every finding.
- **Cite evidence with counts.** "Observed in 8/10 sampled service files" is a finding.
  "Observed once" is a signal — put it in Section 10, not in the main rules.
- **Distinguish observed vs inferred.** Config-file rules are explicit; pattern-inferred rules
  say "inferred from N/n samples".
- **Flag violations.** Files that break the dominant pattern are often more instructive than the norm.
  Note them explicitly, especially if they cluster in one stratum.
- **Don't hallucinate patterns.** If a layer is absent, say absent.
- **Section 9 only takes ✅ findings.** Six solid rules beat twelve uncertain ones.
- **Section 10 is not a dump.** Each signal should be specific enough to verify in under 5 minutes.
