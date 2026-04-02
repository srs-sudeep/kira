---
sidebar_position: 4
---

# CI/CD Pipelines

KIRA uses GitHub Actions with one workflow per service plus a shared production deploy workflow.

## Per-Service CI Workflow

Each backend service has a workflow at `.github/workflows/ci-{service}.yml`.

### Trigger

```yaml
on:
  push:
    branches: [main]
    paths:
      - 'services/{service-name}/**'
      - '.github/workflows/ci-{service-name}.yml'
  pull_request:
    paths:
      - 'services/{service-name}/**'
```

Path filtering means a push to `services/channel-engine/` only triggers the channel-engine workflow — not all 6.

### Jobs

#### 1. test

Runs on every push and PR:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    env:
      POSTGRES_DB: test_db
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
  redis:
    image: redis:7-alpine
```

Steps:
1. Checkout code
2. Install `uv` via `astral-sh/setup-uv@v4`
3. `uv run poetry install`
4. `uv run ruff check .` (lint)
5. `uv run ruff format --check .` (format check)
6. `uv run pytest --cov=app --cov-fail-under=70` (tests + coverage gate)

#### 2. build-and-push

Runs only on `main` branch push (after test passes):

1. Configure AWS credentials via OIDC
2. Login to ECR with `aws-actions/amazon-ecr-login@v2`
3. Set up Docker Buildx with GitHub Actions cache (`type=gha`)
4. Build and push: `{ECR_REGISTRY}/{service}:{GITHUB_SHA::8}`

#### 3. deploy-staging

Runs after `build-and-push` succeeds:

1. Configure AWS credentials
2. `aws eks update-kubeconfig`
3. `kubectl set image deployment/kira-{service} kira-{service}={image}:{sha} -n kira-staging`
4. `kubectl rollout status deployment/kira-{service} -n kira-staging`

## Production Deploy Workflow

`.github/workflows/deploy-production.yml` is triggered manually via `workflow_dispatch`.

```yaml
on:
  workflow_dispatch:
    inputs:
      service:
        description: 'Service to deploy'
        type: choice
        options: [all, identity-service, rate-inventory-service, ...]
        required: true
      image_tag:
        description: 'Image tag (git SHA) to deploy'
        type: string
        required: true
```

The job runs with `environment: production`, which requires manual approval from a GitHub environment reviewer before the deployment step executes.

### Deploying to Production

1. Verify the staging deployment is stable
2. Go to GitHub → Actions → "Deploy to Production"
3. Click "Run workflow"
4. Enter the service name and image tag (git SHA from the CI run)
5. A designated reviewer approves the environment
6. Deployment proceeds: `kubectl set image` + `kubectl rollout status`

## Web App CI

`.github/workflows/ci-web-app.yml` follows the same pattern:

- **test job:** `bun install`, TypeScript type-check, ESLint
- **build-and-push:** `bun run build` with `VITE_API_BASE_URL` build arg, push to ECR
- **deploy-staging:** `kubectl set image deployment/kira-web-app`

## Coverage Gate

Tests must achieve ≥ 70% coverage on `app/` code:

```bash
uv run pytest --cov=app --cov-fail-under=70
```

If coverage drops below 70%, the `test` job fails and the workflow stops — no image is built or deployed.
