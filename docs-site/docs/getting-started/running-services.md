---
sidebar_position: 7
---

# Running Services

How to run individual services during development.

## Running a Single Backend Service

Use `uv run` to execute Poetry-managed commands without activating a virtual environment manually:

```bash
cd services/identity-service

# Install dependencies
uv run poetry install

# Run dev server (hot reload)
uv run uvicorn app.main:app --reload --port 8001

# Run tests
uv run pytest -v

# Run tests with coverage
uv run pytest --cov=app --cov-report=term-missing

# Lint and format
uv run ruff check .
uv run ruff format --check .

# Apply DB migrations
uv run alembic upgrade head

# Create a new migration
uv run alembic revision --autogenerate -m "add column foo"
```

## Running the Frontend

```bash
cd web-app

# Install dependencies (use bun, not npm/yarn)
bun install

# Start dev server (http://localhost:3000)
bun run dev

# Type-check
bun run typecheck

# Build for production
bun run build

# Preview production build
bun run preview
```

## Running the documentation site

From the repo root (or `cd docs-site`):

```bash
bun install
bun run start   # http://localhost:4000 — fixed in package.json; same port as Docker host mapping
```

Or use **`kira docs dev`** / **`make docs-dev`** from the monorepo root.

## Makefile Shortcuts

The root `Makefile` provides convenience targets:

```bash
make up           # docker compose -f docker/docker-compose.yml up -d --build
make down         # docker compose … down (see Makefile COMPOSE_FULL)
make logs         # docker compose -f docker/docker-compose.yml logs -f
make migrate-all  # alembic upgrade head for all services
make test-all     # run pytest for all services
make lint-all     # ruff check + format check for all services
make docs-dev     # start Docusaurus dev server
make docs-build   # build static docs site
```

## Accessing Service APIs

When running via Docker Compose, the **Kong** proxy listens on **port 8000**. HTTP APIs are under **`/api/v1/`** (see `kong/kong.yml` for the exact paths). Examples:

```
http://localhost:8000/api/v1/auth/login     → identity-service
http://localhost:8000/api/v1/rooms          → rate-inventory-service
http://localhost:8000/api/v1/reservations   → reservation-service
http://localhost:8000/api/v1/channels       → channel-engine
http://localhost:8000/api/v1/notifications  → notification-service
http://localhost:8000/api/v1/tenants        → admin-service
```

OpenAPI (Swagger) is **not** routed through Kong; use each service port below.

Or directly by port when running a service standalone:

```
http://localhost:8001  → identity-service
http://localhost:8002  → rate-inventory-service
http://localhost:8003  → reservation-service
http://localhost:8004  → channel-engine
http://localhost:8005  → notification-service
http://localhost:8006  → admin-service
```

## Interactive API Docs

Each FastAPI service exposes Swagger UI and ReDoc:

```
http://localhost:8001/docs    # Swagger UI
http://localhost:8001/redoc   # ReDoc
```
