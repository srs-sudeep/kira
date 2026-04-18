---
sidebar_position: 6
title: Commit Conventions
description: How to write proper commits in the KIRA monorepo
---

# Commit Conventions

KIRA uses **Conventional Commits** enforced by Husky git hooks, Commitizen, and Commitlint.

## Quick Start

```bash
# Use the interactive prompt (recommended)
uv run kira commit

# Or write it manually following the format below
git commit -m "feat(identity): add MFA backup codes"
```

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

Runs before every commit:

- TypeScript type-check (`tsc --noEmit`) on `web-app/`
- ESLint on `web-app/`

### `commit-msg`

Runs after you write the commit message:

- Validates the message against Conventional Commits format via **commitlint**
- Rejects the commit if the format is wrong

### `pre-push`

Runs before every push:

- Runs `make test-all` (all backend service tests)

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
| `package.json` (root)  | Husky + Commitizen + Commitlint packages |
| `commitlint.config.mjs` | Commitlint rules and allowed scopes     |
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
