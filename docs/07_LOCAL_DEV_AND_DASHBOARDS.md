# Local Development Setup — Mac Edition

## Table of Contents
1. Monorepo Git Strategy
2. Git Branching & Versioning
3. Docker Compose — Full Local Stack
4. Observability Dashboards
5. Makefile Shortcuts
6. Day-to-Day Workflow
7. Migrating to AWS Later

---

## 1. Monorepo Git Strategy

### Single repo, not separate repos

All code lives in ONE GitHub repository: `abodeatab-platform`. This is a monorepo.

```
abodeatab-platform/          ← ONE GitHub repo
├── services/
│   ├── identity-service/
│   ├── rate-inventory-service/
│   ├── reservation-service/
│   ├── channel-engine/
│   ├── notification-service/
│   └── admin-service/
├── web-app/
├── shared/
├── k8s/
├── docker/
│   ├── docker-compose.yml
│   └── docker-compose.observability.yml
├── Makefile
└── .github/workflows/
```

### Why monorepo, not polyrepo:

| Factor | Monorepo (what we do) | Polyrepo (separate repos) |
|--------|----------------------|--------------------------|
| Atomic changes | Change API + consumer in one PR | Need coordinated PRs across repos |
| Shared code | `shared/` folder, one import | Publish as npm/pip package, version hell |
| CI complexity | One repo, path-filtered workflows | 7+ repos, 7+ pipeline configs |
| Code search | One place to grep | Search across 7 repos |
| Onboarding | Clone once, run once | Clone 7 repos, configure 7 envs |
| Dependency updates | One PR updates everywhere | 7 PRs for a shared library change |

### When to consider splitting later:
Only if you have 5+ developers working on completely independent services AND deployment coordination becomes a bottleneck. For a team under 10, monorepo is strictly better.

---

## 2. Git Branching & Versioning

### Branch strategy: trunk-based with short-lived feature branches

```
main                          ← always deployable, protected branch
  └── feat/identity-auth      ← feature branch, lives 1-3 days max
  └── feat/rate-calendar      ← another feature branch
  └── fix/booking-duplicate   ← bugfix branch
  └── release/v1.0.0          ← release branch (optional, for production tags)
```

### Rules:
- `main` is protected — no direct pushes, PRs required with at least 1 review
- Feature branches are short-lived (1-3 days). Name: `feat/<service>-<feature>` or `fix/<service>-<bug>`
- CI runs on every PR (tests only the changed service — see path filters)
- Merge to `main` triggers build + deploy to local/staging
- Tags for releases: `v1.0.0`, `v1.1.0`, etc.

### Path-filtered CI — only build what changed:

```yaml
# .github/workflows/ci-identity-service.yml
on:
  push:
    branches: [main]
    paths:
      - 'services/identity-service/**'
      - 'shared/**'                     # Shared code changes trigger all services
  pull_request:
    paths:
      - 'services/identity-service/**'
      - 'shared/**'
```

If you only change `services/channel-engine/`, only the channel-engine CI runs. The other 6 don't even start. This keeps CI fast and cheap.

### Versioning strategy:

Each service has its own version in `pyproject.toml`:
```toml
# services/identity-service/pyproject.toml
[project]
name = "identity-service"
version = "1.2.0"
```

Docker images are tagged with the Git commit SHA:
```
identity-service:abc1234
rate-inventory-service:def5678
```

For production releases, also tag with semver:
```
identity-service:1.2.0
identity-service:abc1234    # both tags point to same image
```

---

## 3. Docker Compose — Full Local Stack

### Prerequisites on Mac:
```bash
# Install Docker Desktop for Mac (includes docker-compose)
brew install --cask docker

# Allocate resources in Docker Desktop settings:
# - CPUs: 4+
# - Memory: 8GB+ (recommended 12GB if your Mac has 16GB+)
# - Disk: 30GB+
```

### Main `docker/docker-compose.yml` (services + infrastructure):

