---
sidebar_position: 7
---

# Running Services

How to run individual services during development.

## Monorepo commands (prefer the CLI)

From the **repository root**, the **`kira`** CLI is the primary interface; **`make`** targets are thin wrappers around **`uv run kira …`** (same flags). See **[Makefile, CLI, and Compose](./makefile-and-cli.md)** and **[CLI Reference](./cli-reference.md)**.

| Goal | CLI | Make (optional) |
|------|-----|------------------|
| Core stack | `uv run kira dev up` | `make up` |
| + Observability | `uv run kira dev up --full` | `make up-full` |
| Stop (keep volumes) | `uv run kira dev down` | `make down` |
| Wipe volumes | `uv run kira dev clean --yes` | `make clean` |
| Logs | `uv run kira dev logs [service]` | `make logs` / `make logs-<service>` |
| Container status | `uv run kira dev status` | `make stack-status` |
| All backend tests | `uv run kira test --all --no-web` | `make test-all` |
| Web tests | `uv run kira test --web` | `make test-web` |
| Integration tests | `uv run kira test --integration` | `make test-integration` |
| Full monorepo lint | `uv run kira lint --all` | (run via Husky pre-commit; no `make lint-*`) |
| Migrate all (Docker) | `uv run kira migrate --all --docker` | `make migrate-docker-all` |
| Docs dev server | `uv run kira docs dev` | `make docs-dev` |

---

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

From the **repo root** you can also run **`uv run kira test identity-service`**, **`uv run kira lint identity-service`**, etc.

---

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

---

## Running the documentation site

From the repo root:

```bash
uv run kira docs dev        # Make: make docs-dev
uv run kira docs build      # Make: make docs-build
uv run kira docs docker-up  # Make: make docs-docker-up
```

---

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
