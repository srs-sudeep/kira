---
title: Local Docker Development
description: How docker/docker-compose.yml powers the full KIRA stack locally — service by service, volumes, hot reload, and useful commands.
sidebar_position: 1
---

# Local Docker Development

:::tip Prefer the CLI for everyday commands
**`uv run kira dev up`**, **`kira dev up --full`**, **`kira dev logs`**, **`kira migrate --all --docker`**, and **`kira dev bootstrap`** apply the same Compose files documented here (with absolute **`-f`** paths). The root **`Makefile`** is optional thin wrappers around those commands — see [Makefile, CLI, and Compose](../getting-started/makefile-and-cli.md).
:::

**What you'll learn:**

- How this file fits with **`kira` / Make** (see [Makefile, CLI, and Compose](../getting-started/makefile-and-cli.md))
- All **Compose files** under `docker/` (core, observability, optional dummy OTA, per-developer override)
- What every service in `docker/docker-compose.yml` does and why
- How `docker/docker-compose.observability.yml` adds monitoring dashboards
- How volume mounts enable hot reload without rebuilding images
- The commands you'll use every day

---

## Compose files under `docker/`

| File | Purpose | Committed? |
| ---- | ------- | ---------- |
| **`docker-compose.yml`** | Core stack — Postgres, Redis, Kafka, Mailhog, Kong, six APIs, web-app, Celery workers, optional **docs** / **tools** profiles | Yes |
| **`docker-compose.observability.yml`** | Grafana, Prometheus, Loki, Grafana Alloy, pgAdmin, Redis Insight, Kafka UI, Portainer, exporters | Yes |
| **`docker-compose.dummy-ota.yml`** | Optional **dummy OTA** HTTP server for local channel testing (`dummy-ota` on `kira_kira-net`, host **127.0.0.1:18080**) | Yes |
| **`docker-compose.override.yml`** | Per-developer merge (e.g. isolated `POSTGRES_DB` / `DATABASE_URL`) | **No** — gitignored; each dev creates their own |
| **`docker-compose.override.yml.example`** | Template for the override above; documents env shape and copy commands | Yes |

