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
uv run kira dev setup   # installs deps, starts infra, migrates, seeds
uv run kira dev up      # starts all services + web app
open http://localhost:3000
```

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

You should see commands: `commit`, `dashboards`, `dev`, `test`, `migrate`, `seed`, `deploy`, `docs`.

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

Optional but recommended when multiple developers share a machine:

```bash
uv run kira dev init --name alice
```

This creates `docker/docker-compose.override.yml` pointing all services to `kira_alice` instead of `kira`.

---

## 6. (Manual) Start Infrastructure

```bash
uv run kira dev up
# Or directly:
docker compose -f docker/docker-compose.yml up -d postgres redis kafka
```

Wait for health checks:

```bash
uv run kira dev status
# All infra containers should show "healthy"
```

---

## 7. (Manual) Run Database Migrations

```bash
uv run kira migrate --all --docker
```

This runs Alembic `upgrade head` inside each running service container. Alternatively, run migrations on the host (requires Postgres on localhost:5432):

```bash
uv run kira migrate --all
```

---

## 8. (Manual) Seed Development Data

```bash
uv run kira seed --docker
```

Seeds: super-admin user (`admin@example.com` / `Admin1234!`), sample tenants, room types, rate plans, and test reservations.

---

## 9. Start the Full Stack

```bash
uv run kira dev up          # Core: 6 services + Kong + web-app + infra
uv run kira dev up --full   # Core + observability (Grafana, Prometheus, Loki, etc.)
```

Verify everything is healthy:

```bash
uv run kira dev status
```

| Service                | URL                        | Notes                             |
| ---------------------- | -------------------------- | --------------------------------- |
| **Web App**            | http://localhost:3000      | React + Vite dev server           |
| **Kong Gateway**       | http://localhost:8000      | API gateway (proxies to services) |
| **Identity API**       | http://localhost:8001/docs | Swagger UI                        |
| **Rate/Inventory API** | http://localhost:8002/docs | Swagger UI                        |
| **Reservation API**    | http://localhost:8003/docs | Swagger UI                        |
| **Channel Engine API** | http://localhost:8004/docs | Swagger UI                        |
| **Notification API**   | http://localhost:8005/docs | Swagger UI                        |
| **Admin API**          | http://localhost:8006/docs | Swagger UI                        |
| **Mailhog**            | http://localhost:8025      | Catches outgoing emails           |

Open all dashboards at once:

```bash
uv run kira dashboards
```

---

## 10. Run Tests

### Backend Tests (per service)

```bash
uv run kira test identity-service        # Single service
uv run kira test --all                   # All 6 services
uv run kira test --all --coverage        # With coverage (fail < 70%)
```

Or with Make:

```bash
make test-identity-service
make test-all
make test-coverage
```

### Frontend Tests

```bash
cd web-app && bun run test               # Vitest
# Or from root:
make test-web
```

### Linting

```bash
# Backend (per service)
cd services/identity-service && uv run ruff check . && uv run ruff format --check .

# Frontend
cd web-app && bun run lint
```

### Integration Tests

```bash
make test-integration    # Requires running infra containers
```

---

## 11. Make a Commit

KIRA uses Conventional Commits enforced by Husky + Commitlint.

```bash
git add .
uv run kira commit       # Interactive Commitizen prompt
# Or:
git commit               # Pre-commit hook runs lint-staged; commit-msg hook runs commitlint
```

Valid prefixes: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.

---

## 12. Observability Stack (Optional)

```bash
uv run kira dev up --full
uv run kira dashboards --full
```

| Tool           | URL                    | Credentials                          |
| -------------- | ---------------------- | ------------------------------------ |
| **Grafana**    | http://localhost:3001  | Anonymous viewer, or `admin`/`admin` |
| **Prometheus** | http://localhost:9090  | —                                    |
| **Kafka UI**   | http://localhost:8080  | —                                    |
| **pgAdmin**    | http://localhost:5050  | `admin@kira.dev` / `admin`           |
| **Portainer**  | http://localhost:9000  | `admin` / `adminadmin`               |
| **Alloy UI**   | http://localhost:12345 | —                                    |

---

## 13. Stop & Clean Up

```bash
uv run kira dev down     # Stop containers (keep data)
uv run kira dev clean    # Stop + remove volumes (fresh start)
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
| Stale data after branch switch | `uv run kira dev clean` then re-setup              |

---

## Quick Reference

```bash
# Daily workflow
uv run kira dev up              # Start stack
uv run kira dev status          # Check health
uv run kira test --all          # Run tests
uv run kira commit              # Commit with Conventional Commits
uv run kira dev down            # End of day

# After pulling new code
uv run kira migrate --all --docker
uv run kira dev down && uv run kira dev up

# Full reset
uv run kira dev clean
uv run kira dev setup
```
