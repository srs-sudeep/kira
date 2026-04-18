---
sidebar_position: 8
title: CLI Reference
description: Complete reference for the KIRA CLI tool
---

# CLI Reference

KIRA ships a unified CLI tool that wraps every monorepo operation — Docker, testing, migrations, deployment, linting, and more.

:::info CLI is the source of truth

Behavior for stack, tests, migrations, seed, docs, and lint lives in **`cli/`**. The root **`Makefile`** is a thin convenience layer: most targets run **`uv run kira …`** so CI, Husky, and `make` users get the same logic. Prefer **`uv run kira`** (or **`./bin/kira`**) for day-to-day work; see **[Makefile, CLI, and Compose](./makefile-and-cli.md)**.
:::

:::info How commands are written here

Examples use **`uv run kira …`** from the **repository root** (where the root `pyproject.toml` lives). If you installed the CLI with **`uv tool install --editable .`** from that same root, the executable is on your **`PATH`** and every command works as **`kira …`** instead — same flags, no `uv run` prefix.

:::

### `bin/kira` (repo wrapper script) {#bin-kira}

The repo ships **`bin/kira`**, a small Bash script that:

1. Finds the monorepo root (`git rev-parse --show-toplevel`, or the parent of `bin/` if Git is unavailable).
2. Runs **`exec uv run --project "$root" kira "$@"`** so the **root** `pyproject.toml` is always used.

Use it when your cwd is under **`services/…`** (or anywhere `uv run kira` would bind to the wrong project), **without** a global `uv tool install`:

```bash
./bin/kira dev up
./bin/kira --help
```

It does **not** install `kira` globally; it only forwards to the root CLI. For a permanent **`kira`** on `PATH`, still use **`uv tool install --editable .`** from the repo root.

## Installation

