# KIRA

**KIRA** is a multi-tenant SaaS **hotel channel manager** for **Abode@AB**. Property managers update rates and availability once; changes flow to connected OTAs (Booking.com, Expedia, MakeMyTrip, etc.), and reservations land in one dashboard.

The repo is a **microservices monorepo**: six FastAPI services, a **React 19** app (`web-app`), PostgreSQL with per-tenant schemas, Kafka for events, Kong as the API gateway, and a **Kubernetes-first** path to AWS EKS.

---

## Documentation

| Resource | Contents |
|----------|----------|
| **[`docs/`](docs/)** | Numbered **coding blueprint**: architecture, monorepo layout, service prompts, DB schema, frontend modules, local dev. Start with [`docs/00_OVERVIEW.md`](docs/00_OVERVIEW.md). |
| **[`docs-site/`](docs-site/)** | **Docusaurus** site — start with [local setup](docs-site/docs/getting-started/local-setup.md) and [dev dashboards & ports](docs-site/docs/getting-started/dev-dashboards.md) (**web :3000**, **docs :4000**). |

**Docs site — pick one:**

| Command | What it does |
|---------|----------------|
| `make docs-dev` | Docusaurus **dev server** with hot reload (needs [bun](https://bun.sh)) → [http://localhost:4000](http://localhost:4000) |
| `make docs-docker-up` | **Built** docs served by nginx in Docker → [http://localhost:4000](http://localhost:4000) (rebuild image after editing markdown) |
| `make docs-build` | Static output in `docs-site/build/` only |

---

## Quick start (Docker — recommended)

Full detail: [`docs-site/docs/getting-started/local-setup.md`](docs-site/docs/getting-started/local-setup.md).

1. **Prerequisites:** Docker Desktop (8 GB+ RAM). Optional on the host: Python 3.13 + [uv](https://docs.astral.sh/uv/) if you run migrations/tests outside containers; [bun](https://bun.sh) only for `make docs-dev`.

2. **Environment:** The repo ships `services/*/.env.local` for local Compose (Postgres/Redis/Kafka hostnames + shared dev `SECRET_KEY`). Adjust or copy from `.env.example` if needed.

3. **One-shot setup** (starts stack, waits for Postgres, runs **Alembic inside each service container**, then **seeds via Docker network**):

   ```bash
   make bootstrap
   ```

   Or step by step: `make up` → `make migrate-docker-all` → `make seed-docker`.

4. **Open the web app:** [http://localhost:3000](http://localhost:3000) — the Vite container proxies `/api` to Kong (`API_PROXY_TARGET=http://kong:8000`).

5. **OpenAPI (Swagger)** for each service is only on the **direct service ports**, e.g. [http://localhost:8001/docs](http://localhost:8001/docs). Kong routes `/api/v1/...` only — **not** `/docs`, so `http://localhost:8000/docs` will not show service Swagger.

**Host-only alternative** (Postgres exposed on `localhost:5432`): `make migrate-all` and `make seed` using `uv` on your machine.

**Useful commands:** `make help` — `bootstrap`, `up`, `up-full`, `migrate-docker-all`, `seed-docker`, `dashboards`, `dashboards-full`, `docs-dev`, `docs-docker-up`.

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

Aligned with [`docs/00_OVERVIEW.md`](docs/00_OVERVIEW.md) and the docs site: **Python 3.13+**, **FastAPI**, **SQLAlchemy 2** (async), **Pydantic v2**, **Alembic**, **Kafka**, **Redis**, **Celery**; frontend **TypeScript**, **Vite**, **Tailwind**, **shadcn/ui**; infra **Docker**, **Kubernetes**, **Kong**, **GitHub Actions**, **AWS** (EKS, RDS, etc.) for production paths.

---

## Contributing

Follow [`docs-site/docs/contributing/development-setup.md`](docs-site/docs/contributing/development-setup.md), [`docs-site/docs/contributing/git-workflow.md`](docs-site/docs/contributing/git-workflow.md), and [`docs-site/docs/contributing/code-conventions.md`](docs-site/docs/contributing/code-conventions.md).
