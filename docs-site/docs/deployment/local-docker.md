---
title: Local Docker Development
description: How docker-compose.yml powers the full KIRA stack locally — service by service, volumes, hot reload, and useful commands.
sidebar_position: 1
---

# Local Docker Development

**What you'll learn:**
- What every service in `docker-compose.yml` does and why
- How `docker-compose.observability.yml` adds monitoring dashboards
- How volume mounts enable hot reload without rebuilding images
- The commands you'll use every day

---

## Two Compose Files

KIRA's local environment is split into two compose files:

| File | Purpose | When to use |
|---|---|---|
| `docker-compose.yml` | Core stack — all services, infra, gateway | Always |
| `docker-compose.observability.yml` | Prometheus, Grafana, Loki, pgAdmin, Kafka UI | When debugging metrics/logs |

Start the core stack:

```bash
docker compose up -d --build
```

Start with observability dashboards:

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d --build
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
ports: ["6379:6379"]
volumes: [redisdata:/data]
```

Shared Redis instance. Each service uses a different database number (0–5) to avoid key collisions:

| DB | Usage |
|---|---|
| 0 | identity-service — sessions, rate limiting |
| 1 | Celery broker (task queue) |
| 2 | Celery result backend |
| 3 | channel-engine — circuit breaker, rate limiting |
| 4 | notification-service |
| 5 | admin-service |

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

All six FastAPI services follow the same pattern:

```yaml
build:
  context: .
  dockerfile: services/<name>/Dockerfile
env_file: ./services/<name>/.env.local
ports: ["800X:800X"]
volumes:
  - ./services/<name>/app:/app/app
  - ./shared:/app/shared
command: uvicorn app.main:app --host 0.0.0.0 --port 800X --reload
```

Key points:
- **Build context is the repo root** (`.`), not the service directory. This is required because Dockerfiles `COPY` the `shared/` directory.
- **`env_file`** loads from `.env.local` — copy from `.env.example` in each service directory.
- **`--reload`** enables hot reload. Any change to Python files triggers an automatic restart.

| Service | Port | Notes |
|---|---|---|
| identity-service | 8001 | Depends on postgres + redis only |
| rate-inventory-service | 8002 | Depends on postgres + redis only |
| reservation-service | 8003 | Depends on postgres + redis only |
| channel-engine | 8004 | Depends on postgres + redis + kafka |
| notification-service | 8005 | Depends on postgres + redis + kafka |
| admin-service | 8006 | Depends on postgres + redis only |

---

## Celery Workers

```yaml
channel-worker:
  command: celery -A app.tasks worker --loglevel=info --queues=channel

notification-worker:
  command: celery -A app.tasks worker --loglevel=info --queues=notifications
```

Workers use the **same Docker image** as their parent service — same code, different entrypoint. Both use `./services/<name>/app:/app/app` volume mounts so code changes apply to workers without rebuilding. Workers use Redis DB 1 as the Celery broker and DB 2 for results.

---

## Volume Mounts and Hot Reload

Two mounts on every app service enable live code changes:

```yaml
volumes:
  - ./services/identity-service/app:/app/app    # service-specific code
  - ./shared:/app/shared                         # shared utilities, schemas, middleware
```

When you edit any `.py` file in `services/<name>/app/` or `shared/`, uvicorn detects the change and reloads the process. **No rebuild required.**

The exception: changes to `pyproject.toml` or `poetry.lock` (dependency changes) require a rebuild:

```bash
docker compose up -d --build identity-service
```

---

## Profiles

Two services are behind Docker Compose profiles and don't start with the default `up` command:

```yaml
web-app:
  profiles: [frontend]

docs-site:
  profiles: [docs]
```

Start them explicitly:

```bash
# Start frontend dev server
docker compose --profile frontend up -d web-app

# Start docs site
docker compose --profile docs up -d docs-site
```

---

## Observability Stack

Launched by merging `docker-compose.observability.yml`:

| Service | Port | Purpose |
|---|---|---|
| Prometheus | 9090 | Scrapes `/metrics` from all services |
| Grafana | 3001 | Dashboards — default login admin/admin |
| Loki | 3100 | Log aggregation (receives from Promtail) |
| Promtail | — | Ships Docker container logs to Loki |
| pgAdmin | 5050 | PostgreSQL GUI — login admin@kira.local / admin |
| Redis Insight | 5540 | Redis key browser |
| Kafka UI | 8080 | Topic browser, consumer group lag |
| Portainer | 9443 | Docker container management UI |

The observability stack joins the `kira_kira-net` network (set `external: true`) so it can reach the app services.

---

## Useful Commands

**View logs for one service:**

```bash
docker compose logs -f identity-service
```

**View logs for all services, last 100 lines:**

```bash
docker compose logs --tail=100 -f
```

**Restart one service (picks up code changes that require a restart):**

```bash
docker compose restart channel-engine
```

**Rebuild and restart one service (after dependency changes):**

```bash
docker compose up -d --build rate-inventory-service
```

**Run a one-off command inside a container:**

```bash
docker compose exec identity-service uv run alembic upgrade head
docker compose exec identity-service uv run pytest -v
```

**Stop everything, keep volumes:**

```bash
docker compose down
```

**Stop everything, delete all data volumes:**

```bash
docker compose down -v
```

**See resource usage per container:**

```bash
docker stats
```

---

## Troubleshooting

:::warning Port already in use
If a port is taken, find and stop the conflicting process or change the host-side port in `docker-compose.yml` (e.g., `"8002:8002"` → `"18002:8002"`).
:::

:::tip Service keeps restarting
Run `docker compose logs <service>` immediately after `up`. The most common causes are: missing `.env.local` file, wrong `DATABASE_URL`, or postgres not yet healthy when the service first connected.
:::

:::note Changes to shared/ not picked up
Confirm `./shared:/app/shared` is in the service's volumes. If `shared/` was added after the container was created, run `docker compose up -d` (without `--build`) to recreate the container with the updated mount.
:::