The CLI is Python ([Typer](https://typer.tiangolo.com/)) under `cli/` at the repo root. You can run it **without** a global install, put **`kira` on your PATH** once via uv’s tool interface, or run a **one-off** invocation with `uvx`.

### Run via project (`uv run`)

From the **repository root** (the directory that contains the root `pyproject.toml`):

```bash
uv run kira --help
```

If your shell is inside `services/*`, uv picks that service’s `pyproject.toml` instead, and `uv run kira` fails — use **`./bin/kira`** as in the [wrapper section above](#bin-kira).

More causes and fixes: [E2E local dev → Troubleshooting](./e2e-local-dev.md#troubleshooting).

### Global `kira` on your PATH ([uv tools](https://docs.astral.sh/uv/concepts/tools/))

From the **repository root** of your clone:

```bash
cd kira   # your clone directory
uv tool install --editable .
```

- This installs the `kira` [console script](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/#console-scripts) from the root package (`kira-cli` in `pyproject.toml`) into uv’s tool environment and symlinks it onto your PATH.
- **`--editable` (`-e`)** — recommended while you work on the monorepo: edits under `cli/` apply immediately without reinstalling.
- Without `-e`, you get a normal install; after `git pull`, refresh with `uv tool upgrade kira-cli` or `uv tool install . --force`.

If uv warns that the executable directory is not on your `PATH`, follow its hint or run:

```bash
uv tool update-shell
```

**Uninstall:** `uv tool uninstall kira-cli`

### One-off without installing (`uvx`)

From the repo root:

```bash
uvx --from . kira --help
```

From another directory, point `--from` at your clone (absolute path is clearest):

```bash
uvx --from ~/src/kira kira dev status
```

:::danger Do not use plain `uvx kira`
That command installs a **different** project named `kira` from PyPI, not this repository. Always use `uvx --from <path-to-clone> kira`, or install with `uv tool install` as above.
:::

### Shell Completion

```bash
# Bash (from repo root, or use `kira` if you installed with `uv tool install`)
uv run kira --install-completion bash

# Zsh
uv run kira --install-completion zsh

# Fish
uv run kira --install-completion fish
```

---

## Commands

### `kira dev` — Local Development

| Command                     | Description                                                                                          |
| --------------------------- | ---------------------------------------------------------------------------------------------------- |
| `kira dev setup`            | Bootstrap local dev: check prereqs, copy envs, install deps, start infra, migrate on **host**, seed |
| `kira dev up`               | Start core Docker Compose stack (same as `make up`)                                                  |
| `kira dev up --full`        | Core + observability compose files (same as `make up-full`; **no** docs profile unless you add `--docs`) |
| `kira dev up --docs`        | With `--full` or core `up`: also enable Compose **`docs`** profile (docs-site container)             |
| `kira dev e2e`              | Run `setup`, then `up --full` (observability; use `kira docs docker-up` separately if you want docs in Docker) |
| `kira dev bootstrap`        | **Docker-first path:** `up --full` → wait Postgres → `kira migrate --all --docker` → `kira seed --docker` (same as `make bootstrap`) |
| `kira dev wait-postgres`    | Poll `pg_isready` in the core Postgres container (same as `make wait-postgres`)                      |
| `kira dev down`             | Stop and remove containers (keep volumes)                                                            |
| `kira dev logs [SERVICE]`   | Follow container logs (all or one Compose service name)                                              |
| `kira dev status`           | `docker compose ps -a` for the core file                                                             |
| `kira dev clean`            | Stop everything, remove volumes + orphans (**prompts**; use `--yes` / `-y` for automation / `make clean`) |
| `kira dev init`             | Write per-developer `docker-compose.override.yml` (DB name isolation)                                |

**Quick start from a fresh clone:**

```bash
uv run kira dev setup       # Host-side migrate + seed after infra is up
uv run kira dev up          # Start all app containers (core)
uv run kira dev bootstrap   # Or: full Docker path (migrate + seed in containers) — see Makefile, CLI, and Compose
uv run kira dashboards      # Open browser tabs (core URLs)
# After `kira dev up --full`:  uv run kira dashboards --full   # or --all — adds Grafana, Prometheus, …
```

---

### `kira test` — Testing

| Command                     | Description                                                                 |
| --------------------------- | --------------------------------------------------------------------------- |
| `kira test <service>`       | Run pytest for one service (e.g. `kira test identity-service`)              |
| `kira test --all`           | All six **backend** services **and** web-app (Vitest)                       |
| `kira test --all --no-web`  | Backend only (matches **`make test-all`** and pre-push Python stage)       |
| `kira test --web`           | Web-app tests only (Vitest)                                                 |
| `kira test --all --coverage --no-web` | All services with coverage gate (matches **`make test-coverage`**) |
| `kira test --integration`   | Compose up Postgres/Redis/Kafka, `pytest -m integration` per service, tear down |

**Environment:** `SKIP_TEST_SERVICES="svc1 svc2"` skips those service directories in **`--all`** and **`--integration`**.

```bash
uv run kira test identity-service
uv run kira test --all --no-web          # Same as make test-all
uv run kira test --all                   # Backend + web
uv run kira test --all --coverage --no-web
uv run kira test --integration
```

---

### `kira migrate` — Database Migrations

| Command                           | Description                             |
| --------------------------------- | --------------------------------------- |
| `kira migrate <service>`          | Run Alembic `upgrade head` on host      |
| `kira migrate --all`              | Migrate all services on host            |
| `kira migrate <service> --docker` | Run Alembic inside the Docker container |
| `kira migrate --all --docker`     | Migrate all services inside containers  |

```bash
uv run kira migrate identity-service
uv run kira migrate --all --docker
```

---

### `kira seed` — Seed Data

| Command                | Description                             |
| ---------------------- | --------------------------------------- |
| `kira seed`            | Seed development data from host         |
| `kira seed --docker`   | Seed via Docker Compose profile         |
| `kira seed superadmin` | Create a super-admin user interactively |

---

### `kira deploy` — Deployment

| Command                  | Description                                       |
| ------------------------ | ------------------------------------------------- |
| `kira deploy staging`    | Deploy to staging (EKS, `kira-staging` namespace) |
| `kira deploy production` | Deploy to production (EKS, `kira` namespace)      |

**Flags:**

| Flag                   | Description                                      |
| ---------------------- | ------------------------------------------------ |
| `--skip-terraform`     | Skip the Terraform init/plan/apply phase         |
| `--services svc1,svc2` | Deploy only specific services                    |
| `--dry-run`            | Show what would execute without running anything |

```bash
uv run kira deploy staging --dry-run
uv run kira deploy production --skip-terraform --services identity-service,admin-service
```

---

### `kira lint` — Linting

| Command                 | Description                         |
| ----------------------- | ----------------------------------- |
| `kira lint <service>`   | Lint one service with ruff          |
| `kira lint --web`       | Lint web-app with eslint            |
| `kira lint --all`       | Lint all services + web-app         |
| `kira lint --all --fix` | Auto-fix lint issues where possible |

---

### `kira docs` — Documentation

| Command              | Description                                                                 |
| -------------------- | --------------------------------------------------------------------------- |
| `kira docs dev`        | `bun install` in `docs-site/`, then Docusaurus dev server (port **4000**)   |
| `kira docs build`      | `bun install`, then static build → `docs-site/build/`                       |
| `kira docs docker-up`  | `docker compose --profile docs up -d --build docs-site` (same as `make docs-docker-up`) |

---

### `kira commit`

Opens the Commitizen interactive prompt for writing conventional commits.

```bash
uv run kira commit
```

---

### `kira push`

Runs the same gate as Husky **pre-push** (`make test-pre-push`) with optional skips, then **`git push`** with **`SKIP_TEST_PRE_PUSH=1`** so the hook does not run that suite again.

- **Default:** interactive prompts (which stages to run).
- **`-y` / `--yes`:** non-interactive full suite (CI-friendly).
- **`--skip-tests`**, **`--no-services`**, **`--no-web`**, **`--no-integration`**, **`--skip-services`:** non-interactive partial runs.

```bash
uv run kira push -y origin main
uv run kira push --no-services --no-integration
```

Full reference: [Git, Husky hooks, and pushes](../contributing/git-hooks-and-pushes.md).

---

### `kira dashboards`

Opens KIRA dashboard URLs in the default browser.

```bash
uv run kira dashboards              # Web :3000, docs :4000, Mailhog, Kong, each service /docs (8001–8006)
uv run kira dashboards --full       # Above + observability UIs (Grafana, Prometheus, …)
uv run kira dashboards --all        # Same as --full
```

---

## Service Names

The following service names are valid wherever a `<service>` argument is expected:

- `admin-service`
- `identity-service`
- `rate-inventory-service`
- `reservation-service`
- `channel-engine`
- `notification-service`

---

## Makefile Equivalents

Many tasks exist in both places. **`make help`** lists all Make targets. For compose **profiles**, **workers**, **bootstrap**, and when to prefer host vs Docker migrations, see **[Makefile, CLI, and Compose](./makefile-and-cli.md)**.

| CLI | Makefile |
| --- | -------- |
| `kira dev up` | `make up` |
| `kira dev up --full` | `make up-full` |
| `kira dev down` | `make down` |
| `kira dev logs` / `kira dev logs <service>` | `make logs` / `make logs-<service>` |
| `kira dev status` | `make stack-status` |
| `kira dev clean` | `make clean` (Make calls `kira dev clean --yes`; interactive use: `kira dev clean` prompts) |
| `kira dev bootstrap` | `make bootstrap` |
| `kira dev wait-postgres` | `make wait-postgres` |
| `kira dev up --docs` | Optional docs profile on core or full stack (see `kira dev up --help`) |
| `kira test <service>` | `make test-<service>` |
| `kira test --all --no-web` | `make test-all` |
| `kira test --web` | `make test-web` |
| `kira test --all --coverage --no-web` | `make test-coverage` |
| `kira test --integration` | `make test-integration` |
| `kira push` / `kira push -y` | Runs `make test-pre-push` (with your skips), then `git push` — not a single Make alias; see [Git hooks doc](../contributing/git-hooks-and-pushes.md) |
| `kira migrate <service>` | `make migrate-<service>` |
| `kira migrate --all` | `make migrate-all` |
| `kira migrate <service> --docker` | `make migrate-docker-<service>` |
| `kira migrate --all --docker` | `make migrate-docker-all` |
| `kira seed` | `make seed` |
| `kira seed --docker` | `make seed-docker` |
| `kira seed superadmin` | `make superadmin` |
| `kira dev setup` | `make dev-setup` |
| `kira dashboards` | `make dashboards` |
| `kira dashboards --full` / `--all` | `make dashboards-full` |
| `kira docs dev` | `make docs-dev` |
| `kira docs build` | `make docs-build` |
| `kira docs docker-up` | `make docs-docker-up` |
