---
title: Makefile, CLI, and Compose
description: How kira, Make, and docker compose fit together — compose files, profiles, workers, and day-to-day workflows.
sidebar_position: 9
---

# Makefile, CLI, and Compose

You can run the same work through **`uv run kira`**, plain **`kira`** (after `uv tool install --editable .` from the repo root), **`make`**, or raw **`docker compose`**. This page explains how they relate so you can pick the shortest path and debug when something disagrees.

---

## CLI + Make in docs and copy-paste blocks

Across this site, when **both** interfaces exist you will usually see:

1. **`uv run kira …`** first (or **`kira …`** on your PATH) — this is the **source of truth** (`cli/`).
2. **`make …`** on the next line or as a comment — same behavior from the **repo root** (thin Makefile wrapper).

**CLI-only today (no `make` alias):** for example **`kira dev init`** (per-developer DB override). Use **`uv run kira dev init`** or **`./bin/kira dev init`**.

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

The **`kira`** CLI builds the same `docker compose -f …` commands (absolute paths) so you do not have to remember them. The **Makefile** is a **thin wrapper** around `uv run kira …` for muscle memory, CI, and tools that only know `make`.

---

## `kira` vs `make` — do you need both?

**No.** For your own workflow you can use **only** `uv run kira` (plus raw **`docker compose`** when you need something ad hoc).

**Yes, keep Make in the repo** for discoverability (`make help`), Husky (`make test-pre-push`), CI that already calls `make …`, and contributors who prefer four-letter commands. Every common `make` target delegates to the CLI.

| You want | Prefer |
|----------|--------|
| One-shot bootstrap (envs, deps, infra, migrate, seed on **host** DB) | `uv run kira dev setup` — same as `make dev-setup` |
| Bring up **core** stack in Docker | `uv run kira dev up` or `make up` |
| Core **+** Grafana/Prometheus/Loki/… | `uv run kira dev up --full` or `make up-full` |
| Setup **then** full stack (automation) | `uv run kira dev e2e` |
| First-time **Docker-only** DB path | `uv run kira dev bootstrap` or `make bootstrap` |
| Open browser tabs | `uv run kira dashboards` / `--full` |
| Tail logs | `uv run kira dev logs [service]` |
| Container list | `uv run kira dev status` |
| Wipe volumes | `uv run kira dev clean` (prompts) or `make clean` / `kira dev clean --yes` (no prompt) |

---

## Makefile targets (reference)

Each target runs the **`uv run kira …`** command in the second column (same effect from the repo root).

| Target | Under the hood |
|--------|----------------|
| `make up` | `uv run kira dev up` |
| `make up-full` | `uv run kira dev up --full` |
| `make down` | `uv run kira dev down` |
| `make clean` | `uv run kira dev clean --yes` |
| `make logs` / `make logs-<service>` | `uv run kira dev logs` / `… logs <service>` |
| `make stack-status` | `uv run kira dev status` |
| `make test-<service>` | `uv run kira test <service>` |
| `make test-all` | `uv run kira test --all --no-web` |
| `make test-web` | `uv run kira test --web` |
| `make test-coverage` | `uv run kira test --all --coverage --no-web` |
| `make test-integration` | `uv run kira test --integration` |
| `make test-pre-push` | Shell orchestrator calling the three test targets above (skip envs; see `.husky/pre-push`) |
| `make migrate-<service>` | `uv run kira migrate <service>` |
| `make migrate-all` | `uv run kira migrate --all` |
| `make migrate-docker-<service>` | `uv run kira migrate <service> --docker` |
| `make migrate-docker-all` | `uv run kira migrate --all --docker` |
| `make seed` | `uv run kira seed` |
| `make seed-docker` | `uv run kira seed --docker` |
| `make bootstrap` | `uv run kira dev bootstrap` |
| `make wait-postgres` | `uv run kira dev wait-postgres` |
| `make superadmin` | `uv run kira seed superadmin` |
| `make dashboards` / `make dashboards-full` | `uv run kira dashboards` / `… --full` |
| `make docs-dev` / `docs-build` / `docs-docker-up` | `uv run kira docs dev` / `build` / `docker-up` |
| `make dev-setup` | `uv run kira dev setup` |
| `make help` | Printed catalog (also lists CLI equivalents) |

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
