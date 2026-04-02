---
title: Microservices Design
description: Why KIRA uses microservices, each service's responsibilities and owned data, the internal layer pattern, and the Phase 1 → Phase 2 roadmap.
sidebar_position: 2
---

# Microservices Design

**What you'll learn:**
- What a microservice is and why it's the right choice for a channel manager
- Each service's port, responsibility, and owned data tables
- The mandatory Router → Service → Repository layer pattern inside every service
- How independent deployability works in practice
- The Phase 1 (single-node) to Phase 2 (scaled) evolution plan

---

## What Is a Microservice?

A microservice is a small, independently deployable application that owns exactly one business domain. It has:

- Its own source code (a separate directory in the monorepo)
- Its own database tables (other services never write to them)
- Its own Docker image (built and deployed independently)
- Its own API (REST endpoints scoped to its domain)
- Its own CI/CD pipeline (triggered only when its code changes)

The key constraint is **data ownership**. Two services cannot share a table. If service A needs data owned by service B, it either calls B's API (synchronous) or reacts to an event that B publishes (asynchronous).

**Why microservices for a channel manager?**

A channel manager has two very different performance requirements: the property management UI needs fast, consistent reads (< 200ms), while OTA sync is slow and unreliable (Booking.com's API can take 5–30 seconds, fail intermittently, and has rate limits). Putting both in a monolith means slow OTA calls would block the UI. With microservices, the channel-engine Celery workers handle OTA I/O independently — a slow OTA doesn't slow down a property manager loading the reservation inbox.

---

## Service Inventory

### Kong API Gateway `:8000`

Not a microservice — it's infrastructure. Kong sits in front of all services and handles:
- **Routing** — `/api/v1/auth/*` → identity-service, `/api/v1/rooms/*` → rate-inventory-service
- **JWT verification** — validates Bearer tokens on every request (except `/health`)
- **Rate limiting** — 100 req/min per IP default, 10 req/min on auth endpoints
- **CORS** — configured per environment
- **Request logging** — structured access logs to stdout

Kong runs in DB-less mode with a declarative YAML config (`kong/kong.yml`).

---

### identity-service `:8001`

**Responsibility:** Authentication and authorization hub for the entire platform.

**Owns:** `public.users`, `public.refresh_tokens`, `public.audit_events`

**Key capabilities:**
- Email/password login with bcrypt hashing
- JWT access tokens (60-min) + refresh tokens (7-day, HttpOnly cookie)
- TOTP-based MFA with backup codes (pyotp)
- RBAC: `super_admin` | `property_owner` | `revenue_manager` | `front_desk` | `read_only`
- Immutable audit log for every permission-sensitive action
- Token revocation via Redis blacklist

**Why a separate service?** Every other service needs to verify JWTs. With identity as a separate service, JWT verification logic lives in `shared/core/security.py` and is used identically everywhere. No service has its own auth implementation to drift or break.

---

### rate-inventory-service `:8002`

**Responsibility:** Source of truth for what rooms exist, what they cost, and how many are available on each date.

**Owns:** `room_types`, `rate_plans`, `ari_snapshots`, `seasonal_rules`, `blackout_dates`, `inventory_history`

**Key capabilities:**
- Room type CRUD with occupancy config and amenities
- Rate plan CRUD with derived rates (percentage/fixed offset from BAR)
- ARI (Availability + Rate + Inventory) calendar — one row per (room_type, rate_plan, date)
- Bulk ARI updates across date ranges with day-of-week filters
- Seasonal rule application (nightly Celery beat task)
- Publishes `ari.updated` to Kafka on every ARI write

**Performance note:** `ari_snapshots` has a composite unique constraint and index on `(room_type_id, rate_plan_id, date)`. Bulk calendar reads are a single range scan — no N+1.

---

### reservation-service `:8003`

**Responsibility:** Full booking lifecycle — creation, modification, cancellation, and guest records.

**Owns:** `reservations`, `guest_profiles`, `reservation_notes`

**Key capabilities:**
- Reservation CRUD with status machine: `confirmed → modified | checked_in → checked_out`
- Guest profile deduplication by email hash
- Cancellation with policy enforcement and refund calculation
- Consumes `reservation.created` from channel-engine (OTA bookings)
- Publishes `reservation.created` and `reservation.cancelled` to Kafka

**Note:** Guest PII (email, phone) is stored encrypted. See [Database Design](./database-design.md#pii-encryption).

---

### channel-engine `:8004` + Celery worker

**Responsibility:** The integration layer between KIRA and OTA booking platforms.

**Owns:** `channels`, `channel_mappings`, `sync_logs`

**Key capabilities:**
- OTA adapter implementations for Booking.com, Expedia, MakeMyTrip (all implement `BaseOTAAdapter`)
- ARI push to connected OTAs (triggered by `ari.updated` Kafka events via Celery)
- Booking pull from OTAs on schedule (Celery beat, every 15 minutes)
- Channel mapping management (KIRA room/rate → OTA room/rate identifier)
- Circuit breaker: after `CIRCUIT_BREAKER_THRESHOLD` consecutive failures, a channel trips to `error` status and is skipped until manually reset or auto-recovery after 5 minutes
- Sync log for every push/pull attempt
- Publishes `channel.sync.failed` when retries are exhausted

**Two-pod architecture:** The API server handles REST requests. A separate Celery worker pod runs the background tasks. Both use the same Docker image, different entrypoint commands.

---

### notification-service `:8005`

**Responsibility:** All outbound communication — emails via SendGrid and in-app notifications.

**Owns:** `notifications`, `notification_preferences`

**Key capabilities:**
- Consumes `reservation.created`, `reservation.cancelled`, `channel.sync.failed` from Kafka
- Sends transactional emails via SendGrid SMTP
- Creates in-app notification records readable by the dashboard
- Per-user preferences (email and/or in-app per event type)
- Notification archive with read/unread state and bulk actions
- Bell icon unread count endpoint (polled every 30s by the frontend)

---

### admin-service `:8006`

**Responsibility:** Tenant lifecycle management and billing. Super-admin only.

**Owns:** `public.tenants`

**Key capabilities:**
- Tenant provisioning: creates PostgreSQL schema, runs migrations, seeds default data
- Tenant settings management (property info, currency, timezone)
- Stripe subscription integration
- Platform metrics (cross-tenant usage, revenue summaries)
- Publishes `tenant.created` event for other services to initialise their tenant-scoped state

---

## Internal Layer Pattern

Every service enforces the same three-layer architecture. The layers have strict rules:

```
HTTP Request
    │
    ▼ ─────────────────────────────────────────────────
    Router (app/routers/)
    • Parses and validates request with Pydantic schema
    • Calls exactly ONE service method
    • Returns a Pydantic response schema
    • Never touches the database directly
    • Never contains business logic
    ▼ ─────────────────────────────────────────────────
    Service (app/services/)
    • Contains all business logic
    • Calls repositories for data access
    • Publishes Kafka events after state changes
    • Raises domain exceptions (NotFoundError, ConflictError)
    • Never builds HTTP responses
    • Never imports from routers/
    ▼ ─────────────────────────────────────────────────
    Repository (app/repositories/)
    • All SQLAlchemy queries live here
    • Returns ORM objects or scalars
    • Never contains business logic
    • Never publishes events
    • Never imports from services/
    ▼ ─────────────────────────────────────────────────
    Database (PostgreSQL)
```

**Why is this strict?**

When a bug surfaces ("the rate bulk update isn't decrementing inventory correctly"), you know immediately it's in the service layer. When a query is slow, you look at the repository. When a validation error occurs, you look at the router schema. The layers make the codebase navigable without reading every file.

:::tip Finding the right file
If you're adding a new endpoint: router → service → repository, in that order.  
If you're fixing a business logic bug: start in `services/`.  
If you're fixing a query performance issue: start in `repositories/`.
:::

---

## Independent Deployability

Each service is independently deployed via its own GitHub Actions workflow. A commit to `services/channel-engine/` triggers only `ci-channel-engine.yml` — the other five service pipelines don't run.

This means:
- Deploying a channel-engine bug fix doesn't require building or deploying identity-service
- A failing test in rate-inventory-service doesn't block a channel-engine deploy
- Each service has its own image version in ECR with its own git SHA tag

In Kubernetes, each service is a separate Deployment with its own rollout history:

```bash
# Roll back only channel-engine — leaves all other services untouched
kubectl rollout undo deployment/kira-channel-engine -n kira
```

---

## Phase 1 → Phase 2 Roadmap

### Phase 1 — Current (single EKS node, 1 replica per service)

All six services run on a single `t3.xlarge` EKS node. This is sufficient for:
- Development and staging
- Early production with up to ~50 hotels
- ~1,000 reservations/day
- ~100 concurrent users

```yaml
# Current (base k8s manifests)
spec:
  replicas: 1
  resources:
    requests: { cpu: 100m, memory: 256Mi }
    limits: { cpu: 500m, memory: 512Mi }
```

### Phase 2 — Scale (multi-node EKS, HPA active)

No code changes required. Only Kubernetes configuration changes:

| Change | How |
|---|---|
| Add replicas | Production overlay patches to 2 replicas; HPA scales to 5 |
| More OTAs | Add adapter in `channel-engine/app/adapters/`, register in `adapters/registry.py` |
| New service | Create `services/new-service/`, add K8s manifests, add CI workflow |
| Separate Kafka | Switch `KAFKA_BOOTSTRAP_SERVERS` to MSK endpoint — zero code change |
| Read replicas | Update `DATABASE_URL` to RDS read replica endpoint in read-heavy services |

Phase 2 upgrades are configuration-only because the application code never assumes single-replica deployment: no in-process state, no sticky sessions, idempotent Kafka consumers.

:::info Planned Phase 2 services
- **pms-adapter-service** — two-way sync with PMS systems (Opera, Mews, Cloudbeds)
- **analytics-service** — read-only reporting queries against a separate read replica
- **rate-intelligence-service** — competitor rate monitoring and recommendation engine
:::
