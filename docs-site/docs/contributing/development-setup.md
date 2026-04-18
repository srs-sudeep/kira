---
sidebar_position: 1
---

# Development Setup

## Fork and Clone

```bash
git clone https://github.com/abodeab/kira.git
cd kira
```

## Install Tools

See [Prerequisites](../getting-started/prerequisites) for required tools.

## Configure Environment

```bash
cp .env.example .env
# Edit .env with your local values
```

## Start Infrastructure Only

If you want to run a single service locally (outside Docker) while keeping the rest containerized, start the stack from the **repo root** (Compose needs **`-f docker/docker-compose.yml`**):

```bash
# Full core stack (simplest — includes Kong + APIs + web; stop what you do not need)
uv run kira dev up
# Make: make up

# Or: infra only
docker compose -f docker/docker-compose.yml up -d postgres redis kafka

# Run your service locally (e.g., identity-service)
cd services/identity-service
uv run poetry install
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8001
```

## IDE Setup

### VS Code

Recommended extensions:
- Python (ms-python.python)
- Pylance
- Ruff (charliermarsh.ruff)
- ESLint
- Tailwind CSS IntelliSense
- Docker
- YAML

Add to `.vscode/settings.json`:
```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  },
  "python.linting.enabled": false,
  "ruff.lint.enable": true
}
```

### PyCharm / IntelliJ

Configure the Python interpreter to use the uv virtual environment:
```bash
cd services/identity-service
uv run which python  # copy this path
```

## Running Tests Locally

From the **repo root** (same commands Husky uses via Make):

```bash
uv run kira test identity-service    # Make: make test-identity-service
uv run kira test --all --no-web      # Make: make test-all
uv run kira test --web               # Make: make test-web
uv run kira test --integration       # Make: make test-integration
```

Inside a single service directory:

```bash
cd services/identity-service
uv run pytest -v
uv run pytest --cov=app --cov-report=html   # open htmlcov/index.html
uv run pytest -f   # watch mode
```

A test database is created automatically by the test fixtures — no manual setup needed as long as PostgreSQL is running.

## Pre-commit Checks

Before pushing, mirror what **Husky** runs:

```bash
# Full monorepo lint (pre-commit runs this after lint-staged)
uv run kira lint --all
uv run kira lint --all --fix

# Or per service / web (when iterating)
cd services/identity-service && uv run ruff check . && uv run ruff format --check .
cd web-app && bun run lint
```

Full pre-push gate from root: **`make test-pre-push`** or **`uv run kira push -y`** (then push). See **[Git, Husky hooks, and pushes](./git-hooks-and-pushes.md)**.