```yaml
# docker/docker-compose.yml (paths relative to repo root in this excerpt)
services:

  # ── Infrastructure ──
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: abodeatab
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports: ["5432:5432"]
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    volumes: [redisdata:/data]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

  kafka:
    image: confluentinc/cp-kafka:7.6.0
    ports: ["9092:9092"]
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,HOST:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,HOST://localhost:9092
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:29093
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:29092,CONTROLLER://0.0.0.0:29093,HOST://0.0.0.0:9092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      CLUSTER_ID: "MkU3OEVBNTcwNTJENDM2Qk"
    volumes: [kafkadata:/var/lib/kafka/data]

  # ── Email trap (catches all outbound email locally) ──
  mailhog:
    image: mailhog/mailhog:latest
    ports:
      - "1025:1025"    # SMTP
      - "8025:8025"    # Web UI

  # ── API Gateway ──
  kong:
    image: kong:3.6
    environment:
      KONG_DATABASE: "off"
      KONG_DECLARATIVE_CONFIG: /etc/kong/kong.yml
      KONG_PROXY_LISTEN: 0.0.0.0:8000
      KONG_LOG_LEVEL: info
    volumes:
      - ./kong/kong.yml:/etc/kong/kong.yml
    ports:
      - "8000:8000"
    depends_on:
      identity-service: { condition: service_started }
      rate-inventory-service: { condition: service_started }
      reservation-service: { condition: service_started }

  # ── Application Services ──
  identity-service:
    build: { context: ./services/identity-service }
    ports: ["8001:8001"]
    env_file: ./services/identity-service/.env.local
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
    volumes:
      - ./services/identity-service/app:/app/app
      - ./shared:/app/shared
    command: uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

  rate-inventory-service:
    build: { context: ./services/rate-inventory-service }
    ports: ["8002:8002"]
    env_file: ./services/rate-inventory-service/.env.local
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
    volumes:
      - ./services/rate-inventory-service/app:/app/app
      - ./shared:/app/shared
    command: uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

  reservation-service:
    build: { context: ./services/reservation-service }
    ports: ["8003:8003"]
    env_file: ./services/reservation-service/.env.local
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
    volumes:
      - ./services/reservation-service/app:/app/app
      - ./shared:/app/shared
    command: uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload

  channel-engine:
    build: { context: ./services/channel-engine }
    ports: ["8004:8004"]
    env_file: ./services/channel-engine/.env.local
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
      kafka: { condition: service_started }
    volumes:
      - ./services/channel-engine/app:/app/app
      - ./shared:/app/shared
    command: uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload

  notification-service:
    build: { context: ./services/notification-service }
    ports: ["8005:8005"]
    env_file: ./services/notification-service/.env.local
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
    volumes:
      - ./services/notification-service/app:/app/app
      - ./shared:/app/shared
    command: uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload

  admin-service:
    build: { context: ./services/admin-service }
    ports: ["8006:8006"]
    env_file: ./services/admin-service/.env.local
    depends_on:
      postgres: { condition: service_healthy }
    volumes:
      - ./services/admin-service/app:/app/app
      - ./shared:/app/shared
    command: uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload

  # ── Celery Workers ──
  channel-worker:
    build: { context: ./services/channel-engine }
    env_file: ./services/channel-engine/.env.local
    depends_on: [redis, kafka, postgres]
    volumes:
      - ./services/channel-engine/app:/app/app
      - ./shared:/app/shared
    command: celery -A app.tasks.celery_app worker --loglevel=info -Q channel_tasks

  notification-worker:
    build: { context: ./services/notification-service }
    env_file: ./services/notification-service/.env.local
    depends_on: [redis]
    volumes:
      - ./services/notification-service/app:/app/app
      - ./shared:/app/shared
    command: celery -A app.tasks.celery_app worker --loglevel=info -Q notification_tasks

  # ── Frontend ──
  web-app:
    build: { context: ./web-app, target: dev }
    ports: ["3000:3000"]
    volumes:
      - ./web-app/src:/app/src
      - ./web-app/public:/app/public
    environment:
      VITE_API_BASE_URL: http://localhost:8000/api/v1
    command: npm run dev -- --host 0.0.0.0 --port 3000

volumes:
  pgdata:
  redisdata:
  kafkadata:
```

### Observability stack (separate compose file — opt-in):

