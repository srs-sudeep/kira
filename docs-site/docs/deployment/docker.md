---
sidebar_position: 2
---

# Docker

## Local Development with Docker Compose

The `docker-compose.yml` at the repo root orchestrates all services for local development.

### Services Defined

| Service | Image | Port |
|---|---|---|
| `postgres` | `postgres:16-alpine` | 5432 |
| `redis` | `redis:7-alpine` | 6379 |
| `zookeeper` | `confluentinc/cp-zookeeper:7.5.0` | 2181 |
| `kafka` | `confluentinc/cp-kafka:7.5.0` | 9092 |
| `kong` | `kong:3.4-alpine` | 8000, 8443, 8001 (admin) |
| `identity-service` | `./services/identity-service` | 8001 |
| `rate-inventory-service` | `./services/rate-inventory-service` | 8002 |
| `reservation-service` | `./services/reservation-service` | 8003 |
| `channel-engine` | `./services/channel-engine` | 8004 |
| `channel-engine-worker` | `./services/channel-engine` | — |
| `notification-service` | `./services/notification-service` | 8005 |
| `admin-service` | `./services/admin-service` | 8006 |
| `web-app` | `./web-app` | 3000 |

### Hot Reload

Service source code is volume-mounted for hot reload during development:

```yaml
volumes:
  - ./services/identity-service/app:/app/app
```

Changes to Python files reload uvicorn automatically (`--reload` flag).

## Backend Dockerfile

Each backend service uses a two-stage build:

```dockerfile
# Stage 1: Install dependencies
FROM python:3.13-slim AS builder
WORKDIR /build
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main

# Stage 2: Runtime image
FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY app/ ./app/
EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

## Frontend Dockerfile

The web-app uses a bun build stage and nginx runtime:

```dockerfile
# Stage 1: Build
FROM oven/bun:1 AS builder
WORKDIR /app
COPY package.json bun.lockb ./
RUN bun install --frozen-lockfile
COPY . .
ARG VITE_API_BASE_URL
RUN bun run build

# Stage 2: Serve with nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost/health || exit 1
```

The `VITE_API_BASE_URL` build arg is baked into the static bundle at build time. In CI, it's set to the Kong gateway URL for the target environment.

## Observability Stack

```bash
# Start with Prometheus, Grafana, Loki, Jaeger
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d --build
```

Additional services:
- `prometheus` — metrics scraper (port 9090)
- `grafana` — dashboards (port 3001)
- `loki` — log aggregation (port 3100)
- `jaeger` — distributed tracing (port 16686)
