---
title: Makefile, CLI, and Compose
description: How kira, Make, and docker compose fit together — compose files, profiles, workers, and day-to-day workflows.
sidebar_position: 9
---

# Makefile, CLI, and Compose

You can run the same work through **`uv run kira`**, plain **`kira`** (after `uv tool install --editable .` from the repo root), **`make`**, or raw **`docker compose`**. This page explains how they relate so you can pick the shortest path and debug when something disagrees.

---

## Compose files (source of truth)

| File | Role |
|------|------|
| `docker/docker-compose.yml` | **Core** — Postgres, Redis, Kafka, Mailhog, six API services, Kong, **web-app**, Celery **channel-worker** and **notification-worker**, optional **docs-site** (`docs` profile), **seed-data** (`tools` profile). |
| `docker/docker-compose.observability.yml` | **Observability** — Grafana, Prometheus, Loki, Grafana Alloy, pgAdmin, Redis Insight, Kafka UI, Portainer, exporters. |
| `docker/docker-compose.dummy-ota.yml` | **Optional dummy OTA** — merge with core when you need the fake OTA server on the same Docker network (`127.0.0.1:18080` on the host). |
| `docker/docker-compose.override.yml` | **Per-developer** — auto-merged next to the core file when present; **gitignored** (DB name isolation, local tweaks). |
| `docker/docker-compose.override.yml.example` | **Committed template** for that override — copy or use `kira dev init`; see [Per-developer database isolation](./per-developer-db.md). |

From the **repo root**, Compose almost always needs an explicit compose file path for the **base** file:

```bash
docker compose -f docker/docker-compose.yml up -d
docker compose -f docker/docker-compose.yml -f docker/docker-compose.observability.yml up -d
```

If `docker/docker-compose.override.yml` exists, Compose loads it **automatically** (same directory as the first `-f` file).

The **Makefile** and **`kira`** CLI embed these `-f` paths so you do not have to remember them.

---

## `kira` vs `make` — do you need both?

**No.** For your own workflow you can use **only** `kira` (plus `docker compose` when you need something ad hoc).

**Yes, keep Make in the repo** for discoverability (`make help`), CI or scripts that call `make test-all`, and contributors who prefer four-letter commands.

| You want | Prefer |
|----------|--------|
| One-shot bootstrap (envs, deps, infra, migrate, seed on **host** DB) | `uv run kira dev setup` — same idea as `make dev-setup` |
| Bring up **core** stack in Docker | `uv run kira dev up` or `make up` |
| Core **+** Grafana/Prometheus/Loki/… | `uv run kira dev up --full` or `make up-full` |
| Setup **then** full stack (automation) | `uv run kira dev e2e` |
| First-time **Docker-only** DB path | `make bootstrap` (= `up-full` → wait Postgres → `migrate-docker-all` → `seed-docker`) — overlaps `setup` + `up` but migrations run **inside** containers |
| Open browser tabs | `uv run kira dashboards` / `--full` — `make dashboards` delegates here |
| Tail logs | `uv run kira dev logs [service]` — `make logs` / `make logs-<service>` |
| Container list | `uv run kira dev status` — `make stack-status` |
| Wipe volumes | `uv run kira dev clean` (asks confirmation) — `make clean` (no prompt; uses full compose files) |

---

## Makefile targets (reference)