```yaml
# docker-compose.observability.yml
# Run with: docker compose -f docker/docker-compose.yml -f docker/docker-compose.observability.yml up

services:

  # ── Grafana — the main dashboard for everything ──
  grafana:
    image: grafana/grafana:latest
    ports: ["3001:3000"]
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: admin
      GF_USERS_ALLOW_SIGN_UP: "false"
    volumes:
      - grafanadata:/var/lib/grafana
      - ./observability/grafana/provisioning:/etc/grafana/provisioning
      - ./observability/grafana/dashboards:/var/lib/grafana/dashboards

  # ── Loki — log aggregation (lightweight ELK replacement) ──
  loki:
    image: grafana/loki:latest
    ports: ["3100:3100"]
    command: -config.file=/etc/loki/local-config.yaml
    volumes:
      - lokidata:/loki

  # ── Promtail — ships Docker logs to Loki ──
  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./observability/promtail/config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
    depends_on: [loki]

  # ── Prometheus — metrics collection ──
  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
    volumes:
      - ./observability/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - promdata:/prometheus

  # ── Portainer — Docker container management UI ──
  portainer:
    image: portainer/portainer-ce:latest
    ports: ["9443:9443"]
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - portainerdata:/data

  # ── Kafka UI — topic browser, message viewer ──
  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    ports: ["8080:8080"]
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:29092
    depends_on: [kafka]

  # ── pgAdmin — PostgreSQL management ──
  pgadmin:
    image: dpage/pgadmin4:latest
    ports: ["5050:80"]
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@abodeatab.com
      PGADMIN_DEFAULT_PASSWORD: admin
    volumes: [pgadmindata:/var/lib/pgadmin]

  # ── Redis Insight — Redis browser ──
  redis-insight:
    image: redis/redisinsight:latest
    ports: ["5540:5540"]

volumes:
  grafanadata:
  lokidata:
  promdata:
  portainerdata:
  pgadmindata:
```

---

## 4. Observability Dashboards — What Each One Does

### Grafana (localhost:3001) — Your command centre
This is where you spend most of your time. Grafana connects to Loki (logs) and Prometheus (metrics) and gives you pre-built dashboards:

**Dashboard 1: Service health**
- Request rate per service (requests/sec)
- Error rate (4xx, 5xx per service)
- Response time (P50, P95, P99 per service)
- Active connections

**Dashboard 2: Logs**
- Live log stream from all services (filterable by service name, log level)
- Search across all logs: "find me all ERROR logs from channel-engine in the last hour"
- This replaces ELK — Loki + Grafana is much lighter and does the same job

**Dashboard 3: Infrastructure**
- PostgreSQL: active connections, query performance, database size
- Redis: hit rate, memory usage, connected clients
- Kafka: consumer lag, topic throughput, partition status

### Prometheus config (scrape metrics from FastAPI):

```yaml
# observability/prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'identity-service'
    static_configs:
      - targets: ['identity-service:8001']
  - job_name: 'rate-inventory-service'
    static_configs:
      - targets: ['rate-inventory-service:8002']
  - job_name: 'reservation-service'
    static_configs:
      - targets: ['reservation-service:8003']
  - job_name: 'channel-engine'
    static_configs:
      - targets: ['channel-engine:8004']
  - job_name: 'notification-service'
    static_configs:
      - targets: ['notification-service:8005']
  - job_name: 'admin-service'
    static_configs:
      - targets: ['admin-service:8006']
```

Each FastAPI service exposes `/metrics` via `prometheus-fastapi-instrumentator` (add to pyproject.toml).

### Promtail config (ship Docker logs to Loki):

```yaml
# observability/promtail/config.yml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        target_label: 'container'
      - source_labels: ['__meta_docker_container_label_com_docker_compose_service']
        target_label: 'service'
```

### Other dashboards:

| Tool | URL | Use it for |
|------|-----|-----------|
| Portainer | localhost:9443 | See all running containers, restart services, view logs, check resource usage. Like a Docker Desktop GUI but better. |
| Kafka UI | localhost:8080 | Browse Kafka topics, see messages in real-time, check consumer groups and lag. Essential for debugging event flows. |
| pgAdmin | localhost:5050 | Browse database tables, run queries, check tenant schemas, inspect indexes. |
| Redis Insight | localhost:5540 | Browse Redis keys, check session data, monitor cache hit rates. |
| Mailhog | localhost:8025 | See all emails sent by the system. Every booking confirmation, invitation, and alert lands here instead of going to real email. |

---

## 5. Makefile Shortcuts

