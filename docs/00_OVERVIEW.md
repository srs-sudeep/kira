# Abode@AB Channel Manager — Coding Blueprint (Microservices Edition)

## Master Overview

This folder contains modular engineering documentation for building the Abode@AB Hotel Channel Manager Platform using a **microservices architecture** on **Kubernetes**. Each file is a self-contained guide or AI-codegen prompt.

---

## File Index

| # | File | Purpose | Sprint |
|---|------|---------|--------|
| 00 | `00_OVERVIEW.md` | This file — architecture, tech stack, system maps | Read first |
| 01 | `01_MICROSERVICES_AND_CICD.md` | Microservices explained, K8s setup, GitHub Actions CI/CD, Docker, deployment | Sprint 0 |
| 02 | `02_MONOREPO_STRUCTURE.md` | Complete monorepo layout, per-service template, shared code | Sprint 0 |
| 03 | `03_SERVICE_IMPLEMENTATIONS.md` | Per-service implementation prompts (Identity, Rate, Reservation, Channel, etc.) | Sprint 1–3 |
| 04 | `04_DATABASE_SCHEMA.md` | PostgreSQL schemas per service, multi-tenant strategy, migrations | Sprint 0–1 |
| 05 | `05_FRONTEND_ARCHITECTURE.md` | React frontend — folder structure, design system, routing, state | Sprint 0–1 |
| 06 | `06_FRONTEND_MODULES.md` | Screen-by-screen frontend implementation prompts | Sprint 1–3 |
| 07 | `07_LOCAL_DEV_AND_DASHBOARDS.md` | Monorepo Git strategy, local Docker setup, observability dashboards, Mac workflow | Day 1 |

---

## Architecture Decision: Microservices on Kubernetes

We are building **true microservices from day 1** — not a modular monolith. Each service is:
- Its own FastAPI application
- Its own Docker image
- Its own Kubernetes Deployment (pod)
- Its own database schema (shared PostgreSQL cluster, isolated schemas)
- Independently deployable via its own CI/CD pipeline

**Phase 1:** All services run on a **single EKS node** (1 replica each). This is enough for development, staging, and early production with pilot hotels.

**Phase 2 expansion (zero code changes):** Add K8s nodes, increase replica counts, add new services (PMS Adapter, Analytics, DBE). Kubernetes handles all of this via configuration — not code changes.

---

## Tech Stack

### Backend (all services)
| Layer | Technology | Purpose |
|-------|-----------|---------|
| Language | Python 3.13+ | All backend services |
| Framework | FastAPI | Async REST APIs |
| ORM | SQLAlchemy 2.0 (async) | Database access |
| Validation | Pydantic v2 | Request/response schemas |
| Migrations | Alembic | Schema versioning |
| Auth | python-jose + pwdlib | JWT + password hashing |
| Background tasks | Celery + Redis | Async jobs (email, sync) |
| Message broker | Apache Kafka (aiokafka) | Event-driven ARI distribution |
| Cache | Redis | Sessions, locks, caching |
| HTTP client | httpx | Async OTA API calls |
| Email | SendGrid | Transactional emails |
| Logging | structlog | Structured JSON logging |
| Tracing | OpenTelemetry | Distributed tracing |
| Testing | pytest + pytest-asyncio | Unit + integration tests |
| Linting | ruff | Lint + format |

### Frontend
| Layer | Technology | Purpose |
|-------|-----------|---------|
| Framework | React 18+ | UI library |
| Language | TypeScript 5.4+ | Type safety |
| Build | Vite 5+ | Build tool |
| Styling | Tailwind CSS 3.4+ | Utility-first CSS |
| Components | shadcn/ui | Accessible component library |
| Server state | TanStack Query 5+ | Data fetching, caching |
| Client state | Zustand 4+ | Lightweight global state |
| Routing | React Router 6+ | SPA routing |
| Forms | React Hook Form + Zod | Validation |
| Tables | TanStack Table 8+ | Data tables |
| Charts | Recharts 2+ | Dashboard visualisations |
| HTTP | Axios | API client with interceptors |

### Infrastructure
| Layer | Technology | Purpose |
|-------|-----------|---------|
| Container orchestration | Kubernetes (EKS) | Pod management, scaling |
| Container runtime | Docker | Service packaging |
| Container registry | AWS ECR | Image storage |
| API gateway | Kong | Routing, SSL, rate limiting |
| Database | PostgreSQL 16 (RDS) | Primary data store |
| Cache | Redis 7 (ElastiCache) | Caching, sessions |
| Message queue | Apache Kafka (MSK) | Event streaming |
| Object storage | S3 | Images, documents |
| CDN | CloudFront | Static asset delivery |
| CI/CD | GitHub Actions | Build, test, deploy |
| Monitoring | OpenTelemetry + CloudWatch | Observability |
| Secrets | AWS Secrets Manager | Credentials |
| WAF | AWS WAF | OWASP protection |

---

