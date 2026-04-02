# Monorepo Structure — Complete Layout

## Repository Root

```
abodeatab-platform/
│
├── services/                          # ── Backend microservices ──
│   ├── identity-service/              # Auth, users, RBAC, MFA, sessions
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py               # FastAPI app + lifespan + router registration
│   │   │   ├── config.py             # Pydantic BaseSettings (service-specific env vars)
│   │   │   ├── database.py           # Async SQLAlchemy engine + session
│   │   │   ├── dependencies.py       # get_db, get_current_user, require_roles
│   │   │   ├── exceptions.py         # Custom exceptions
│   │   │   ├── exception_handlers.py # Global error handler
│   │   │   ├── health.py             # GET /health endpoint
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py           # DeclarativeBase + mixins
│   │   │   │   ├── user.py           # User, RefreshToken models
│   │   │   │   └── audit.py          # AuditEvent model
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py           # Login, Register, Token schemas
│   │   │   │   └── user.py           # User CRUD schemas
│   │   │   ├── repositories/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user_repo.py
│   │   │   │   └── audit_repo.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth_service.py
│   │   │   │   └── user_service.py
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth_router.py     # /auth/login, /register, /refresh, /mfa/*
│   │   │   │   ├── user_router.py     # /users CRUD, /users/invite
│   │   │   │   └── audit_router.py    # /audit (read-only)
│   │   │   ├── core/
│   │   │   │   ├── security.py        # JWT, password hashing, TOTP
│   │   │   │   └── permissions.py     # RBAC decorators
│   │   │   └── tasks/
│   │   │       ├── celery_app.py
│   │   │       └── email_tasks.py     # Send invitation emails
│   │   ├── migrations/
│   │   │   ├── env.py
│   │   │   └── versions/
│   │   ├── tests/
│   │   │   ├── conftest.py
│   │   │   ├── test_auth.py
│   │   │   └── test_users.py
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── alembic.ini
│   │   └── .env.example
│   │
│   ├── rate-inventory-service/        # Room types, rate plans, ARI, calendar
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── dependencies.py
│   │   │   ├── health.py
│   │   │   ├── models/
│   │   │   │   ├── room_type.py
│   │   │   │   ├── rate_plan.py
│   │   │   │   ├── ari_snapshot.py
│   │   │   │   ├── seasonal_rule.py
│   │   │   │   ├── blackout_date.py
│   │   │   │   └── inventory_history.py
│   │   │   ├── schemas/
│   │   │   │   ├── room_type.py
│   │   │   │   ├── rate_plan.py
│   │   │   │   └── inventory.py
│   │   │   ├── repositories/
│   │   │   │   ├── room_type_repo.py
│   │   │   │   ├── rate_plan_repo.py
│   │   │   │   └── ari_repo.py
│   │   │   ├── services/
│   │   │   │   ├── room_service.py
│   │   │   │   ├── rate_plan_service.py
│   │   │   │   └── inventory_service.py
│   │   │   ├── routers/
│   │   │   │   ├── room_router.py      # /rooms/types CRUD
│   │   │   │   ├── rate_plan_router.py  # /rooms/types/{id}/rate-plans CRUD
│   │   │   │   └── inventory_router.py  # /inventory/calendar, /bulk-update, /stop-sell
│   │   │   ├── events/
│   │   │   │   └── producer.py          # Publish ari.updated to Kafka
│   │   │   └── tasks/
│   │   │       ├── celery_app.py
│   │   │       └── seasonal_apply.py    # Nightly: apply seasonal rules
│   │   ├── migrations/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── alembic.ini
│   │
│   ├── reservation-service/           # Bookings, guests, lifecycle
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── models/
│   │   │   │   ├── reservation.py
│   │   │   │   ├── guest_profile.py
│   │   │   │   └── reservation_note.py
│   │   │   ├── schemas/
│   │   │   ├── repositories/
│   │   │   ├── services/
│   │   │   │   ├── reservation_service.py
│   │   │   │   └── guest_service.py
│   │   │   ├── routers/
│   │   │   │   ├── reservation_router.py  # CRUD + /modify, /cancel, /notes
│   │   │   │   └── guest_router.py
│   │   │   └── events/
│   │   │       ├── producer.py           # Publish reservation.created/cancelled
│   │   │       └── consumer.py           # Consume from channel engine
│   │   ├── migrations/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   ├── channel-engine/                # OTA adapters, ARI sync, retry
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── models/
│   │   │   │   ├── channel.py
│   │   │   │   ├── channel_mapping.py
│   │   │   │   └── sync_log.py
│   │   │   ├── schemas/
│   │   │   ├── repositories/
│   │   │   ├── services/
│   │   │   │   ├── channel_service.py
│   │   │   │   └── sync_service.py
│   │   │   ├── routers/
│   │   │   │   ├── channel_router.py     # CRUD + /mapping, /health, /sync-log
│   │   │   │   └── health_router.py      # /channels/health dashboard
│   │   │   ├── adapters/                 # OTA-specific implementations
│   │   │   │   ├── base.py              # Abstract ChannelAdapter interface
│   │   │   │   ├── booking_com.py
│   │   │   │   ├── expedia.py
│   │   │   │   └── makemytrip.py
│   │   │   ├── events/
│   │   │   │   ├── consumer.py           # Subscribe to ari.updated
│   │   │   │   └── producer.py           # Publish channel.sync.*, reservation.created
│   │   │   └── tasks/
│   │   │       ├── celery_app.py
│   │   │       ├── ari_push.py           # Push ARI to channels (triggered by Kafka)
│   │   │       └── booking_pull.py       # Poll OTAs for new bookings (beat schedule)
│   │   ├── migrations/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   ├── notification-service/          # Email, in-app, alerts
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── models/
│   │   │   │   ├── notification.py
│   │   │   │   └── notification_preference.py
│   │   │   ├── schemas/
│   │   │   ├── repositories/
│   │   │   ├── services/
│   │   │   │   └── notification_service.py
│   │   │   ├── routers/
│   │   │   │   └── notification_router.py
│   │   │   ├── events/
│   │   │   │   └── consumer.py           # Subscribe to reservation.*, channel.sync.failed
│   │   │   └── tasks/
│   │   │       ├── celery_app.py
│   │   │       └── email_sender.py       # SendGrid email dispatch
│   │   ├── migrations/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   └── admin-service/                 # Tenants, config, billing
│       ├── app/
│       │   ├── main.py
│       │   ├── models/
│       │   │   └── tenant.py
│       │   ├── schemas/
│       │   ├── repositories/
│       │   ├── services/
│       │   │   └── tenant_service.py     # Onboarding, schema provisioning
│       │   └── routers/
│       │       └── tenant_router.py
│       ├── migrations/
│       ├── tests/
│       ├── Dockerfile
│       └── pyproject.toml
│
├── shared/                            # ── Shared code across services ──
│   ├── __init__.py
│   ├── pyproject.toml                 # Installable as: pip install -e shared/
│   ├── schemas/
│   │   ├── events.py                  # Kafka event schemas (ARIUpdatedEvent, ReservationCreatedEvent)
│   │   └── pagination.py             # PaginatedResponse, PaginationParams
│   ├── middleware/
│   │   ├── tenant.py                  # Tenant resolution middleware (reused by all services)
│   │   └── logging.py                # Request logging middleware
│   ├── utils/
│   │   ├── crypto.py                  # AES-256 field encryption for PII
│   │   ├── datetime_utils.py          # Timezone helpers
│   │   └── kafka_helpers.py           # Kafka producer/consumer wrappers
│   └── core/
│       ├── security.py                # JWT verification (shared, used by all services)
│       └── permissions.py             # RBAC helpers
│
├── web-app/                           # ── React frontend ──
│   ├── src/                           # (See 05_FRONTEND_ARCHITECTURE.md)
│   ├── public/
│   ├── Dockerfile                     # Multi-stage: build React → serve via nginx
│   ├── nginx.conf                     # SPA routing + proxy to API gateway
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.ts
│
├── k8s/                               # ── Kubernetes manifests ──
│   ├── base/                          # Kustomize base configs
│   │   ├── namespace.yaml
│   │   ├── identity-service/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   └── hpa.yaml
│   │   ├── rate-inventory-service/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   └── hpa.yaml
│   │   ├── reservation-service/
│   │   ├── channel-engine/
│   │   ├── notification-service/
│   │   ├── admin-service/
│   │   ├── web-app/
│   │   └── kustomization.yaml
│   ├── overlays/
│   │   ├── staging/
│   │   │   ├── kustomization.yaml     # Patches: 1 replica, staging DB URL
│   │   │   └── configmap-patches.yaml
│   │   └── production/
│   │       ├── kustomization.yaml     # Patches: 2+ replicas, prod DB URL
│   │       └── configmap-patches.yaml
│   └── kong/
│       └── kong.yml                   # API Gateway route definitions
│
├── infra/                             # ── Infrastructure as Code ──
│   ├── terraform/                     # (or AWS CDK)
│   │   ├── main.tf
│   │   ├── eks.tf                     # EKS cluster
│   │   ├── rds.tf                     # PostgreSQL
│   │   ├── elasticache.tf             # Redis
│   │   ├── ecr.tf                     # Container registries
│   │   ├── msk.tf                     # Kafka (Phase 2, use docker Kafka in Phase 1)
│   │   ├── s3.tf                      # Asset storage
│   │   └── variables.tf
│   └── scripts/
│       ├── setup-cluster.sh           # Initial EKS setup
│       └── create-ecr-repos.sh        # Create all ECR repositories
│
├── .github/
│   └── workflows/
│       ├── ci-identity-service.yml
│       ├── ci-rate-inventory-service.yml
│       ├── ci-reservation-service.yml
│       ├── ci-channel-engine.yml
│       ├── ci-notification-service.yml
│       ├── ci-admin-service.yml
│       ├── ci-web-app.yml
│       ├── deploy-staging.yml
│       └── deploy-production.yml
│
├── docker-compose.yml                 # Local dev: all services + infra
├── Makefile                           # Shortcuts: make up, make test-all, make deploy-staging
├── .gitignore
└── README.md
```

