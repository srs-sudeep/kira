---
sidebar_position: 4
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

## Makefile Shortcuts

The root `Makefile` provides convenience targets:

```bash
make up           # docker compose up -d --build
make down         # docker compose down
make logs         # docker compose logs -f
make migrate-all  # alembic upgrade head for all services
make test-all     # run pytest for all services
make lint-all     # ruff check + format check for all services
make docs-dev     # start Docusaurus dev server
make docs-build   # build static docs site
```

## Accessing Service APIs

When running via Docker Compose, services are accessible through the Kong gateway at port 8000:

```
http://localhost:8000/identity/  → identity-service
http://localhost:8000/rates/     → rate-inventory-service
http://localhost:8000/bookings/  → reservation-service
http://localhost:8000/channels/  → channel-engine
http://localhost:8000/notify/    → notification-service
http://localhost:8000/admin/     → admin-service
```

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
