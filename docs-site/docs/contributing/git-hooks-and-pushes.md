---
title: Git, Husky Hooks, and Pushes
description: How staging, commit, pre-commit, commit-msg, pre-push, kira push, and local tests fit together.
sidebar_position: 10
---

# Git, Husky Hooks, and Pushes

**What you'll learn:**

- A typical **add → commit → push** flow in this repo
- What each **Husky** hook runs (and how it differs from CI)
- How to **skip** parts of the pre-push test gate when you need a faster push
- How **`kira push`** wraps `git push` so you are not double-running tests

---

## Typical flow

```bash
# 1. Stage changes (review with git diff first)
git add .
# or: git add -p   # patch by patch

# 2. Commit — message must pass commitlint (see Commit Conventions)
uv run kira commit              # interactive Commitizen (recommended)
# or: bun run commit
# or: git commit -m "docs(docs-site): clarify API error responses"

# 3. Push — pre-push hook runs tests unless you skip (see below)
git push origin your-branch
# or: uv run kira push              # interactive: choose which tests to run, then push
# or: uv run kira push -y           # full pre-push suite, no prompts, then push
```

Run **`bun install`** once after clone so Husky installs (`.husky/` hooks are wired via the `prepare` script in the repo root `package.json`).

---

## Husky hooks (automation on your machine)

| Hook | When | What runs |
|------|------|-----------|
| **pre-commit** | After `git commit` (before the commit is created) | **`bunx lint-staged`** on staged files (Ruff on staged Python, ESLint/tsc on staged web), then **`uv run kira lint --all`** (full monorepo lint gate: Ruff check+format per service, shared, ESLint + `tsc` on `web-app`). |
| **commit-msg** | Commit message is written | **`bunx commitlint`** — enforces [Conventional Commits](./commit-conventions.md) and allowed **scopes**. |
| **pre-push** | Before `git push` sends objects | **`make test-pre-push`**: all Python services **`pytest`**, **`web-app`** Vitest, then **`scripts/test_integration.sh`** (Docker Postgres/Redis/Kafka + **`pytest -m integration`** per service). Pytest **exit code 5** (no tests matched `-m integration`) is treated as OK for that service. |

**Plain `git push`** always runs the full **pre-push** gate unless you set skip environment variables (below) or use **`kira push`** (which runs tests first, then pushes with **`SKIP_TEST_PRE_PUSH=1`** so the hook does not run the same suite twice).

---

## Skipping parts of pre-push (`git push`)

Set variables in the **same** environment as `git push` (prefix the command or `export` first):

| Variable | Effect |
|----------|--------|
| **`SKIP_TEST_PRE_PUSH=1`** | Skip the **entire** pre-push test suite (hook exits success without running tests). |
| **`SKIP_TEST_ALL=1`** | Skip **all** Python service **`pytest`** loops (`make test-all`). |
| **`SKIP_TEST_WEB=1`** | Skip **web-app** Vitest (`make test-web`). |
| **`SKIP_TEST_INTEGRATION=1`** | Skip Docker **integration** script (`make test-integration`). |
| **`SKIP_TEST_SERVICES="identity-service channel-engine"`** | Space-separated service directory names to skip in **`test-all`** and in **`scripts/test_integration.sh`**. |

Examples:

```bash
SKIP_TEST_INTEGRATION=1 git push
SKIP_TEST_ALL=1 SKIP_TEST_INTEGRATION=1 git push    # Python + integration off; web tests still run
SKIP_TEST_PRE_PUSH=1 git push                       # emergency: no tests on push
```

`make test-pre-push` is defined in the root **`Makefile`**; it runs the three stages in one shell so **`SKIP_TEST_PRE_PUSH=1`** exits the whole target correctly.

---

## `kira push` (wrapper around `git push`)

From the repo root:

- **`uv run kira push`** — **Interactive by default**: prompts for Python tests, web tests, and integration; optional comma-separated services to skip; then runs **`make test-pre-push`** with that env, then **`git push …`** with **`SKIP_TEST_PRE_PUSH=1`** so Husky does not repeat the same work.
- **`uv run kira push -y`** / **`--yes`** — Non-interactive **full** pre-push suite, then push (good for scripts).
- **`uv run kira push --skip-tests`** — No local test run in kira; **`git push`** still sets **`SKIP_TEST_PRE_PUSH=1`** so the hook skips tests too.
- **`uv run kira push --no-services`**, **`--no-web`**, **`--no-integration`**, **`--skip-services`** — Non-interactive partial runs (combine as needed).

Extra arguments are forwarded to **`git`** (e.g. `uv run kira push -y origin main`).

See also: [Getting started — CLI reference](../getting-started/cli-reference.md).

---

## Local testing (without pushing)

| Goal | Command |
|------|---------|
| One service | `uv run kira test <service>` or `make test-<service>` |
| All Python services | `make test-all` |
| All services + web (pytest + Vitest) | `uv run kira test --all` |
| Web only | `make test-web` or `uv run kira test --web` |
| Integration (Docker infra) | `make test-integration` or `uv run kira test --integration` |
| Full pre-push mirror | `make test-pre-push` |

Details on writing tests: [Testing guide](./testing-guide.md).

---

## CI vs hooks

Hooks are your **fast feedback** before sharing commits; CI may run the same or stricter checks on the server. Do not rely on **`SKIP_TEST_PRE_PUSH=1`** for routine work — use it only when you intentionally bypass the gate (e.g. docs-only WIP push with team agreement).
