# KIRA

**KIRA** is a multi-tenant SaaS **hotel channel manager** for **Abode@AB**. Property managers update rates and availability once; changes flow to connected OTAs (Booking.com, Expedia, MakeMyTrip, etc.), and reservations land in one dashboard.

The repo is a **microservices monorepo**: six FastAPI services, a **React 19** app (`web-app`), PostgreSQL with per-tenant schemas, Kafka for events, Kong as the API gateway, and a **Kubernetes-first** path to AWS EKS.

---

## Documentation

| Resource                       | Contents                                                                                                                                                                                                                    |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **[`docs/`](docs/)**           | Numbered **coding blueprint**: architecture, monorepo layout, service prompts, DB schema, frontend modules, local dev. Start with [`docs/00_OVERVIEW.md`](docs/00_OVERVIEW.md).                                             |
| **[`docs-site/`](docs-site/)** | **Docusaurus** site — start with the [E2E local dev guide](docs-site/docs/getting-started/e2e-local-dev.md) and [dev dashboards & ports](docs-site/docs/getting-started/dev-dashboards.md) (**web :3000**, **docs :4000**). |

**Docs site — pick one:**

| Command               | What it does                                                                                                                     |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `make docs-dev`       | Docusaurus **dev server** on **port 4000** (same as `kira docs dev`; needs [bun](https://bun.sh)) → [http://localhost:4000](http://localhost:4000) |
| `make docs-docker-up` | **Built** docs in Docker (`--profile docs`) → host [http://localhost:4000](http://localhost:4000) (rebuild the image after editing markdown) |
| `make docs-build`     | Static output in `docs-site/build/` only                                                                                         |

---

## Quick Start

Full detail: [`docs-site/docs/getting-started/e2e-local-dev.md`](docs-site/docs/getting-started/e2e-local-dev.md).

**Prerequisites:** Docker Desktop (8 GB+ RAM), Python 3.13, [uv](https://docs.astral.sh/uv/), [bun](https://bun.sh).

```bash
git clone https://github.com/abodeab/kira.git
cd kira
uv run kira dev setup      # env files, deps, infra, migrations, seed
uv run kira dev up          # start all services (core: Kong, APIs, web-app on :3000)
uv run kira dashboards      # open many browser tabs: web :3000, docs :4000, Mailhog, Kong, each /docs
uv run kira dashboards --full   # same as above + Grafana, Prometheus, Loki, … (use after kira dev up --full)
# --full and --all are equivalent
```

**Open the web app:** [http://localhost:3000](http://localhost:3000) — login as `admin@example.com` / `Admin1234!`. The Vite dev server defaults to **3000** (`PORT` / `VITE_DEV_PORT` in `web-app/vite.config.ts`; Compose sets `PORT=3000`).

**Step by step alternative:** `make up` → `make migrate-docker-all` → `make seed-docker` (see `make help`).

:::info OpenAPI docs
Available on each **direct service port**: [http://localhost:8001/docs](http://localhost:8001/docs), etc. Not exposed via Kong. Kong serves HTTP APIs under **`/api/v1/…`** — see `kong/kong.yml`.
:::

**Celery workers:** `channel-worker` and `notification-worker` use the same code/images as **channel-engine** and **notification-service** but run **`celery worker`** only (no HTTP port in those containers).

---

## Makefile and `kira`

You can use **either** [Make](Makefile) **or** `uv run kira` for most tasks; the Makefile often delegates to the CLI (for example `make dashboards` → `kira dashboards`). For a full comparison, compose **profiles**, **host vs Docker** migrations, and **`make bootstrap`**, see the docs site: **[Makefile, CLI, and Compose](docs-site/docs/getting-started/makefile-and-cli.md)**.

---

## KIRA CLI

The monorepo ships a **`kira`** CLI (Python, powered by [Typer](https://typer.tiangolo.com/)).

- **`uv run kira <command>`** — from the **repository root** only (nearest `pyproject.toml` wins).
- **`./bin/kira <command>`** — from anywhere in the clone; resolves the repo root and runs `uv run --project <root> kira`.
- **Global `kira` on your PATH** (optional, one-time from the clone root): `uv tool install --editable .` using [uv’s tool interface](https://docs.astral.sh/uv/concepts/tools/). Then you can run `kira` from any directory, including under `services/`. Upgrade after pulls with `uv tool upgrade kira-cli`; remove with `uv tool uninstall kira-cli`. If uv warns about PATH, run `uv tool update-shell`.
- **One-off without installing:** from the clone root, `uvx --from . kira <command>`. Do **not** run plain `uvx kira` — that installs a different package from PyPI.

Full detail: [`docs-site/docs/getting-started/cli-reference.md`](docs-site/docs/getting-started/cli-reference.md#installation).

| Command                                     | What it does                                                  |
| ------------------------------------------- | ------------------------------------------------------------- |
| `kira dev setup`                            | One-shot bootstrap (env files, deps, infra, migrations, seed on **host** Postgres) |
| `kira dev e2e`                              | `setup` then **`dev up --full`** (core + observability + docs profile) |
| `kira dev up [--full]`                      | Start Docker stack (add `--full` for observability + docs-site image) |
| `kira dev down`                             | Stop containers (both compose files)                          |
| `kira dev clean`                            | Stop + remove volumes (prompts first)                         |
| `kira dev init --name alice`                | Per-developer DB isolation (`docker-compose.override.yml`)     |
| `kira dev logs [service]`                   | Tail Compose logs                                             |
| `kira dev status`                           | `docker compose ps -a`                                        |
| `kira test …` / `kira migrate …` / `kira seed …` | Pytest, Alembic, seed — see [CLI Reference](docs-site/docs/getting-started/cli-reference.md) |
| `kira lint …`                               | Ruff (services) / ESLint (web-app)                            |
| `kira deploy staging` / `production`      | Deploy scripts (EKS); `--dry-run`, `--skip-terraform`, `--services` |
| `kira commit`                               | Interactive Conventional Commit (Commitizen)                  |
| `kira dashboards [--full \| --all]`         | Open local dev URLs in the browser                            |
| `kira docs dev \| build`                    | Docusaurus dev server or build                                |

---

## Repository Layout

| Path             | Role                                                                                                                           |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `services/`      | `identity-service`, `rate-inventory-service`, `reservation-service`, `channel-engine`, `notification-service`, `admin-service` |
| `web-app/`       | Property manager dashboard (Vite, React 19, Tailwind, TanStack Query, Zustand)                                                 |
| `shared/`        | Shared Python libraries used by services (middleware, schemas, utils)                                                          |
| `docker/`        | All Dockerfiles + Docker Compose files                                                                                         |
| `cli/`           | `kira` CLI source (Typer + Rich)                                                                                               |
| `kong/`          | Kong declarative config                                                                                                        |
| `k8s/`           | Kubernetes / Kustomize manifests (base + staging / production overlays)                                                        |
| `infra/`         | Terraform for AWS (EKS, RDS, ElastiCache, ECR, etc.)                                                                           |
| `observability/` | Grafana dashboards, Prometheus config, Loki, Alloy, Portainer, pgAdmin                                                         |
| `scripts/`       | Seeding and one-off tooling                                                                                                    |
| `docs/`          | Architecture & coding blueprint (numbered markdown)                                                                            |
| `docs-site/`     | Docusaurus documentation site                                                                                                  |

Monorepo details: [`docs/02_MONOREPO_STRUCTURE.md`](docs/02_MONOREPO_STRUCTURE.md) and [`docs-site/docs/getting-started/project-structure.md`](docs-site/docs/getting-started/project-structure.md).

---

## Services and Ports (Local Compose)

| Service                | Host port                     |
| ---------------------- | ----------------------------- |
| Kong (HTTP proxy)      | [8000](http://localhost:8000) |
| Kong Admin API         | [8100](http://localhost:8100) |
| identity-service       | 8001                          |
| rate-inventory-service | 8002                          |
| reservation-service    | 8003                          |
| channel-engine         | 8004                          |
| notification-service   | 8005                          |
| admin-service          | 8006                          |
| web-app                | [3000](http://localhost:3000) |
| docs-site (optional)   | [4000](http://localhost:4000) — `make docs-dev`, `kira docs dev`, or Compose `--profile docs` |

Each backend exposes OpenAPI at `http://localhost:<port>/docs`.

---

## Observability and Debug UIs (`make up-full`)

Start the full stack with observability: `make up-full`. These URLs assume defaults from `docker/docker-compose.observability.yml` and `observability/`. **Use only on your machine** — passwords are for local dev.

| Dashboard         | URL                                              | Access / credentials                                                                                          |
| ----------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| **Grafana**       | [http://localhost:3001](http://localhost:3001)   | Anonymous **Viewer** (no login). **Sign in** as **`admin` / `admin`** to edit dashboards or settings.         |
| **Prometheus**    | [http://localhost:9090](http://localhost:9090)   | No authentication.                                                                                            |
| **Loki**          | [http://localhost:3100](http://localhost:3100)   | **HTTP API only** (root `/` often 404). Query logs in **Grafana → Explore → Loki**; try `/ready` or `/metrics` to verify the process. |
| **Grafana Alloy** | [http://localhost:12345](http://localhost:12345) | Ships Docker logs to Loki (replaces EOL Promtail); optional debug UI.                                         |
| **Kafka UI**      | [http://localhost:8080](http://localhost:8080)   | No login (local dev).                                                                                         |
| **Redis Insight** | [http://localhost:5540](http://localhost:5540)   | Add a Redis connection manually (see [dev dashboards](docs-site/docs/getting-started/dev-dashboards.md)).      |
| **pgAdmin**       | [http://localhost:5050](http://localhost:5050)   | **`admin@kira.dev` / `admin`**. Pre-registered server **KIRA Local**.                                         |
| **Portainer**     | [http://localhost:9000](http://localhost:9000)   | HTTP UI; HTTPS on [9443](https://localhost:9443). Password: [dev dashboards](docs-site/docs/getting-started/dev-dashboards.md). |
| **Mailhog**       | [http://localhost:8025](http://localhost:8025)   | No login (starts with `make up`).                                                                             |

**Postgres:** host `localhost`, port **`5432`**, database **`kira`**, user **`postgres`**, password **`postgres`**.

**Redis:** host **`localhost`**, port **`6379`**, password **`redis-local-dev`** (matches Compose).

**Kafka (host tools):** broker on **`127.0.0.1:9092`** (bound to loopback in Compose to reduce noise from random internet scans).

More detail: [`docs-site/docs/getting-started/dev-dashboards.md`](docs-site/docs/getting-started/dev-dashboards.md).

---

## Troubleshooting (quick hits)

| Symptom | What to check |
|--------|----------------|
| `uv run kira` fails inside `services/…` | Run from **repo root**, or `./bin/kira`, or `uv tool install --editable .` — see [CLI Reference](docs-site/docs/getting-started/cli-reference.md#installation). |
| Grafana / `:3001` never loads | You need **`kira dev up --full`** or `make up-full`, not core-only `up`. |
| `:8003` / reservation flapping | Ensure **Kafka** is healthy; **`docker compose … logs reservation-service`**. After DB changes, **`kira migrate reservation-service --docker`**. |
| Worker container “connection refused” to `:8004` | Celery workers are **not** HTTP servers; ignore API **HEALTHCHECK** noise if you are on an older compose revision — workers disable that check in current `docker-compose.yml`. |
| Loki **404** on `/` | Expected — use **Grafana** for log UI ([makefile-and-cli doc](docs-site/docs/getting-started/makefile-and-cli.md#loki-on-3100-returns-404)). |

Longer walkthrough: [`docs-site/docs/getting-started/e2e-local-dev.md#troubleshooting`](docs-site/docs/getting-started/e2e-local-dev.md#troubleshooting).

---

## Tech Stack

**Python 3.13+**, **FastAPI**, **SQLAlchemy 2** (async), **Pydantic v2**, **Alembic**, **Kafka**, **Redis**, **Celery**; frontend **TypeScript**, **Vite**, **Tailwind**, **shadcn/ui**; DX **Bun**, **Husky**, **Commitizen**, **Commitlint**, **lint-staged**; infra **Docker**, **Kubernetes**, **Kong**, **GitHub Actions**, **AWS** (EKS, RDS, etc.).

---

## Contributing

See [`docs-site/docs/contributing/development-workflow.md`](docs-site/docs/contributing/development-workflow.md).

**Commits:** KIRA enforces [Conventional Commits](https://www.conventionalcommits.org/) via Husky + Commitlint. Use `uv run kira commit` for the interactive prompt.

---

## More documentation

| Topic | Link |
|-------|------|
| End-to-end local dev (single page) | [`e2e-local-dev.md`](docs-site/docs/getting-started/e2e-local-dev.md) |
| Makefile vs CLI, Compose profiles | [`makefile-and-cli.md`](docs-site/docs/getting-started/makefile-and-cli.md) |
| Every `kira` command | [`cli-reference.md`](docs-site/docs/getting-started/cli-reference.md) |
| Ports & sign-ins | [`dev-dashboards.md`](docs-site/docs/getting-started/dev-dashboards.md) |
| Compose service-by-service | [`local-docker.md`](docs-site/docs/deployment/local-docker.md) |
| Monorepo tour | [`project-structure.md`](docs-site/docs/getting-started/project-structure.md) |
| Numbered internal blueprint (`docs/`) | [`00_OVERVIEW.md`](docs/00_OVERVIEW.md) |
