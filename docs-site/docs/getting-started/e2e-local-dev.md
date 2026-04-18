---
title: End-to-End Local Development
description: Complete walkthrough from cloning the repo to running tests — every command in order.
sidebar_position: 0
---

# End-to-End Local Development

A single page covering **everything** — from a blank machine to a **fully tested, running KIRA stack**.

:::tip TL;DR

```bash
git clone https://github.com/abodeab/kira.git && cd kira
# Host-path setup (deps, infra, migrate+seed on host):
uv run kira dev setup          # Make: make dev-setup
# Then start all app containers:
uv run kira dev up             # Make: make up
# Optional: own Postgres DB name (CLI only — no make alias):
# uv run kira dev init --name yourname   # see Per-developer database isolation
open http://localhost:3000
```

**Docker-first one-liner** after clone (full stack + migrate + seed in containers): **`uv run kira dev bootstrap`** — same as **`make bootstrap`**.

For **Make vs `kira`**, compose **profiles**, Celery **workers**, **DB isolation**, and **host vs Docker** Postgres, see [Makefile, CLI, and Compose](./makefile-and-cli.md) and [Per-developer database isolation](./per-developer-db.md).

Throughout this site, **`uv run kira`** and **`kira`** mean the same CLI — use whichever matches how you installed it ([CLI Reference → Installation](./cli-reference.md#installation)).

:::

---

## 1. Install Prerequisites

| Tool                            | Install (macOS)                                    | Verify                   |
| ------------------------------- | -------------------------------------------------- | ------------------------ |
| **Docker Desktop** (8 GB+ RAM)  | `brew install --cask docker`                       | `docker compose version` |
| **Python 3.13**                 | `brew install python@3.13`                         | `python3 --version`      |
| **uv** (Python package manager) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `uv --version`           |
| **Bun** (JS runtime)            | `curl -fsSL https://bun.sh/install \| bash`        | `bun --version`          |
| **Git**                         | `xcode-select --install`                           | `git --version`          |

:::warning Docker memory
Open **Docker Desktop → Settings → Resources → Memory** and set to **8 GB minimum** (12 GB recommended). The default 2 GB will OOM-kill Kafka/Postgres.
:::

See [Prerequisites](./prerequisites.md) for Linux instructions and optional tools.

---

## 2. Clone & Install the CLI

```bash
git clone https://github.com/abodeab/kira.git
cd kira
```

The `kira` CLI is a Python tool managed by uv. Verify it works:

```bash
uv run kira --help
```

You should see top-level commands such as `commit`, `dashboards`, `dev`, `test`, `migrate`, `seed`, `deploy`, `docs`, `lint`, and `push`.

Install root JS tooling (Husky hooks, Commitizen, lint-staged):

```bash
bun install
```

---

## 3. Automated Setup (Recommended)

The `dev setup` command does everything in steps 4–8 automatically:

```bash
uv run kira dev setup
```

**What it does:**

1. Checks Docker, uv, bun are installed
2. Copies `.env.example` → `.env.local` for each service
3. Runs `bun install` at root and in `web-app/`
4. Starts Postgres, Redis, Kafka containers
5. Waits for Postgres to be healthy
6. Runs Alembic migrations for all 6 services
7. Seeds development data (tenants, users, room types, rates)

Skip to [Step 9](#9-start-the-full-stack) after this completes.

---

## 4. (Manual) Configure Environment Files

```bash
for svc in identity-service rate-inventory-service reservation-service \
           channel-engine notification-service admin-service; do
  cp services/$svc/.env.example services/$svc/.env.local
done
```

Each `.env.local` contains sensible defaults for local dev (localhost Postgres, Redis, Kafka).

---

## 5. (Manual) Per-Developer Database Isolation

Optional but recommended when multiple developers share a machine — each gets a separate Postgres **database name** inside the same container. Full guide: **[Per-developer database isolation](./per-developer-db.md)**.

**CLI only** (no `make` wrapper):

```bash
uv run kira dev init --name alice
```

This creates `docker/docker-compose.override.yml` pointing all services to `kira_alice` instead of `kira`.

---

## 6. (Manual) Start Infrastructure

```bash
uv run kira dev up
# Make: make up

# Or infra only, raw Compose (same files kira uses):
docker compose -f docker/docker-compose.yml up -d postgres redis kafka
```

Wait for health checks:

```bash
uv run kira dev status
# Make: make stack-status
# All infra containers should show "healthy"
```

---

## 7. (Manual) Run Database Migrations

```bash
uv run kira migrate --all --docker
# Make: make migrate-docker-all
```

This runs Alembic `upgrade head` inside each running service container. Alternatively, run migrations on the host (requires Postgres on localhost:5432):

```bash
uv run kira migrate --all
# Make: make migrate-all
```

---

## 8. (Manual) Seed Development Data

```bash
uv run kira seed --docker
# Make: make seed-docker
```

Seeds: super-admin user (`admin@example.com` / `Admin1234!`), sample tenants, room types, rate plans, and test reservations.

---

## 9. Start the Full Stack

```bash
uv run kira dev up          # Core: 6 services + Kong + web-app + infra  |  Make: make up
uv run kira dev up --full   # Core + observability                        |  Make: make up-full
```

Verify everything is healthy:

```bash
uv run kira dev status      # Make: make stack-status
```

| Service                | URL                        | Notes                             |
| ---------------------- | -------------------------- | --------------------------------- |
| **Web App**            | http://localhost:3000      | React + Vite dev server (`PORT` / `VITE_DEV_PORT`, default **3000**) |
| **Docs site**          | http://localhost:4000      | Docusaurus — `kira docs dev`, `make docs-dev`, or Docker `--profile docs` (only one :4000 at a time) |
| **Kong Gateway**       | http://localhost:8000      | API gateway (proxies to services under `/api/v1/`) |
| **Identity API**       | http://localhost:8001/docs | Swagger UI                        |
| **Rate/Inventory API** | http://localhost:8002/docs | Swagger UI                        |
| **Reservation API**    | http://localhost:8003/docs | Swagger UI                        |
| **Channel Engine API** | http://localhost:8004/docs | Swagger UI                        |
| **Notification API**   | http://localhost:8005/docs | Swagger UI                        |
| **Admin API**          | http://localhost:8006/docs | Swagger UI                        |
| **Mailhog**            | http://localhost:8025      | Catches outgoing emails           |

Open local URLs in the browser (many tabs):

```bash
uv run kira dashboards              # Make: make dashboards
uv run kira dashboards --full       # Make: make dashboards-full  (alias --all)
uv run kira dashboards --all        # Same as --full
```

---

## 10. Run Tests

### Backend Tests (per service)

```bash
uv run kira test identity-service           # Single service
uv run kira test --all --no-web            # All six backends (same as make test-all / pre-push Python stage)
uv run kira test --all                     # Backends + web-app Vitest
uv run kira test --all --coverage --no-web # Coverage gate (same as make test-coverage)
```

Or with Make (each target delegates to `kira`):

```bash
make test-identity-service
make test-all
make test-coverage
```

### Frontend Tests

```bash
cd web-app && bun run test               # Vitest
# Or from root:
uv run kira test --web
make test-web
```

### Linting

```bash
# Same gate as Husky after lint-staged (full monorepo)
uv run kira lint --all

# Backend (single service)
cd services/identity-service && uv run ruff check . && uv run ruff format --check .

# Frontend only
cd web-app && bun run lint
```

### Integration Tests

```bash
uv run kira test --integration   # Starts Postgres/Redis/Kafka via Compose, runs pytest -m integration, tears down
make test-integration            # Same (thin Make wrapper)
```

---

## 11. Git push and pre-push tests

Before **`git push`**, Husky runs **`make test-pre-push`** (Python services, web Vitest, integration). To choose what runs and avoid double work, use **`uv run kira push`** (interactive by default). Skip env vars (`SKIP_TEST_*`) are documented in **[Git, Husky hooks, and pushes](../contributing/git-hooks-and-pushes.md)**.

---

## 12. Make a Commit

KIRA uses Conventional Commits enforced by Husky + Commitlint.

```bash
git add .
uv run kira commit       # Interactive Commitizen prompt
# Or:
git commit               # Pre-commit hook runs lint-staged; commit-msg hook runs commitlint
```

Valid prefixes: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.

---

## 13. Observability Stack (Optional)

```bash
uv run kira dev up --full
uv run kira dashboards --full   # or --all
```

| Tool             | URL                    | Credentials / notes |
| ---------------- | ---------------------- | ------------------- |
| **Grafana**      | http://localhost:3001  | Anonymous **Viewer**; **Sign in** as `admin` / `admin` to edit |
| **Prometheus**   | http://localhost:9090  | No auth (local dev) |
| **Loki**         | http://localhost:3100  | API only; use Grafana → Explore → Loki |
| **Kafka UI**     | http://localhost:8080  | No login |
| **Redis Insight**| http://localhost:5540  | Add Redis manually (see [Dev dashboards](./dev-dashboards.md)) |
| **pgAdmin**      | http://localhost:5050  | `admin@kira.dev` / `admin` |
| **Portainer**    | http://localhost:9000  | Local admin password — [Dev dashboards & ports](./dev-dashboards.md) |
| **Alloy UI**     | http://localhost:12345 | Log pipeline debug UI |

---

## 14. Stop & Clean Up

```bash
uv run kira dev down              # Stop containers (keep data)
uv run kira dev clean             # Stop + remove volumes (prompts for confirmation)
uv run kira dev clean --yes       # Non-interactive (same as make clean)
```

---

## Troubleshooting

| Problem                        | Solution                                           |
| ------------------------------ | -------------------------------------------------- |
| Kafka crash / OOM              | Increase Docker Desktop memory to 8 GB+            |
| Port already in use            | `lsof -i :<port>` to find the process, kill it     |
| Postgres connection refused    | `uv run kira dev status` — wait for healthy        |
| Migration fails                | Ensure Postgres is running and `.env.local` exists |
| `kira: command not found`      | Use `uv run kira` (not just `kira`)                |
| `Failed to spawn: kira` / `No such file or directory` | You are inside `services/*` (or another nested project). `cd` to the repo root, or run `./bin/kira …`, or `uv run --project "$(git rev-parse --show-toplevel)" kira …`, or install once with `uv tool install --editable .` from the clone root so `kira` is on your PATH ([CLI Reference](./cli-reference.md#installation)). |
| Stale data after branch switch | `uv run kira dev clean` then re-setup              |

---

## Quick Reference

```bash
# Daily workflow
uv run kira dev up              #  |  make up
uv run kira dev status          #  |  make stack-status
uv run kira test --all --no-web #  |  make test-all
uv run kira test --web          #  |  make test-web
uv run kira commit              #  (no make alias)
uv run kira dev down            #  |  make down

# After pulling new code
uv run kira migrate --all --docker   #  |  make migrate-docker-all
uv run kira dev down && uv run kira dev up   #  |  make down && make up

# Full reset (host setup path)
uv run kira dev clean           # prompts  |  make clean → kira dev clean --yes
uv run kira dev setup           #  |  make dev-setup
```
