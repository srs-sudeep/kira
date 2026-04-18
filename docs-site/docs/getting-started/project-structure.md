---
title: Project Structure
description: A complete tour of the KIRA monorepo — every top-level folder explained, with the reasoning behind each structural decision.
sidebar_position: 6
---

# Project Structure

**What you'll learn:**

- Why KIRA uses a monorepo and what that means day-to-day
- What every top-level folder contains and why it exists
- How the `services/` directory is organised internally (and why every service looks the same)
- How `shared/` code works as a local installable package
- How the frontend talks to the backend through Kong
- How Kubernetes manifests are structured with Kustomize overlays
- How CI/CD pipelines are path-filtered so a change to one service doesn't run tests for all six

---

## Top-Level Layout

```
kira/
├── services/          # Six independent backend microservices (FastAPI)
├── shared/            # Python utilities shared across all services
├── web-app/           # React 19 frontend (TypeScript + Vite)
├── k8s/               # Kubernetes manifests (Kustomize base + overlays)
├── kong/              # Kong API gateway declarative config
├── infra/             # Terraform for AWS infrastructure
├── observability/     # Prometheus, Grafana, Loki, Grafana Alloy configs
├── docs-site/         # This documentation (Docusaurus 3)
├── scripts/           # One-off scripts (seed data, create super-admin)
├── bin/               # `bin/kira` — run root CLI from any cwd (`uv run --project` to repo root); see [CLI Reference](./cli-reference.md#bin-kira)
├── docker/            # Dockerfiles + Compose files
│   ├── docker-compose.yml
│   ├── docker-compose.observability.yml
│   ├── docker-compose.dummy-ota.yml
│   ├── docker-compose.override.yml.example   # template; real override is gitignored
│   └── *.Dockerfile
├── cli/               # `kira` CLI (Python); see [CLI Reference](./cli-reference.md#installation) and [bin/kira](./cli-reference.md#bin-kira)
├── .github/
│   └── workflows/     # GitHub Actions CI/CD (one workflow per service)
├── Makefile
└── CLAUDE.md          # AI assistant instructions for this repo
```

### Why a monorepo?

KIRA uses a single repository for all six services, the frontend, and infrastructure rather than separate repos per service. The reasons:

| Concern            | Monorepo advantage                                                             |
| ------------------ | ------------------------------------------------------------------------------ |
| **Atomic changes** | A Kafka event schema change that affects producer and consumer lands in one PR |
| **Shared code**    | The `shared/` package is a local file dependency — no publish/version step     |
| **CI cost**        | Path-filtered workflows mean only the changed service is tested                |
| **Onboarding**     | Clone once, `docker compose up`, done — not seven separate repo setups         |
| **Code search**    | One place to grep across the entire codebase                                   |

The tradeoff is that the repo grows over time. For a team under ten developers, the benefits outweigh the cost.

---

## `services/` — Backend Microservices

```
services/
├── identity-service/          # :8001 — auth, users, RBAC, MFA, audit
├── rate-inventory-service/    # :8002 — room types, rate plans, ARI calendar
├── reservation-service/       # :8003 — bookings, guests, cancellations
├── channel-engine/            # :8004 — OTA adapters, ARI push/pull, Celery workers
├── notification-service/      # :8005 — email, in-app alerts
└── admin-service/             # :8006 — tenant onboarding, billing
```

Every service is a fully self-contained Python project. You can `cd` into any service directory and run it in isolation:

```bash
cd services/identity-service
uv run poetry install
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8001
```

### Per-Service Internal Structure

Every service follows the **same internal layout** — intentionally. When you know one service, you know them all:

```
services/<name>/
├── app/
│   ├── main.py                # FastAPI app factory, middleware, router registration
│   ├── config.py              # Pydantic BaseSettings (reads from environment)
│   ├── database.py            # Async SQLAlchemy engine + session factory
│   ├── dependencies.py        # FastAPI DI: get_db, get_current_user, require_roles
│   ├── exceptions.py          # Domain-specific exceptions
│   ├── exception_handlers.py  # Registers handlers on the FastAPI app
│   ├── health.py              # GET /health → {"status": "ok"}
│   ├── models/                # SQLAlchemy ORM classes (one file per entity)
│   ├── schemas/               # Pydantic v2 request/response models
│   ├── repositories/          # All SQLAlchemy queries (services never touch db directly)
│   ├── services/              # Business logic (calls repos, publishes events)
│   ├── routers/               # FastAPI APIRouter (thin: validate → call service → return)
│   ├── events/
│   │   ├── producer.py        # Kafka event publishing
│   │   └── consumer.py        # Kafka event consumption
│   └── tasks/
│       └── celery_app.py      # Celery background tasks (channel-engine uses this most)
├── migrations/
│   ├── env.py                 # Alembic migration environment
│   └── versions/              # Migration files (auto-generated + hand-edited)
├── tests/
│   ├── conftest.py            # Fixtures: test DB session, httpx AsyncClient, auth tokens
│   └── test_*.py
├── Dockerfile
├── pyproject.toml             # Poetry dependencies (uv resolves these)
├── alembic.ini
└── .env.example               # Documents required env vars (copy → .env.local)
```

**The layer rule is strict:**

```
HTTP Request
    │
    ▼
Router         — validates input (Pydantic), calls one service method, returns response
    │
    ▼
Service        — business logic, orchestrates repos, publishes Kafka events
    │
    ▼
Repository     — all SQLAlchemy queries live here, returns ORM objects or scalars
    │
    ▼
Database
```

Routers never touch the database. Services never build HTTP responses. Repositories never contain business rules. This makes each layer independently testable.

---

## `shared/` — Cross-Service Python Utilities

```
shared/
├── __init__.py
├── pyproject.toml             # Installable as a local package
├── schemas/
│   ├── events.py              # Pydantic models for every Kafka event
│   └── pagination.py          # PaginatedResponse[T], PaginationParams
├── middleware/
│   ├── tenant.py              # Tenant resolution: extracts tenant_id from JWT, sets search_path
│   └── logging.py             # structlog JSON request logging middleware
├── utils/
│   ├── crypto.py              # AES-256 field encryption for PII (guest data, channel creds)
│   ├── datetime_utils.py      # Timezone-aware datetime helpers
│   └── kafka_helpers.py       # Typed Kafka producer/consumer wrapper
└── core/
    ├── security.py            # JWT verification (all services verify tokens the same way)
    └── permissions.py         # RBAC helper decorators
```

`shared/` is installed as a **local file dependency** in each service's `pyproject.toml`:

```toml
# services/identity-service/pyproject.toml
[tool.poetry.dependencies]
shared = { path = "../../shared", develop = true }
```

In Docker, the `shared/` directory is volume-mounted (dev) or COPY-ed (production build) into each service image before `poetry install` runs.

**What goes in `shared/`:**

- Kafka event schemas — so the producer (rate-inventory) and consumer (channel-engine) both use the same `ARIUpdatedEvent` Pydantic model
- JWT verification — all services validate tokens identically
- Tenant middleware — one implementation used by all services
- Encryption utilities — guest PII and OTA credentials use the same AES-256 wrapper

**What does NOT go in `shared/`:**