## Service Map — Phase 1

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster (EKS)                  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              API Gateway (Kong)                       │   │
│  │    Routes /auth/* → Identity, /rooms/* → Rate, etc.  │   │
│  └──────────────┬───────────────────────────┬───────────┘   │
│                 │ REST                       │ REST          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ Identity │ │ Rate &   │ │Reserva-  │ │  Channel     │   │
│  │ Service  │ │ Inventory│ │tion Svc  │ │  Engine      │   │
│  │ :8001    │ │ :8002    │ │ :8003    │ │  :8004       │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘   │
│       │             │            │               │           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐         │           │
│  │ Notifi-  │ │  Admin   │ │ Web App  │         │           │
│  │ cation   │ │ Service  │ │ (React)  │         │           │
│  │ :8005    │ │ :8006    │ │ :80      │         │           │
│  └────┬─────┘ └────┬─────┘ └──────────┘         │           │
│       │             │                            │           │
│  ┌──────────────────┴────────────────────────────┴──────┐   │
│  │           Kafka Event Bus                             │   │
│  │  Topics: ari.updated | reservation.* | channel.*      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────────────────┐   │
│  │ PostgreSQL │ │   Redis    │ │    Elasticsearch       │   │
│  │  (RDS)     │ │(ElastiCache│ │    (logs, audit)       │   │
│  └────────────┘ └────────────┘ └────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## FR → Service Ownership Matrix

Each FR module from the SRS is owned by exactly one service. "Owns" means the service stores the data and handles all CRUD. "Reads" means it queries data from the owning service via REST. "Triggers" means it publishes events that the other service reacts to.

| FR Module | Identity | Rate & Inv | Reservation | Channel | Notification | Admin |
|-----------|----------|-----------|-------------|---------|-------------|-------|
| FR-UM (users/RBAC) | **OWNS** | — | — | — | — | Co-owns |
| FR-RI (rates/rooms) | — | **OWNS** | — | Reads | — | — |
| FR-CM (channels) | — | Reads | Writes | **OWNS** | Triggers | — |
| FR-RM (reservations) | — | Updates | **OWNS** | Reads | Triggers | — |
| FR-DB (direct booking) | — | Reads | Writes | — | Triggers | — |
| FR-NA (notifications) | — | — | — | — | **OWNS** | — |
| FR-AR (analytics) | — | Reads | Reads | Reads | — | — |
| FR-PMS (PMS) | — | Reads | Writes | Via adapter | Triggers | — |

---

## Role → Service Access Matrix

| Role | Identity | Rate & Inv | Reservation | Channel | Notification | Analytics | Admin |
|------|----------|-----------|-------------|---------|-------------|----------|-------|
| Super admin | Full | Read | Read | Read | Full | Read | Full |
| Property owner | Full | Full | Full | Full | Full | Full | Full |
| Revenue manager | Self | Full | Read | Full | Full | Full | — |
| Front desk | Self | Read | Full | — | Full | — | — |
| Read-only | Self | Read | Read | Read | Read | Read | — |

---

## NFR Enforcement Map

NFRs don't belong to one service — they cut across all services:

| NFR Category | Where Enforced |
|-------------|---------------|
| Performance (<300ms P99) | API Gateway measures. Each service owns its latency. Kafka handles >5K events/sec. |
| Availability (99.9%) | K8s replica sets + health checks + auto-restart. RDS Multi-AZ. RPO <15min via backups. |
| Security | Gateway: TLS 1.3, WAF, rate limiting. Identity: auth, MFA, RBAC. All services: mTLS, encrypted PII, audit. |
| Scalability (10K tenants) | K8s HPA per service. Kafka partitions. PostgreSQL read-replicas. Redis cluster. |
| Compliance (PDPB/GDPR) | Identity + Reservation + Admin: consent, erasure, breach notification. PCI via gateway tokenisation. |
| Maintainability | All services: 80%+ coverage, OpenTelemetry, structured logs, OpenAPI docs. CI/CD: blue-green deploys. |

---

## Event Flow — What Happens When

### A revenue manager updates a rate:
1. React app → `PUT /api/v1/inventory/calendar` → API Gateway → Rate & Inventory Service
2. Rate Service updates ARISnapshot in DB, logs to InventoryHistory
3. Rate Service publishes `ari.updated` event to Kafka
4. Channel Engine (subscribed) picks up the event
5. Channel Engine resolves all active channel mappings for that room/rate
6. Channel Engine pushes updated ARI to each OTA (Booking.com, Expedia, etc.)
7. Channel Engine logs each push to SyncLog, updates channel.last_sync_at
8. If any push fails after 3 retries → Channel Engine publishes `channel.sync.failed`
9. Notification Service (subscribed) picks up failure → sends alert to property owner

### A booking arrives from Booking.com:
1. Channel Engine polls Booking.com API (every 60 seconds via Celery beat)
2. New booking detected → Channel Engine publishes `reservation.created` to Kafka
3. Reservation Service (subscribed) picks up the event
4. Reservation Service creates GuestProfile (or matches existing), creates Reservation, decrements ARI
5. Reservation Service publishes `reservation.confirmed` to Kafka
6. Notification Service picks up → sends in-app + email alert to front desk
7. Notification Service sends booking confirmation email to guest

---

## How to Use These Docs

1. Read this overview first to understand the full picture.
2. Read `01_MICROSERVICES_AND_CICD.md` to understand Docker, K8s, and GitHub Actions setup.
3. Execute `02_MONOREPO_STRUCTURE.md` to scaffold the entire repository.
4. Execute `04_DATABASE_SCHEMA.md` to create schemas and run migrations.
5. Execute `05_FRONTEND_ARCHITECTURE.md` to scaffold the React app.
6. Build services one by one using `03_SERVICE_IMPLEMENTATIONS.md` (Identity first, then Rate, Reservation, Channel).
7. Build frontend screens using `06_FRONTEND_MODULES.md` in parallel.