---

## Per-Service Internal Template

Every service follows this exact pattern. Copy this skeleton for each new service:

```
services/<service-name>/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI app, lifespan, router registration
│   ├── config.py              # Pydantic BaseSettings (env vars)
│   ├── database.py            # Async SQLAlchemy engine + session
│   ├── dependencies.py        # get_db, auth dependencies
│   ├── exceptions.py          # Service-specific exceptions
│   ├── exception_handlers.py  # Register handlers on app
│   ├── health.py              # GET /health → {"status": "ok", "service": "..."}
│   ├── models/                # SQLAlchemy ORM models
│   ├── schemas/               # Pydantic v2 request/response models
│   ├── repositories/          # Database access layer (SQL queries only)
│   ├── services/              # Business logic (calls repos, publishes events)
│   ├── routers/               # FastAPI APIRouter (thin — validate, call service, return)
│   ├── events/                # Kafka producer/consumer for this service
│   │   ├── producer.py
│   │   └── consumer.py
│   └── tasks/                 # Celery background tasks
│       └── celery_app.py
├── migrations/
│   ├── env.py
│   └── versions/
├── tests/
│   ├── conftest.py            # Test fixtures: DB, client, auth headers
│   └── test_*.py
├── Dockerfile
├── pyproject.toml
├── alembic.ini
└── .env.example
```

**Data flow inside a service:**

```
HTTP Request → Router (validate) → Service (logic) → Repository (SQL) → Database
                                 → Events Producer (Kafka)
                                 → Celery Task (background)
```

**Rules:**
- Routers never touch SQLAlchemy directly
- Services never construct HTTP responses
- Repositories never contain business logic
- Events are fire-and-forget (published, not awaited)
- Each service has its own `config.py` with its own env vars

---

## Shared Code (`shared/`)

The `shared/` package contains code that multiple services need. It is installed as a local package:

```toml
# In each service's pyproject.toml:
[project]
dependencies = [
    "shared @ file://../../shared",  # Local dev
    # In Docker: COPY shared/ and pip install -e ./shared
]
```

What goes in shared:
- Kafka event schemas (Pydantic models for events — so producer and consumer agree on the shape)
- JWT verification logic (every service needs to validate tokens)
- Tenant resolution middleware
- Pagination helpers
- Encryption utilities (AES-256 for PII)
- Structured logging setup

What does NOT go in shared:
- Business logic (belongs in the service)
- Database models (each service owns its own)
- API schemas (each service defines its own request/response shapes)