```makefile
# Makefile — put this at the repo root

.PHONY: up down logs test migrate seed clean

# Start everything (services + infra)
up:
	docker compose -f docker/docker-compose.yml up -d --build

# Start with observability dashboards too
up-full:
	docker compose -f docker/docker-compose.yml -f docker/docker-compose.observability.yml up -d --build

# Stop everything
down:
	docker compose -f docker/docker-compose.yml -f docker/docker-compose.observability.yml down

# View logs (all services)
logs:
	docker compose -f docker/docker-compose.yml logs -f --tail=100

# View logs for one service
logs-%:
	docker compose -f docker/docker-compose.yml logs -f --tail=100 $*

# Run tests for a specific service
test-%:
	cd services/$* && pip install -e ".[dev]" && pytest -v

# Run all tests
test-all:
	@for svc in identity-service rate-inventory-service reservation-service channel-engine notification-service admin-service; do \
		echo "=== Testing $$svc ===" && cd services/$$svc && pytest -v && cd ../..; \
	done

# Run migrations for a specific service
migrate-%:
	cd services/$* && alembic upgrade head

# Run all migrations
migrate-all:
	@for svc in identity-service rate-inventory-service reservation-service channel-engine notification-service admin-service; do \
		echo "=== Migrating $$svc ===" && cd services/$$svc && alembic upgrade head && cd ../..; \
	done

# Seed test data
seed:
	python scripts/seed_data.py

# Nuclear option — destroy all data and rebuild
clean:
	docker compose -f docker/docker-compose.yml -f docker/docker-compose.observability.yml down -v
	docker system prune -f

# Open all dashboards in browser (Mac)
dashboards:
	open http://localhost:3000    # React app
	open http://localhost:8000    # API gateway (Swagger at /api/v1/docs)
	open http://localhost:3001    # Grafana
	open http://localhost:9443    # Portainer
	open http://localhost:8080    # Kafka UI
	open http://localhost:5050    # pgAdmin
	open http://localhost:8025    # Mailhog
```

### Usage:
```bash
make up              # Start services + infra
make up-full         # Start everything including dashboards
make logs            # Tail all logs
make logs-channel-engine  # Tail one service
make test-identity-service  # Run tests for identity service
make migrate-all     # Run all migrations
make seed            # Load test data
make dashboards      # Open all UIs in browser
make clean           # Nuke everything and start fresh
```

---

## 6. Day-to-Day Workflow

### Morning:
```bash
cd abodeatab-platform
make up-full                    # Start everything (takes ~30s after first build)
make dashboards                 # Open all UIs
```

### Working on a feature:
```bash
git checkout -b feat/channel-mapping-crud

# Edit code in services/channel-engine/app/...
# Hot reload picks up changes automatically (volume mounts)
# Test in browser at localhost:3000 or via API at localhost:8000

# Run tests
make test-channel-engine

# Commit
git add -A
git commit -m "feat(channel-engine): add CRUD for channel mappings"
git push origin feat/channel-mapping-crud

# Open PR on GitHub
# CI runs automatically (only channel-engine tests, due to path filter)
# Review → merge to main
```

### End of day:
```bash
make down                       # Stop everything (data persists in volumes)
```

---

## 7. Migrating to AWS Later

When the client is ready to pay for AWS (or when you hit the production milestone), the migration is straightforward because everything is already containerised:

### What changes:
| Component | Local | AWS |
|-----------|-------|-----|
| Docker runtime | Docker Desktop | EKS (Kubernetes) |
| PostgreSQL | Docker container | RDS |
| Redis | Docker container | ElastiCache |
| Kafka | Docker container | MSK (or keep self-hosted on EKS) |
| Container registry | Local images | ECR |
| API Gateway | Kong in Docker | Kong on EKS (or AWS API Gateway) |
| Logs | Loki + Grafana | CloudWatch (or keep Loki on EKS) |
| Metrics | Prometheus + Grafana | CloudWatch (or keep Prometheus on EKS) |
| CI/CD | GitHub Actions (already set up) | Same GitHub Actions, just push to ECR instead of local |

### What does NOT change:
- Docker images (same Dockerfile, same image)
- Application code (zero changes)
- `docker/docker-compose.yml` (still used for local dev even after AWS migration)
- API contracts
- Database schema
- Kafka topics

### The migration steps:
1. Create AWS infrastructure (EKS, RDS, ElastiCache, ECR) — use Terraform from `infra/`
2. Push Docker images to ECR (GitHub Actions does this automatically)
3. Apply K8s manifests from `k8s/` to the EKS cluster
4. Point DNS to the EKS load balancer
5. Run migrations against RDS

That's it. The same images that run on your Mac run on AWS. Docker is the abstraction layer that makes this work.

### Cost estimate when you do move to AWS:

| Resource | Size (Phase 1) | Estimated monthly cost |
|----------|----------------|----------------------|
| EKS cluster | 1 node, t3.xlarge | ~$120 |
| RDS PostgreSQL | db.t3.medium, Multi-AZ off | ~$50 |
| ElastiCache Redis | cache.t3.micro | ~$15 |
| ECR | 7 repos, ~2GB total | ~$2 |
| S3 + CloudFront | Minimal | ~$5 |
| Total | | ~$190/month |

That's Phase 1. You can start with even smaller instances and scale up as needed.
