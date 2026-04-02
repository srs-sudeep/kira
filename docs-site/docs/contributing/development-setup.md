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

If you want to run a single service locally (outside Docker) while keeping the rest containerized:

```bash
# Start infrastructure and all other services
docker compose up -d postgres redis kafka zookeeper kong

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

```bash
# Single service
cd services/identity-service
uv run pytest -v

# With coverage
uv run pytest --cov=app --cov-report=html
# Open htmlcov/index.html

# Watch mode
uv run pytest -f
```

A test database is created automatically by the test fixtures — no manual setup needed as long as PostgreSQL is running.

## Pre-commit Checks

Before pushing, ensure your changes pass:

```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check (if mypy is configured)
uv run mypy app/

# Tests
uv run pytest --cov=app --cov-fail-under=70
```

The CI will fail if any of these fail.
