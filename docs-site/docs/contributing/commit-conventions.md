---
sidebar_position: 6
title: Commit Conventions
description: How to write proper commits in the KIRA monorepo
---

# Commit Conventions

KIRA uses **Conventional Commits** enforced by Husky git hooks, Commitizen, and Commitlint.

## Quick Start

```bash
# Use the interactive prompt (recommended) — same as:
bun run commit
# from the repo root (uses Commitizen + @commitlint/cz-commitlint)

uv run kira commit

# Or write it manually following the format below
git commit -m "feat(identity): add MFA backup codes"
```

## Interactive scope helper

`bun run commit` / `npx cz` / `uv run kira commit` use **`@commitlint/cz-commitlint`**, which reads **`commitlint.config.mjs`**. Your **scope** is chosen from the same **allowed list** as commitlint (no free‑typing a filename like `bun.lockb` — pick **`deps`**, **`web`**, etc.). Types and header length follow the same rules as the hook.

## Auditing or rewriting old commits

List subjects that **fail today’s commitlint** (merge commits skipped):

```bash
bun run commit:audit
```

Older commits often predate stricter rules; **do not rewrite the entire shared history** unless you know every collaborator will re-clone or hard-reset. Rewriting changes every SHA and breaks open PRs / forks.

- **Unpushed work only:** `git rebase -i origin/main` and `reword` / `edit` commits, then `git push --force-with-lease`.
- **Already on `main` / GitHub:** leave history as-is; hooks still enforce **new** commits.

## Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type       | When to use                                             |
| ---------- | ------------------------------------------------------- |
| `feat`     | A new feature                                           |
| `fix`      | A bug fix                                               |
| `docs`     | Documentation only changes                              |
| `style`    | Formatting, white-space, semicolons (no code change)    |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf`     | Performance improvement                                 |
| `test`     | Adding or correcting tests                              |
| `build`    | Build system or external dependency changes             |
| `ci`       | CI/CD configuration changes                             |
| `chore`    | Other changes that don't modify src or test files       |
| `revert`   | Reverts a previous commit                               |

### Scopes

Commitlint **only** allows the scopes below. Do **not** use a filename (e.g. `bun.lockb`) as the scope — use **`deps`** for root or package lockfiles, or the area the change belongs to.

| Scope            | Maps to                           |
| ---------------- | --------------------------------- |
| `identity`       | `services/identity-service`       |
| `admin`          | `services/admin-service`          |
| `rate-inventory` | `services/rate-inventory-service` |
| `reservation`    | `services/reservation-service`    |
| `channel`        | `services/channel-engine`         |
| `notification`   | `services/notification-service`   |
| `web`            | `web-app/`                        |
| `infra`          | `docker/`, `infra/`, `k8s/`, `observability/`, Terraform |
| `docs`           | Markdown in `docs/` (blueprint)   |
| `docs-site`      | Docusaurus site under `docs-site/` |
| `shared`         | `shared/`                         |
| `cli`            | `cli/`                            |
| `deps`           | Lockfiles and dependency bumps — **root** `package.json` / `bun.lockb`, `uv.lock`, service `poetry.lock`, `web-app/bun.lock`, etc. |

### Examples

```bash
feat(identity): add password reset flow
fix(channel): handle OTA timeout gracefully
docs(web): update routing documentation
test(reservation): add integration tests for booking flow
ci(infra): add staging deploy workflow
chore(deps): bump fastapi to 0.116
build(deps): update bun.lockb for package versions and structure
refactor(shared): extract tenant middleware to separate module
```

## Git Hooks (Husky)

Three hooks run automatically:

### `pre-commit`

Runs before every commit is finalized:

1. **`bunx lint-staged`** — Ruff on staged Python, ESLint / TS on staged `web-app` files (see `package.json` / lint-staged config).
2. **`uv run kira lint --all`** — full monorepo lint gate: Ruff check + format check on every service and **`shared/`**, ESLint + **`tsc --noEmit`** on **`web-app/`**.

### `commit-msg`

Runs after you write the commit message:

- Validates the message against Conventional Commits format via **commitlint**
- Rejects the commit if the format is wrong

### `pre-push`

Runs before **`git push`** sends objects:

- **`make test-pre-push`** — one shell script that runs (unless skipped via env vars):
  - **`make test-all`** → **`uv run kira test --all --no-web`**
  - **`make test-web`** → **`uv run kira test --web`**
  - **`make test-integration`** → **`uv run kira test --integration`**

Use **`uv run kira push`** to run the same gate interactively (or with flags), then push with **`SKIP_TEST_PRE_PUSH=1`** so the hook does not repeat the work. Details: **[Git, Husky hooks, and pushes](./git-hooks-and-pushes.md)**.

### Bypassing Hooks

In rare cases (e.g., WIP commits on a feature branch):

```bash
git commit --no-verify -m "wip: temporary save"
```

:::caution
CI also validates commit messages on pull requests. Use `--no-verify` sparingly.
:::

## Configuration Files

| File                   | Purpose                                  |
| ---------------------- | ---------------------------------------- |
| `package.json` (root)  | Husky, Commitizen (`@commitlint/cz-commitlint`), Commitlint, `commit:audit` script |
| `commitlint.config.mjs` | Commitlint rules + scopes (also drives interactive `cz`) |
| `scripts/audit-commit-messages.sh` | `bun run commit:audit` — list historical subjects that fail commitlint |
| `.husky/pre-commit`    | Pre-commit hook script                   |
| `.husky/commit-msg`    | Commit message validation hook           |
| `.husky/pre-push`      | Pre-push test hook                       |

## Setup

If hooks aren't running after a fresh clone:

```bash
bun install        # Installs Husky + activates hooks
# or
uv run kira dev setup  # Does this automatically
```
