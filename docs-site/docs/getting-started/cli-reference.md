---
sidebar_position: 8
title: CLI Reference
description: Complete reference for the KIRA CLI tool
---

# CLI Reference

KIRA ships a unified CLI tool that wraps every monorepo operation — Docker, testing, migrations, deployment, linting, and more.

## Installation

The CLI is built with Python (Typer) and lives at the repo root. No separate install is needed:

```bash
# Run any command via uv
uv run kira --help

# Or install in editable mode for a global `kira` command
pip install -e .
```

### Shell Completion

```bash
# Bash
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
| `kira dev up --full`      | Start core + observability (Grafana, Prometheus, Loki…)                                 |
| `kira dev down`           | Stop and remove containers (keep volumes)                                               |
| `kira dev logs [SERVICE]` | Follow container logs (all or one service)                                              |
| `kira dev status`         | Show container status                                                                   |
| `kira dev clean`          | Stop everything, remove containers + volumes + orphans                                  |

**Quick start from a fresh clone:**

```bash
uv run kira dev setup    # One command to rule them all
uv run kira dev up       # Start services
uv run kira dashboards   # Open UIs
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
uv run kira dashboards          # Core UIs
uv run kira dashboards --full   # Core + observability
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

The CLI wraps the Makefile, so both work:

| CLI                  | Makefile           |
| -------------------- | ------------------ |
| `kira dev up`        | `make up`          |
| `kira dev up --full` | `make up-full`     |
| `kira dev down`      | `make down`        |
| `kira test --all`    | `make test-all`    |
| `kira test --web`    | `make test-web`    |
| `kira migrate --all` | `make migrate-all` |
| `kira seed`          | `make seed`        |
| `kira dev setup`     | `make dev-setup`   |
