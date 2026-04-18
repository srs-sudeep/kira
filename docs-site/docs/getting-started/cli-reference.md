---
sidebar_position: 8
title: CLI Reference
description: Complete reference for the KIRA CLI tool
---

# CLI Reference

KIRA ships a unified CLI tool that wraps every monorepo operation — Docker, testing, migrations, deployment, linting, and more.

## Installation

The CLI is Python ([Typer](https://typer.tiangolo.com/)) under `cli/` at the repo root. You can run it **without** a global install, put **`kira` on your PATH** once via uv’s tool interface, or run a **one-off** invocation with `uvx`.

### Run via project (`uv run`)

From the **repository root** (the directory that contains the root `pyproject.toml`):

```bash
uv run kira --help
```

If your shell is inside `services/*`, uv picks that service’s `pyproject.toml` instead, and `uv run kira` fails. From anywhere in the clone you can use the wrapper:

```bash
./bin/kira --help
```

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

| Command                   | Description                                                                             |
| ------------------------- | --------------------------------------------------------------------------------------- |
| `kira dev setup`          | Bootstrap local dev: check prereqs, copy envs, install deps, start infra, migrate, seed |
| `kira dev up`             | Start core Docker Compose stack                                                         |
| `kira dev up --full`      | Start core + observability + docs-site (enables Docker Compose `docs` profile)         |
| `kira dev e2e`            | Run setup flow, then start full stack (core + observability + docs-site)               |
| `kira dev down`           | Stop and remove containers (keep volumes)                                               |
| `kira dev logs [SERVICE]` | Follow container logs (all or one service)                                              |
| `kira dev status`         | Show container status                                                                   |
| `kira dev clean`          | Stop everything, remove containers + volumes + orphans                                  |

**Quick start from a fresh clone:**

```bash
uv run kira dev setup    # One command to rule them all
uv run kira dev up       # Start services
uv run kira dev e2e      # Setup + full stack (includes docs-site)
uv run kira dashboards   # Open browser tabs (core URLs)
# After `kira dev up --full`:  uv run kira dashboards --full   # or --all — adds Grafana, Prometheus, …
```

---

### `kira test` — Testing

| Command                   | Description                                                    |
| ------------------------- | -------------------------------------------------------------- |
| `kira test <service>`     | Run pytest for one service (e.g. `kira test identity-service`) |
| `kira test --all`         | Run all 6 service tests + web-app tests                        |
| `kira test --web`         | Run web-app tests only (Vitest)                                |
| `kira test --coverage`    | Run pytest with `--cov --cov-fail-under=70%` for all services  |
| `kira test --integration` | Start infra containers, run `pytest -m integration`, tear down |

```bash
uv run kira test identity-service          # Single service
uv run kira test --all                     # Everything
uv run kira test --coverage                # With coverage gate
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

| Command           | Description                             |
| ----------------- | --------------------------------------- |
| `kira docs dev`   | Start Docusaurus dev server (port 4000) |
| `kira docs build` | Build static documentation site         |

---

### `kira commit`

Opens the Commitizen interactive prompt for writing conventional commits.

```bash
uv run kira commit
```

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
| `kira dev clean` | `make clean` (Make does not prompt; `kira dev clean` asks for confirmation) |
| `kira test <service>` | `make test-<service>` |
| `kira test --all` | `make test-all` |
| `kira test --web` | `make test-web` |
| `kira test --coverage` | `make test-coverage` |
| `kira test --integration` | `make test-integration` |
| `kira migrate --all` | `make migrate-all` |
| `kira migrate --all --docker` | `make migrate-docker-all` |
| `kira seed` | `make seed` |
| `kira seed --docker` | `make seed-docker` |
| `kira dev setup` | `make dev-setup` |
| `kira dashboards` | `make dashboards` |
| `kira dashboards --full` / `--all` | `make dashboards-full` |
| `kira docs dev` | `make docs-dev` |
| `kira docs build` | `make docs-build` |

There is **no** `kira` subcommand for **`make bootstrap`** (`up-full` → migrate in Docker → seed in Docker); use Make or run those steps by hand.