- Business logic (belongs in the owning service's `services/` layer)
- SQLAlchemy models (each service owns its own schema)
- API request/response schemas (each service defines its own shapes)

---

## `web-app/` — React 19 Frontend

```
web-app/
├── src/
│   ├── components/            # Shared UI: AppShell, Header, Sidebar, shadcn/ui wrappers
│   ├── features/              # Feature modules (one per major section of the dashboard)
│   │   ├── auth/              # Login, registration
│   │   ├── dashboard/         # KPI cards, charts
│   │   ├── rates/             # Room types, rate plans, ARI calendar
│   │   ├── reservations/      # Booking table, detail, modify/cancel
│   │   ├── channels/          # OTA connections, mappings, sync log
│   │   ├── notifications/     # Notification centre, bell, preferences
│   │   ├── profile/           # User profile, password, MFA
│   │   └── settings/          # Property settings, users, audit log
│   ├── router/                # React Router config (routes.ts + index.tsx)
│   ├── stores/                # Zustand stores (auth tokens, UI state only)
│   ├── services/              # Per-feature axios service wrappers
│   ├── types/                 # TypeScript interfaces mirroring API schemas
│   ├── config/                # QUERY_KEYS constants, API_BASE_URL, app config
│   └── lib/                   # cn(), formatCurrency(), formatDate() utilities
├── public/
├── Dockerfile                 # Multi-stage: bun build → nginx:alpine
├── nginx.conf                 # SPA routing, asset caching, gzip
├── package.json               # bun lockfile (bun.lockb committed)
├── vite.config.ts
├── tailwind.config.ts
└── tsconfig.json              # strict: true
```

The frontend talks to the backend exclusively through the **Kong API gateway** at `http://localhost:8000` (configured via `VITE_API_BASE_URL`). It never calls individual service ports directly — Kong handles routing, auth token forwarding, and rate limiting.

For state management: **TanStack Query** owns all server-fetched data (room types, reservations, notifications). **Zustand** owns only client-side state: the JWT access token, the current user object for the header, and UI preferences like sidebar collapse state. See [State Management](../frontend/state-management.md) for the full breakdown.

---

## `k8s/` — Kubernetes Manifests

```
k8s/
├── base/                      # Kustomize base: the defaults
│   ├── kustomization.yaml     # References all sub-directories
│   ├── configmap.yaml         # Shared non-secret config (ENV vars)
│   ├── secrets-template.yaml  # Documents required K8s Secrets (do not apply directly)
│   ├── identity-service/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── hpa.yaml
│   ├── rate-inventory-service/
│   ├── reservation-service/
│   ├── channel-engine/
│   │   ├── deployment.yaml        # API server (port 8004)
│   │   ├── worker-deployment.yaml # Celery worker (same image, different command)
│   │   ├── service.yaml
│   │   └── hpa.yaml
│   ├── notification-service/
│   ├── admin-service/
│   └── web-app/
└── overlays/
    ├── staging/               # namespace: kira-staging, 1 replica, debug log level
    │   └── kustomization.yaml
    └── production/            # namespace: kira, 2 replicas, higher resource limits
        ├── kustomization.yaml
        └── patches/
            ├── replicas.yaml  # Set all deployments to 2 replicas
            └── resources.yaml # Higher CPU/memory limits for API pods
```

**How Kustomize overlays work:**

The `base/` directory defines everything at its simplest (1 replica, base resource limits, `latest` image tag). Each overlay _patches_ the base without duplicating it:

```bash
# What staging will apply:
kubectl kustomize k8s/overlays/staging

# Apply to staging:
kubectl apply -k k8s/overlays/staging

# Apply to production:
kubectl apply -k k8s/overlays/production
# then update image tag:
kubectl set image deployment/kira-identity-service \
  kira-identity-service=${ECR_REGISTRY}/kira-identity-service:abc12345 \
  -n kira
```

Image tags are set to `latest` in the kustomization files but overridden with a git SHA by the CI workflow immediately after `kubectl apply`. This means the manifest files don't need to change on every deploy — only `kubectl set image` is called.

---

## `kong/` — API Gateway Configuration

```
kong/
└── kong.yml    # Declarative config: routes, plugins, upstreams
```

Kong runs in DB-less mode (`KONG_DATABASE: "off"`) with a declarative config file. All routing rules are here: which path prefix maps to which backend service, rate limiting, JWT verification plugin, and CORS headers.

When you change a Kong route (e.g., to add a new service prefix), edit `kong/kong.yml` and restart the Kong container.

---

## `infra/` — Terraform (AWS)

```
infra/
└── terraform/
    ├── main.tf            # Provider config, S3 backend state
    ├── eks.tf             # EKS cluster + node group
    ├── rds.tf             # PostgreSQL 16 (RDS)
    ├── elasticache.tf     # Redis 7 (ElastiCache)
    ├── ecr.tf             # ECR repositories (one per service + web-app)
    ├── msk.tf             # Kafka (MSK)
    ├── s3.tf              # Asset storage bucket
    └── variables.tf
```

All AWS infrastructure is managed through Terraform. Never create resources manually in the AWS console — every resource must be in code so it can be reproduced, audited, and torn down cleanly.

State is stored in an S3 bucket with DynamoDB locking (configured in `main.tf`).

---

## `observability/` — Monitoring Configs

```
observability/
├── prometheus/
│   ├── prometheus.yml     # Scrape config — all six services + infra exporters
│   └── alerts/            # Alert rules (HighErrorRate, ChannelSyncFailing, etc.)
├── grafana/
│   ├── provisioning/      # Auto-provision datasources (Prometheus, Loki) on startup
│   └── dashboards/        # Pre-built dashboard JSON files
├── loki/
│   └── loki-config.yml    # Loki storage config (filesystem for local dev)
└── alloy/
    └── config.alloy       # Grafana Alloy: Docker logs → Loki (Promtail successor)
```

The observability stack is opt-in via a separate Compose file:

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.observability.yml up -d
```

---

## `.github/workflows/` — CI/CD Pipelines

```
.github/workflows/
├── ci-identity-service.yml         # test → build+push → deploy-staging
├── ci-rate-inventory-service.yml
├── ci-reservation-service.yml
├── ci-channel-engine.yml
├── ci-notification-service.yml
├── ci-admin-service.yml
├── ci-web-app.yml
├── deploy-staging.yml              # (referenced by per-service CIs)
└── deploy-production.yml           # workflow_dispatch + manual approval gate
```

**Path filtering** is the key design decision here. Each service workflow only triggers when files in that service's directory change:

```yaml
# ci-channel-engine.yml
on:
  push:
    paths:
      - "services/channel-engine/**"
      - "shared/**" # shared/ changes trigger all services
```

A commit that only touches `services/channel-engine/` will run `ci-channel-engine.yml` and nothing else. The other five service tests don't start. This keeps CI fast (a single-service change completes in ~3 minutes) and cheap (no wasted GitHub Actions minutes).

Each per-service workflow has three jobs:

1. **test** — runs on every push and PR: install deps, lint, format check, pytest with 70% coverage gate
2. **build-and-push** — only on `main` push: builds Docker image, pushes to ECR with git SHA tag
3. **deploy-staging** — only on `main` push: `kubectl set image` on the staging EKS cluster

Production deploys go through `deploy-production.yml` which requires a `workflow_dispatch` trigger (manual, from the GitHub Actions UI) and a GitHub environment reviewer approval before the deployment job runs.

---

## `scripts/` — One-Off Utilities

```
scripts/
├── seed_data.py         # Creates test tenant, users, room types, rate plans, ARI data
└── create_superadmin.py # Creates or resets the super-admin user
```

These are run with `make seed` and `make superadmin` respectively. They are plain Python scripts that connect directly to PostgreSQL (not through the API) and are only used for local development and CI test setup.

---

## `docs-site/` — This Documentation

```
docs-site/
├── docs/                # Markdown files (what you're reading now)
├── src/
│   ├── pages/           # Custom Docusaurus pages (landing page)
│   └── css/             # Custom CSS (brand colours, feature cards)
├── static/img/          # Static assets (logo SVG)
├── docusaurus.config.ts # Site config (title, navbar, footer, Mermaid, Prism)
├── sidebars.ts          # Manual sidebar definition
└── package.json         # Docusaurus 3 + bun
```

Run the docs dev server:

```bash
make docs-dev    # starts on http://localhost:4000
```

Build static output:

```bash
make docs-build  # outputs to docs-site/build/
```

---

## Summary: Where to Find Things

| Task                         | Where to look                                                  |
| ---------------------------- | -------------------------------------------------------------- |
| Add an API endpoint          | `services/<name>/app/routers/` + `services/` + `repositories/` |
| Change a Pydantic schema     | `services/<name>/app/schemas/`                                 |
| Add a Kafka event type       | `shared/schemas/events.py`                                     |
| Change the tenant middleware | `shared/middleware/tenant.py`                                  |
| Add a React page             | `web-app/src/features/<name>/pages/` + `web-app/src/router/`   |
| Add an API service call      | `web-app/src/features/<name>/services/<name>Service.ts`        |
| Change K8s resource limits   | `k8s/overlays/production/patches/resources.yaml`               |
| Add a new Kong route         | `kong/kong.yml`                                                |
| Add AWS infrastructure       | `infra/terraform/*.tf`                                         |
| Add a CI step                | `.github/workflows/ci-<service>.yml`                           |
| Update these docs            | `docs-site/docs/<section>/<page>.md`                           |
