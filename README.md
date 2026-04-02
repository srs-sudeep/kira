# KIRA

**KIRA** is a multi-tenant SaaS **hotel channel manager** for **Abode@AB**. Property managers update rates and availability once; changes flow to connected OTAs (Booking.com, Expedia, MakeMyTrip, etc.), and reservations land in one dashboard.

The repo is a **microservices monorepo**: six FastAPI services, a **React 19** app (`web-app`), PostgreSQL with per-tenant schemas, Kafka for events, Kong as the API gateway, and a **Kubernetes-first** path to AWS EKS.

---

## Documentation

| Resource | Contents |
|----------|----------|
| **[`docs/`](docs/)** | Numbered **coding blueprint**: architecture, monorepo layout, service prompts, DB schema, frontend modules, local dev. Start with [`docs/00_OVERVIEW.md`](docs/00_OVERVIEW.md). |
| **[`docs-site/`](docs-site/)** | **Docusaurus** site: getting started (prerequisites, local setup, first run), architecture, per-service guides, API reference, deployment, operations, contributing. |

**Run the docs site locally** (needs [bun](https://bun.sh)):

```bash
make docs-dev
```

Open [http://localhost:4000](http://localhost:4000). For a production static build: `make docs-build` (output in `docs-site/build/`).

---

## Quick start (local)

Full detail: [`docs-site/docs/getting-started/local-setup.md`](docs-site/docs/getting-started/local-setup.md).

1. **Prerequisites:** Docker Desktop (8 GB+ RAM), Python 3.12, [uv](https://docs.astral.sh/uv/), [bun](https://bun.sh) (for the web app and docs).

2. **Environment:** Copy each service’s `.env.example` to `.env.local` under `services/<name>/`. Generate `SECRET_KEY` and `JWT_SECRET_KEY` for `identity-service` (see the local-setup doc).

3. **Start the stack:**

   ```bash
   make up
   ```

4. **Migrations and seed data:**

   ```bash
   make migrate-all
   make seed
   ```

5. **Open the app:** [http://localhost:3000](http://localhost:3000) — e.g. hotel admin `manager@grandhotel.local` / `Manager1234!`, or super-admin `admin@kira.local` / `Admin1234!` (see [`docs-site/docs/getting-started/first-run.md`](docs-site/docs/getting-started/first-run.md)).

**Useful commands:** `make help` — `up`, `up-full`, `down`, `clean`, `migrate-all`, `seed`, `test-<service>`, `dashboards`, `docs-dev`.

---

## Repository layout (high level)

| Path | Role |
|------|------|
| `services/` | `identity-service`, `rate-inventory-service`, `reservation-service`, `channel-engine`, `notification-service`, `admin-service` |
| `web-app/` | Property manager dashboard (Vite, React 19, Tailwind, TanStack Query, Zustand) |
| `packages/` | Shared Python libraries used by services |
| `kong/` | Kong declarative config |
| `k8s/` | Kubernetes / Kustomize manifests |
| `scripts/` | Seeding and tooling |

Monorepo details: [`docs/02_MONOREPO_STRUCTURE.md`](docs/02_MONOREPO_STRUCTURE.md) and [`docs-site/docs/getting-started/project-structure.md`](docs-site/docs/getting-started/project-structure.md).

---

## Services and ports (local Compose)

| Service | Host port |
|---------|-----------|
| Kong (HTTP proxy) | [8000](http://localhost:8000) |
| Kong Admin API | [8100](http://localhost:8100) |
| identity-service | 8001 |
| rate-inventory-service | 8002 |
| reservation-service | 8003 |
| channel-engine | 8004 |
| notification-service | 8005 |
| admin-service | 8006 |
| web-app | 3000 |

Each backend exposes OpenAPI at `http://localhost:<port>/docs`.

---

## Tech stack (summary)

Aligned with [`docs/00_OVERVIEW.md`](docs/00_OVERVIEW.md) and the docs site: **Python 3.12+**, **FastAPI**, **SQLAlchemy 2** (async), **Pydantic v2**, **Alembic**, **Kafka**, **Redis**, **Celery**; frontend **TypeScript**, **Vite**, **Tailwind**, **shadcn/ui**; infra **Docker**, **Kubernetes**, **Kong**, **GitHub Actions**, **AWS** (EKS, RDS, etc.) for production paths.

---

## Contributing

Follow [`docs-site/docs/contributing/development-setup.md`](docs-site/docs/contributing/development-setup.md), [`docs-site/docs/contributing/git-workflow.md`](docs-site/docs/contributing/git-workflow.md), and [`docs-site/docs/contributing/code-conventions.md`](docs-site/docs/contributing/code-conventions.md).
