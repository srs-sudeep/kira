---
title: Adding a Service
description: Everything you need to create a new KIRA microservice — directory structure, wiring into Docker Compose, Kong, and Kubernetes.
sidebar_position: 3
---

# Adding a Service

**What you'll learn:**
- The files and directories a new service needs
- What to configure manually (Docker Compose, Kong, K8s)
- How to add CI/CD for the new service

---

## When to Add a Service

Add a new service when the functionality you are building:
- Owns a distinct domain with its own database tables
- Has a clearly different scaling profile from existing services
- Will be deployed and updated independently

If it is a new feature within an existing domain (e.g., adding a new report type to rate-inventory), add it to the existing service instead.

---

## New Service Directory Structure

Create `services/<service-name>/` following this layout:

```
services/yield-optimizer/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app factory, lifespan, middleware
│   ├── config.py            # Pydantic BaseSettings
│   ├── database.py          # async_sessionmaker, get_session()
│   ├── dependencies.py      # FastAPI Depends() functions
│   ├── exceptions.py        # domain exceptions
│   ├── exception_handlers.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── yield_router.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── yield_service.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── yield_repository.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── yield_schemas.py
│   └── models/
│       ├── __init__.py
│       └── yield_model.py
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── .gitkeep
├── tests/
│   ├── conftest.py
│   └── test_yield_service.py
├── alembic.ini
├── pyproject.toml
├── poetry.lock
├── Dockerfile
└── .env.example
```

### Copy from an existing service

The fastest way to bootstrap:

```bash
cp -r services/admin-service services/yield-optimizer
```

Then update:
- `pyproject.toml` — change `name`, `description`, update dependencies as needed
- `app/config.py` — add service-specific settings
- `app/main.py` — change `title`, `description`, update router imports
- `alembic.ini` — update `script_location` and `sqlalchemy.url` placeholder
- `Dockerfile` — update `EXPOSE` port and `CMD` port number
- `.env.example` — add service-specific variables

---

## What to Add Manually

### 1. `.env.local` (not committed)

```bash
cp services/yield-optimizer/.env.example services/yield-optimizer/.env.local
# Edit .env.local with your local values
```

### 2. `docker-compose.yml`

Add the new service following the existing pattern:

```yaml
yield-optimizer:
  <<: *app-defaults
  build:
    context: .
    dockerfile: services/yield-optimizer/Dockerfile
  env_file: ./services/yield-optimizer/.env.local
  ports:
    - "8007:8007"
  volumes:
    - ./services/yield-optimizer/app:/app/app
    - ./shared:/app/shared
  command: uvicorn app.main:app --host 0.0.0.0 --port 8007 --reload
```

Choose a port not already in use. Services are currently at 8001–8006; 8007 is next.

### 3. `kong/kong.yml`

Add routes for the new service:

```yaml
services:
  - name: yield-optimizer
    url: http://yield-optimizer:8007
    routes:
      - name: yield-optimizer-route
        paths: [/api/v1/yield]
        strip_path: false
```

### 4. Kubernetes manifests

Create `k8s/base/yield-optimizer/` with three files:

**`deployment.yaml`** — copy from `k8s/base/admin-service/deployment.yaml`, change:
- `metadata.name`, `spec.selector.matchLabels`, `spec.template.metadata.labels` → `yield-optimizer`
- `containerPort` → 8007
- Liveness/readiness probe ports → 8007
- `image` → `kira-yield-optimizer:latest`
- Environment variables (add service-specific secrets/config)

**`service.yaml`** — copy and change name and port:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: yield-optimizer
spec:
  selector:
    app: yield-optimizer
  ports:
    - port: 8007
      targetPort: 8007
```

**`hpa.yaml`** — copy and change `scaleTargetRef.name` → `yield-optimizer`

Add the new directory to `k8s/base/kustomization.yaml`:

```yaml
resources:
  - ...existing services...
  - yield-optimizer
```

### 5. GitHub Actions CI

Copy an existing workflow:

```bash
cp .github/workflows/ci-admin-service.yml .github/workflows/ci-yield-optimizer.yml
```

Update the three env vars at the top:

```yaml
env:
  SERVICE: yield-optimizer
  IMAGE_NAME: kira-yield-optimizer
  WORKDIR: services/yield-optimizer
```

Update `paths` trigger to `services/yield-optimizer/**`.

Add to `deploy-production.yml`'s service choices:

```yaml
inputs:
  service:
    options:
      - ...
      - yield-optimizer
```

### 6. ECR repository

Add to Terraform:

```hcl
resource "aws_ecr_repository" "yield_optimizer" {
  name = "kira-yield-optimizer"
  tags = local.common_tags
}
```

---

## Alembic for the New Service

The new service gets its own Alembic migration chain:

```bash
# Generate the first migration (creates the initial table)
cd services/yield-optimizer
uv run alembic revision --autogenerate -m "create yield tables"
```

Run migrations locally:

```bash
docker compose exec yield-optimizer uv run alembic upgrade head
```

---

## Shared Code

If the new service needs tenant middleware, event schemas, or crypto utilities, import from `shared/`:

```python
from shared.middleware.tenant import TenantMiddleware
from shared.schemas.events import KiraEvent
from shared.utils.crypto import encrypt, decrypt
```

The `shared/` directory is mounted into every container at `/app/shared` and installed as a local package via `pyproject.toml`.

Do not copy code from `shared/` into the service directory. If you need to extend shared utilities, modify `shared/` and all services pick up the change automatically.

---

## Architecture Checklist for New Services

- [ ] Owns its data — no reads or writes to other services' tables
- [ ] Only communicates with other services via REST (sync) or Kafka (async)
- [ ] Has its own Alembic migration chain
- [ ] Config via Pydantic BaseSettings — no hardcoded values
- [ ] All handlers are async
- [ ] Has a `/health` endpoint (GET, returns 200)
- [ ] Test coverage ≥ 70% on service layer
- [ ] Added to `docker-compose.yml`, Kong, K8s base, and CI workflow
