---
name: falcon
description: >
  Fast, precise unit test generation skill. Triggers whenever a user wants to: generate unit
  tests, check for missing test coverage, scan uncommitted changes for untested code, write tests
  for a package or file, or audit test coverage gaps. Trigger this skill for any request involving
  "write tests", "add unit tests", "check coverage", "missing tests", "scan for untested",
  "test my code", "generate test cases", or similar — even if the user doesn't say "falcon"
  explicitly. Also trigger when the user points at a package, module, directory, or diff and
  asks what needs testing. The skill auto-detects the programming language and maps to the
  correct test framework (Jest/Vitest for JS/TS, pytest for Python, JUnit for Java, NUnit for C#,
  go test for Go, RSpec for Ruby, XCTest for Swift, etc.).
---

# 🦅 Falcon — Fast Unit Test Generation

Falcon scans code for missing unit tests and generates clear, robust, useful tests that follow
language-idiomatic conventions and FIRST principles (Fast, Isolated, Repeatable, Self-validating,
Timely).

---

## Entry Points

Two modes, determined by what the user provides:

| Mode | Trigger | What to scan |
|------|---------|--------------|
| **Package mode** | User names a file, folder, or package | Scan only that scope |
| **Diff mode** (default) | No scope given | Run `git diff HEAD` + `git status` to find all uncommitted changes |

Always confirm the detected scope with the user before generating tests (one line is enough).

---

## Step 1 — Detect Scope

### Package mode
```bash
# List all source files in the target (exclude test files, build artifacts)
find <target> -type f \( -name "*.py" -o -name "*.ts" -o -name "*.js" -o -name "*.java" \
  -o -name "*.cs" -o -name "*.go" -o -name "*.rb" -o -name "*.swift" -o -name "*.kt" \
  -o -name "*.rs" -o -name "*.cpp" -o -name "*.php" \) \
  | grep -Ev "(test|spec|__pycache__|node_modules|dist|build|\.min\.)" \
  | sort
```

### Diff mode (default)
```bash
# Get all modified/added source files not yet committed
git diff HEAD --name-only --diff-filter=ACMR
git status --short | awk '{print $2}'
```

Then deduplicate and filter to source files only (same extensions as above).

---

## Step 2 — Detect Language & Framework

Read the file extensions and project config files to pick the right framework.
See `references/frameworks.md` for the full mapping.

Quick heuristics:
- `package.json` present → check for `jest`, `vitest`, `mocha` in devDependencies
- `pyproject.toml` / `setup.py` / `requirements*.txt` → **pytest**
- `pom.xml` / `build.gradle` → **JUnit 5** (+ Mockito for mocking)
- `*.csproj` / `*.sln` → **NUnit** or **xUnit** (check existing test project)
- `go.mod` → **go test** + **testify** if present
- `Gemfile` → **RSpec** (default) or **Minitest**
- `Package.swift` / `*.xcodeproj` → **XCTest**
- `Cargo.toml` → built-in `#[test]`

When ambiguous, check existing test files for the pattern already in use and match it.

---

## Step 3 — Audit for Missing Tests

For each source file in scope:

1. **Find the companion test file** using the project's naming convention (detected from existing tests):
   - Python: `test_<module>.py` or `<module>_test.py`
   - JS/TS: `<module>.test.ts` / `<module>.spec.ts`
   - Java: `<ClassName>Test.java`
   - Go: `<file>_test.go` (same package)
   - etc.

2. **Extract public surface**: classes, functions, methods, exported symbols.

3. **Cross-reference** with existing test file (if any) to find what's already covered.

4. **Report gaps** — list untested functions/methods before writing anything:
   ```
   📋 Coverage gaps found in src/auth/tokenService.ts:
     ✗ generateToken()      — no test
     ✗ verifyToken()        — no test
     ✓ refreshToken()       — covered
     ✗ revokeToken()        — no test
   ```

5. Ask: *"Should I generate tests for all gaps, or just specific ones?"* — unless the user already said "all".

---

## Step 4 — Generate Tests

### Golden rules (apply to every language)

- **AAA structure**: every test body = Arrange → Act → Assert, with blank lines between sections
- **One assertion per test** (or one logical concern); split if a test would need 2+ unrelated asserts
- **Descriptive names**: `should_<expected>_when_<condition>` or `<method> <scenario> <expectation>`
- **No magic numbers**: name constants (`const MAX_RETRIES = 3`, not `3`)
- **Mock all I/O**: network, DB, filesystem, time — tests must run offline in milliseconds
- **Cover the matrix**: happy path + boundary values + error/exception cases + null/empty inputs
- **Never test implementation details**: test behavior through the public API only
- **Reset state**: use `beforeEach`/`afterEach` (or equivalent) so tests are order-independent

### Test case matrix per function

For each untested function, generate at minimum:

| Case type | Example |
|-----------|---------|
| Happy path | valid input → expected output |
| Boundary | empty list, zero, max value |
| Error | invalid input → throws / returns error |
| Null/undefined | null arg → graceful handling |
| Side effects | mock called with correct args |

Add more cases when domain logic warrants it (e.g. auth, math, state machines).

### Output placement

Place generated tests in the **correct companion file** per project convention:
- If the file exists → append new test cases (don't duplicate existing ones)
- If it doesn't exist → create it with proper imports/setup boilerplate

---

## Step 5 — Quality Check

Before presenting output, self-review each test:

- [ ] Test name clearly states what it checks
- [ ] No real I/O (all dependencies mocked)
- [ ] Would fail if the implementation were deleted
- [ ] No dependency on another test's state
- [ ] Imports are correct for the detected framework
- [ ] Follows existing code style in the project (indentation, quote style, etc.)

---

## Communication Style

- Lead with the **scope summary** (files found, language, framework)
- Show the **gap audit table** before writing tests — let the user confirm
- When writing tests, **group by source function** with a brief comment header
- After writing, give a **one-line summary**: `Generated 12 tests across 3 files (auth, user, cart)`
- If a function is too complex to unit-test without refactoring, say so and suggest the split

---

## Reference Files

- `references/frameworks.md` — Full language → framework mapping with import boilerplate
- `references/patterns.md` — Language-specific test patterns and mocking idioms

Read these when you need framework-specific syntax or when the quick heuristics above are ambiguous.