| Target | What it does |
|--------|----------------|
| `make up` | Core stack `up -d --build` |
| `make up-full` | Core + observability `up -d --build` |
| `make down` | `down` on **both** compose files (keeps volumes) |
| `make clean` | `down -v --remove-orphans` on both files |
| `make logs` / `make logs-<service>` | `docker compose … logs -f` |
| `make stack-status` | `docker compose … ps -a` |
| `make test-<service>` | `cd services/<service> && uv run pytest -v` |
| `make test-all` | All six services sequentially |
| `make test-web` | Vitest in `web-app/` |
| `make test-coverage` | Pytest with coverage gate per service |
| `make test-integration` | `scripts/test_integration.sh` |
| `make migrate-<service>` | Host: Poetry env + `alembic upgrade head` in that service |
| `make migrate-all` | Host migrations for all services |
| `make migrate-docker-<service>` | `compose exec <service> python -m alembic upgrade head` |
| `make migrate-docker-all` | Same for all six services |
| `make seed` | Host: `uv run python scripts/seed_data.py` (Postgres on `localhost:5432`) |
| `make seed-docker` | One-off `seed-data` container (`--profile tools`) |
| `make bootstrap` | `up-full` → wait Postgres → `migrate-docker-all` → `seed-docker` |
| `make wait-postgres` | Poll `pg_isready` in Postgres container |
| `make superadmin` | Interactive `scripts/create_superadmin.py` on host |
| `make dashboards` / `make dashboards-full` | `uv run kira dashboards` / `--full` |
| `make docs-dev` / `docs-build` / `docs-docker-up` | Docusaurus or static docs in Docker (`--profile docs`) |
| `make dev-setup` | `uv run kira dev setup` |
| `make help` | Short catalog of targets |

Run **`make help`** anytime for the in-terminal summary.

---

## What actually runs in Docker (core)

Besides the six HTTP services on **8001–8006**:

- **Kong** — **8000** proxy, **8100** admin API (mapped from Kong’s internal 8001).
- **web-app** — Vite on **3000** (`PORT=3000` in Compose).
- **channel-worker** / **notification-worker** — Celery; same **images** as channel-engine / notification-service but **no** uvicorn. Compose disables the image **HEALTHCHECK** for workers (the API image checks `localhost:<port>/health`, which does not exist in a worker-only container).
- **Mailhog** — **8025** UI, **1025** SMTP.
- **docs-site** — optional; **`docs`** profile; host **4000** → nginx **80**.
- **seed-data** — optional; **`tools`** profile; `make seed-docker` / Compose `--profile tools run --rm seed-data`.

Kafka-dependent APIs wait for **`kafka` healthy** where the app starts Kafka clients in lifespan (reservation, notification, channel, and rate-inventory producer).

---

## Profiles

| Profile | Services | How to start |
|---------|----------|--------------|
| *(default)* | Everything in the core file **except** docs-site and seed-data | `make up` / `kira dev up` |
| `docs` | **docs-site** | `make docs-docker-up` or `docker compose -f docker/docker-compose.yml --profile docs up -d docs-site` |
| `tools` | **seed-data** one-off | `make seed-docker` |

`kira dev up --full` passes **`--profile docs`** together with the observability compose file so the static docs container can start with the full stack if you want **:4000** without a separate command.

---

## Host vs container database access

| Flow | Postgres hostname | Typical command |
|------|---------------------|-----------------|
| **Host** migrations / seed (`kira dev setup`, `make migrate-all`, `make seed`) | `localhost` | Service `.env.local` must match (`postgres:5432` URL pointed at localhost). |
| **Docker** migrations / seed (`make migrate-docker-all`, `make seed-docker`) | `postgres` (service DNS) | Compose `environment` / `env_file` already use `postgres:5432`. |

If you see **connection refused** to Postgres, check whether the tool runs **on the host** or **inside a container** and that the DSN matches.

---

## Loki on :3100 returns 404

**Loki** is an HTTP **API**, not a dashboard. `http://localhost:3100/` often returns **404**. Use Grafana (**:3001**) → Explore → **Loki**, or call API paths such as `/ready` or `/metrics` for a quick check.

---

## Related docs

- [CLI Reference](./cli-reference.md) — every `kira` command and installation options.
- [E2E local dev](./e2e-local-dev.md) — happy path from clone to tests.
- [Local Docker](../deployment/local-docker.md) — service-by-service compose notes.
- [Dev dashboards & ports](./dev-dashboards.md) — URLs and sign-ins.