The observability merge file is for **local development** only. In **production** on AWS, the default path is **CloudWatch** (metrics + logs), not a second copy of this Compose stack — see [AWS production — Step 9](./aws-production.md#step-9-observability--development-vs-production).

Compose **auto-merges** `docker-compose.override.yml` when it sits beside the `-f` file you pass (same directory). Use the **`.example`** as the source of truth for what to put in your personal override — see [Per-developer database isolation](../getting-started/per-developer-db.md).

**Dummy OTA** is a separate merge so the main stack stays lean. Bring up the core network first, then:

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dummy-ota.yml up -d dummy-ota
```

Start the core stack from the **repository root**:

```bash
uv run kira dev up
# Make: make up
# Raw Compose (same files):
docker compose -f docker/docker-compose.yml up -d --build
```

Start with observability dashboards:

```bash
uv run kira dev up --full
# Make: make up-full
docker compose -f docker/docker-compose.yml -f docker/docker-compose.observability.yml up -d --build
```

---

## Infrastructure Services

### postgres

```yaml
image: postgres:16
ports: ["5432:5432"]
volumes: [pgdata:/var/lib/postgresql/data]
```

Single database named `kira`. All six services connect to this instance but use separate schemas (`tenant_{uuid}`). The `pgdata` named volume persists data between `docker compose down` restarts — use `docker compose down -v` to wipe it.

Healthcheck: `pg_isready -U postgres -d kira`. App services wait for this to pass before starting.

### redis

```yaml
image: redis:7-alpine
command: redis-server --requirepass redis-local-dev
ports: ["6379:6379"]
volumes: [redisdata:/data]
```

Shared Redis instance. Compose assigns a **different logical DB index (0–5)** per app service (see each service’s `REDIS_URL` in `docker/docker-compose.yml`). Celery workers reuse their parent service’s Redis URL (e.g. channel-worker uses the same index as channel-engine).

### kafka

```yaml
image: confluentinc/cp-kafka:7.6.0
ports: ["9092:9092"]
```

Runs in KRaft mode (no ZooKeeper). Single broker, `KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"` so topics are created on first publish. The `CLUSTER_ID` is fixed so the cluster identity survives restarts.

Healthcheck: `kafka-topics --bootstrap-server localhost:9092 --list`. channel-engine and notification-service wait for this before starting.

### mailhog

```yaml
image: mailhog/mailhog
ports: ["1025:1025", "8025:8025"]
```

Local SMTP server. All outbound emails from notification-service land here instead of being sent for real. Open `http://localhost:8025` to see the inbox.

### kong

```yaml
image: kong:3.6
ports: ["8000:8000", "8100:8001"]
```

API gateway in DB-less mode (`KONG_DATABASE: "off"`). Config is loaded from `./kong/kong.yml` mounted read-only. Port 8000 is the proxy (client requests), port 8100 is the admin API (read-only in local dev).

---

## Application Services

All six FastAPI services follow the same pattern (paths are **relative to `docker/docker-compose.yml`**):

```yaml
build:
  context: ../services/<name>
  dockerfile: ../../docker/<name>.Dockerfile
env_file: ../services/<name>/.env.local
ports: ["800X:800X"]
volumes:
  - ../services/<name>:/app
  - ../shared:/app/shared
command: uvicorn app.main:app --host 0.0.0.0 --port 800X --reload
```

Key points:

- **Build context is the service directory** (`../services/<name>` from `docker/`), with a Dockerfile under `docker/`, so buildx resolves paths correctly.
- **`env_file`** loads from `.env.local` — copy from `.env.example` in each service directory.
- **`--reload`** enables hot reload. Any change to Python files triggers an automatic restart.

| Service                | Port | Notes                               |
| ---------------------- | ---- | ----------------------------------- |
| identity-service       | 8001 | Depends on postgres + redis only    |
| rate-inventory-service | 8002 | Depends on postgres + redis only    |
| reservation-service    | 8003 | Depends on postgres + redis only    |
| channel-engine         | 8004 | Depends on postgres + redis + kafka |
| notification-service   | 8005 | Depends on postgres + redis + kafka |
| admin-service          | 8006 | Depends on postgres + redis only    |

---

## Celery Workers

```yaml
channel-worker:
  command: celery -A app.tasks worker --loglevel=info --queues=channel

notification-worker:
  command: celery -A app.tasks worker --loglevel=info --queues=notifications
```

Workers use the **same Docker image** as their parent service — same code, different entrypoint. Both use the same **`../services/<name>:/app`** style bind mounts as the API containers so code changes apply without rebuilding. Workers use Redis for the Celery broker and result backend per service config.

---

## Volume Mounts and Hot Reload

Typical mounts on app services (paths relative to `docker/docker-compose.yml`):

```yaml
volumes:
  - ../services/identity-service:/app
  - ../shared:/app/shared
```

When you edit Python under `services/<name>/` or `shared/`, uvicorn `--reload` restarts the process. **No rebuild required.**

The exception: changes to `pyproject.toml` or `poetry.lock` (dependency changes) require a rebuild:

```bash
docker compose -f docker/docker-compose.yml up -d --build identity-service
```

---

## Profiles

**`docs-site`** is behind the **`docs`** profile so a plain `up` does not rebuild the static site every time:

```yaml
docs-site:
  profiles: [docs]
```

The **`web-app`** Vite dev server starts with the default stack (no profile).

The **`seed-data`** helper uses the **`tools`** profile (`docker compose --profile tools run --rm seed-data`).

Start the docs container when you need it:

```bash
docker compose -f docker/docker-compose.yml --profile docs up -d docs-site
```

---

## Web app and docs ports

| Where | Port | Notes |
| ----- | ---- | ----- |
| **web-app** (Vite in Docker) | **3000** | Compose sets `PORT=3000`; see `web-app/vite.config.ts` (`PORT` / `VITE_DEV_PORT`). |
| **docs-site** (nginx in Docker) | **4000** | Host `4000` → container `80`. Host dev: `bun run start` in `docs-site/` also uses **4000**. |

---

## Observability Stack

Launched by merging **`docker/docker-compose.observability.yml`** with the core file (same project name `kira`, same `kira-net` network — Compose merges the network so observability containers reach Postgres, Redis, Kafka, and the APIs):

| Service        | Port | Purpose                                                                                              |
| -------------- | ---- | ---------------------------------------------------------------------------------------------------- |
| Prometheus     | 9090 | Scrapes `/metrics` from all services                                                                 |
| Grafana        | 3001 | Dashboards — anonymous Viewer; **Sign in** `admin` / `admin` to edit ([dev dashboards](../getting-started/dev-dashboards.md)) |
| Loki           | 3100 | Log aggregation                                                                                      |
| Grafana Alloy  | 12345 | Ships Docker container logs to Loki (replaces EOL Promtail)                                         |
| pgAdmin        | 5050 | PostgreSQL GUI — `admin@kira.dev` / `admin` ([dev dashboards](../getting-started/dev-dashboards.md)) |
| Redis Insight  | 5540 | Redis key browser                                                                                    |
| Kafka UI       | 8080 | Topic browser, consumer group lag                                                                    |
| Portainer      | 9000 / 9443 | HTTP **9000** or HTTPS **9443** — see [dev dashboards](../getting-started/dev-dashboards.md) for the local admin password |

---

## Useful Commands

**View logs for one service:**

```bash
docker compose -f docker/docker-compose.yml logs -f identity-service
```

**View logs for all services, last 100 lines:**

```bash
docker compose -f docker/docker-compose.yml logs --tail=100 -f
```

**Restart one service (picks up code changes that require a restart):**

```bash
docker compose -f docker/docker-compose.yml restart channel-engine
```

**Rebuild and restart one service (after dependency changes):**

```bash
docker compose -f docker/docker-compose.yml up -d --build rate-inventory-service
```

**Run a one-off command inside a container:**

```bash
docker compose -f docker/docker-compose.yml exec identity-service uv run alembic upgrade head
docker compose -f docker/docker-compose.yml exec identity-service uv run pytest -v
```

**Stop everything, keep volumes:**

```bash
docker compose -f docker/docker-compose.yml down
```

**Stop everything, delete all data volumes:**

```bash
docker compose -f docker/docker-compose.yml down -v
```

**See resource usage per container:**

```bash
docker stats
```

---

## Troubleshooting

:::warning Port already in use
If a port is taken, find and stop the conflicting process or change the host-side port in `docker/docker-compose.yml` (e.g., `"8002:8002"` → `"18002:8002"`).
:::

:::tip Service keeps restarting
Run `docker compose logs <service>` immediately after `up`. The most common causes are: missing `.env.local` file, wrong `DATABASE_URL`, or postgres not yet healthy when the service first connected.
:::

:::note Changes to shared/ not picked up
Confirm `./shared:/app/shared` is in the service's volumes. If `shared/` was added after the container was created, run `docker compose up -d` (without `--build`) to recreate the container with the updated mount.
:::
