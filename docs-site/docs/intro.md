---
id: intro
title: Introduction
description: Welcome to KIRA — the hotel channel manager platform built for Abode@AB.
sidebar_position: 0
slug: /
---

# KIRA Platform

KIRA is a **multi-tenant SaaS hotel channel manager** built for Abode@AB. It lets a hotel property manager update room rates and availability once, then distributes those changes to every connected OTA — Booking.com, Expedia, MakeMyTrip — in real time, and pulls all incoming reservations back into a single dashboard.

The platform is built as a **microservices monorepo**: six independent FastAPI services, a React 19 frontend, PostgreSQL with per-tenant schemas, Kafka for async event distribution, and a Kubernetes-first deployment model on AWS EKS.

---

## Platform at a Glance

```mermaid
graph LR
    Manager["Property Manager\n(browser)"]
    WebApp["web-app\nReact 19"]
    Kong["Kong Gateway\n:8000"]

    subgraph Backend["Backend Services"]
        Auth["identity-service\n:8001"]
        Rates["rate-inventory\n:8002"]
        Res["reservation\n:8003"]
        Channel["channel-engine\n:8004"]
        Notify["notification\n:8005"]
        Admin["admin-service\n:8006"]
    end

    subgraph OTAs["OTA Channels"]
        BC["Booking.com"]
        EX["Expedia"]
        MMT["MakeMyTrip"]
    end

    Manager --> WebApp --> Kong
    Kong --> Auth & Rates & Res & Channel & Notify & Admin
    Channel --> BC & EX & MMT
```

---

## Documentation Sections

### Getting Started
Set up the full stack locally and take your first tour of the platform.

- [Prerequisites](./getting-started/prerequisites.md) — tools to install before you begin
- [Local Setup](./getting-started/local-setup.md) — clone, configure, and run with Docker Compose
- [First Run](./getting-started/first-run.md) — walkthrough of creating a tenant, room types, and your first reservation
- [Project Structure](./getting-started/project-structure.md) — monorepo layout explained, folder by folder

### Architecture
How the pieces fit together.

- [Overview](./architecture/overview.md) — system topology, communication patterns, data isolation
- [Microservices](./architecture/microservices.md) — per-service responsibilities and internal layer rules
- [Multi-Tenancy](./architecture/multi-tenancy.md) — per-tenant PostgreSQL schemas and how `search_path` works
- [Event-Driven Design](./architecture/event-driven.md) — Kafka topics, event catalog, consumer groups
- [Security](./architecture/security.md) — JWT auth flow, RBAC roles, MFA, audit log

### Services
Deep-dives on each backend service.

- [Identity Service](./services/identity-service.md) — auth, users, RBAC, MFA, audit
- [Rate & Inventory Service](./services/rate-inventory-service.md) — room types, rate plans, ARI calendar
- [Reservation Service](./services/reservation-service.md) — bookings, guests, cancellation policy
- [Channel Engine](./services/channel-engine.md) — OTA adapters, ARI push/pull, Celery workers
- [Notification Service](./services/notification-service.md) — email, in-app alerts, preferences
- [Admin Service](./services/admin-service.md) — tenant onboarding, billing, super-admin ops

### Frontend
The React 19 property manager dashboard.

- [Overview](./frontend/overview.md) — tech stack, project structure, feature list
- [Architecture](./frontend/architecture.md) — routing, API layer, form and component patterns
- [State Management](./frontend/state-management.md) — TanStack Query vs. Zustand, query key strategy
- [Feature Modules](./frontend/feature-modules.md) — per-feature structure and adding new modules

### API Reference
Every endpoint documented with request/response examples.

- [Overview](./api-reference/overview.md) — conventions, auth, error format, status codes
- [Authentication](./api-reference/authentication.md) — login, MFA, token refresh
- [Rate & Inventory](./api-reference/rate-inventory.md) — room types, rate plans, ARI bulk update
- [Reservations](./api-reference/reservations.md) — create, modify, cancel bookings
- [Channels](./api-reference/channels.md) — connect OTAs, manage mappings, view sync log

### Deployment
From Docker Compose to production on AWS EKS.

- [Overview](./deployment/overview.md) — environments, image tagging, required AWS infrastructure
- [Docker](./deployment/docker.md) — Compose setup, Dockerfiles, observability stack
- [Kubernetes](./deployment/kubernetes.md) — Kustomize base + overlays, secrets, resource config
- [CI/CD](./deployment/ci-cd.md) — GitHub Actions pipelines, path filters, production approval gate

### Operations
Running the platform in production.

- [Monitoring](./operations/monitoring.md) — Prometheus metrics, Grafana dashboards, SLOs, alerts
- [Logging](./operations/logging.md) — structlog JSON format, Loki, LogQL query examples
- [Runbooks](./operations/runbooks.md) — OTA sync failures, pod crashes, Kafka lag, rollbacks

### Contributing
How to add features, fix bugs, and keep the codebase healthy.

- [Development Setup](./contributing/development-setup.md) — IDE config, running a service outside Docker
- [Code Conventions](./contributing/code-conventions.md) — Python and TypeScript style rules
- [Testing](./contributing/testing.md) — pytest patterns, coverage gate, React Testing Library
- [Git Workflow](./contributing/git-workflow.md) — branch naming, commit format, PR process

---

## Choose Your Path

### I'm setting up locally for the first time

→ Start with **[Prerequisites](./getting-started/prerequisites.md)**, then follow the **[Local Setup](./getting-started/local-setup.md)** guide. The whole stack runs with one command after that.

### I'm deploying to production

→ Go to **[Deployment Overview](./deployment/overview.md)** for the AWS infrastructure requirements, then **[Kubernetes](./deployment/kubernetes.md)** for the Kustomize manifests, and **[CI/CD](./deployment/ci-cd.md)** for the GitHub Actions pipeline setup.

### I'm adding a feature to an existing service

→ Read **[Code Conventions](./contributing/code-conventions.md)** and the relevant **[Service](./services/identity-service.md)** doc first so you understand the layer rules, then **[Git Workflow](./contributing/git-workflow.md)** for branch and PR requirements.

### I'm debugging a production issue

→ Jump straight to **[Runbooks](./operations/runbooks.md)** for step-by-step procedures, or **[Monitoring](./operations/monitoring.md)** to navigate to the right Grafana dashboard.
