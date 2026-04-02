# Microservices, Docker, Kubernetes & CI/CD — Complete Guide

## Table of Contents
1. Microservices Concepts
2. Docker — Packaging Services
3. Kubernetes — Running Services
4. GitHub Actions — CI/CD Pipeline
5. Step-by-Step Setup Order
6. Local Development Workflow
7. Production Deployment Strategy

---

## 1. Microservices Concepts

### What is a microservice?
A microservice is a small, independent application that does ONE domain job. It has its own codebase, its own database schema, its own API, and runs in its own container. Services communicate via REST (synchronous) or Kafka events (asynchronous).

### Our services for Abode@AB:

| Service | Port | Responsibility | Owns Data |
|---------|------|---------------|-----------|
| API Gateway (Kong) | 8000 | Route requests, SSL, rate limiting, CORS | — (stateless) |
| Identity Service | 8001 | Auth, users, RBAC, MFA, sessions, audit log | users, refresh_tokens, audit_events |
| Rate & Inventory Service | 8002 | Room types, rate plans, ARI calendar, seasonal rules | room_types, rate_plans, ari_snapshots |
| Reservation Service | 8003 | Booking lifecycle, guests, modifications, cancellations | reservations, guest_profiles |
| Channel Engine | 8004 | OTA adapters, ARI push/pull, sync, retry, circuit breaker | channels, channel_mappings, sync_logs |
| Notification Service | 8005 | Email, in-app alerts, notification centre, preferences | notifications, notification_preferences |
| Admin / Tenant Service | 8006 | Tenant onboarding, config, billing, super-admin | tenants, tenant_configs |
| Web Application | 80 | React SPA served via nginx | — (static files) |

### Communication patterns:

**Synchronous (REST via API Gateway):**
- User actions that need an immediate response
- Example: "Create a reservation" → POST to Reservation Service → wait for confirmation → return to user
- Gateway routes: `/api/v1/auth/*` → Identity:8001, `/api/v1/rooms/*` → Rate:8002, etc.

**Asynchronous (Kafka events):**
- Background processing, cross-service reactions
- Kafka topics: `ari.updated`, `reservation.created`, `reservation.cancelled`, `reservation.modified`, `channel.sync.result`, `channel.sync.failed`
- Example: Rate update → publishes `ari.updated` → Channel Engine subscribes → pushes to OTAs in background

**Service-to-service REST (internal, no gateway):**
- When Service A needs data from Service B synchronously
- Uses K8s internal DNS: `http://identity-service:8001/api/v1/internal/validate-token`
- Example: Reservation Service calls Identity Service to validate a user token for an internal operation

### The golden rule: each service owns its data
- The Channel Engine NEVER writes directly to the reservations table
- It publishes a `reservation.created` event → Reservation Service consumes it and does the write
- This prevents tight coupling and data integrity issues

---

## 2. Docker — Packaging Services

### What Docker does
Docker packages your Python app + all dependencies into a portable "container image." This image runs identically everywhere — your laptop, CI server, staging, production.

### Dockerfile template (same for every service):

```dockerfile
# ── Build stage ──
FROM python:3.12-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev
COPY pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install .

# ── Runtime stage ──
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local
COPY app/ ./app/
EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

Key points:
- Two-stage build: builder installs dependencies, runtime is smaller (no gcc)
- HEALTHCHECK tells Docker/K8s when the service is ready
- Each service changes the port number (8001, 8002, 8003, etc.)

### Building and pushing images:

```bash
# Build
docker build -t abodeatab/identity-service:1.0.0 -f services/identity-service/Dockerfile services/identity-service/

# Tag for AWS ECR
docker tag abodeatab/identity-service:1.0.0 123456789.dkr.ecr.ap-south-1.amazonaws.com/identity-service:1.0.0

# Push to ECR
docker push 123456789.dkr.ecr.ap-south-1.amazonaws.com/identity-service:1.0.0
```

In practice, CI/CD does all of this automatically (see Section 4).

### docker-compose.yml for local development:

```yaml
services:
  # ── Infrastructure ──
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: abodeatab
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

  kafka:
    image: confluentinc/cp-kafka:7.6.0
    ports: ["9092:9092"]
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:29093
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:29093
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      CLUSTER_ID: "MkU3OEVBNTcwNTJENDM2Qk"

  # ── Application Services ──
  identity-service:
    build:
      context: ./services/identity-service
    ports: ["8001:8001"]
    env_file: ./services/identity-service/.env
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
    volumes:
      - ./services/identity-service/app:/app/app  # Hot reload
      - ./shared:/app/shared
    command: uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

  rate-inventory-service:
    build:
      context: ./services/rate-inventory-service
    ports: ["8002:8002"]
    env_file: ./services/rate-inventory-service/.env
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
      kafka: { condition: service_started }
    volumes:
      - ./services/rate-inventory-service/app:/app/app
      - ./shared:/app/shared
    command: uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

  reservation-service:
    build:
      context: ./services/reservation-service
    ports: ["8003:8003"]
    env_file: ./services/reservation-service/.env
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
      kafka: { condition: service_started }
    volumes:
      - ./services/reservation-service/app:/app/app
      - ./shared:/app/shared
    command: uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload

  channel-engine:
    build:
      context: ./services/channel-engine
    ports: ["8004:8004"]
    env_file: ./services/channel-engine/.env
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
      kafka: { condition: service_started }
    volumes:
      - ./services/channel-engine/app:/app/app
      - ./shared:/app/shared
    command: uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload

  notification-service:
    build:
      context: ./services/notification-service
    ports: ["8005:8005"]
    env_file: ./services/notification-service/.env
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
      kafka: { condition: service_started }
    volumes:
      - ./services/notification-service/app:/app/app
      - ./shared:/app/shared
    command: uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload

  admin-service:
    build:
      context: ./services/admin-service
    ports: ["8006:8006"]
    env_file: ./services/admin-service/.env
    depends_on:
      postgres: { condition: service_healthy }
    volumes:
      - ./services/admin-service/app:/app/app
      - ./shared:/app/shared
    command: uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload

  web-app:
    build:
      context: ./web-app
    ports: ["3000:80"]

  # ── Celery Workers (one per service that needs background tasks) ──
  channel-worker:
    build:
      context: ./services/channel-engine
    env_file: ./services/channel-engine/.env
    depends_on: [redis, kafka, postgres]
    volumes:
      - ./services/channel-engine/app:/app/app
      - ./shared:/app/shared
    command: celery -A app.tasks.celery_app worker --loglevel=info -Q channel_tasks

  notification-worker:
    build:
      context: ./services/notification-service
    env_file: ./services/notification-service/.env
    depends_on: [redis, kafka]
    volumes:
      - ./services/notification-service/app:/app/app
      - ./shared:/app/shared
    command: celery -A app.tasks.celery_app worker --loglevel=info -Q notification_tasks

  # ── API Gateway (local proxy) ──
  kong:
    image: kong:3.6
    environment:
      KONG_DATABASE: "off"
      KONG_DECLARATIVE_CONFIG: /etc/kong/kong.yml
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_ADMIN_ACCESS_LOG: /dev/stdout
    volumes:
      - ./k8s/kong/kong.yml:/etc/kong/kong.yml
    ports:
      - "8000:8000"   # Proxy
      - "8443:8443"   # Proxy SSL
      - "8444:8444"   # Admin API
    depends_on:
      - identity-service
      - rate-inventory-service
      - reservation-service
      - channel-engine
      - notification-service
      - admin-service

volumes:
  pgdata:
```

---

## 3. Kubernetes — Running Services

### Key concepts (simplified):

| Concept | What it is | Analogy |
|---------|-----------|---------|
| Pod | One running instance of your service | One employee doing a job |
| Deployment | "I want N copies of this service running" | A job description + headcount |
| Service (K8s) | A stable address for your pods | A department phone number |
| Ingress | External traffic routing into the cluster | The reception desk |
| HPA | Auto-scaling rule based on CPU/memory | "Hire temp staff when busy" |
| Namespace | Logical grouping of resources | A floor in the building |
| ConfigMap | Non-secret config (environment variables) | Bulletin board |
| Secret | Sensitive config (passwords, API keys) | Locked safe |

### K8s manifest for a service (example: Identity Service):

```yaml
# k8s/base/identity-service/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: identity-service
  namespace: abodeatab
  labels:
    app: identity-service
spec:
  replicas: 1                          # Phase 1: 1 replica. Phase 2: increase to 2-3.
  selector:
    matchLabels:
      app: identity-service
  template:
    metadata:
      labels:
        app: identity-service
    spec:
      containers:
        - name: identity-service
          image: 123456789.dkr.ecr.ap-south-1.amazonaws.com/identity-service:latest
          ports:
            - containerPort: 8001
          envFrom:
            - configMapRef:
                name: identity-service-config
            - secretRef:
                name: identity-service-secrets
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8001
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 8001
            initialDelaySeconds: 5
            periodSeconds: 10
---
# k8s/base/identity-service/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: identity-service
  namespace: abodeatab
spec:
  selector:
    app: identity-service
  ports:
    - port: 8001
      targetPort: 8001
  type: ClusterIP                      # Internal only — gateway handles external
---
# k8s/base/identity-service/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: identity-service-hpa
  namespace: abodeatab
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: identity-service
  minReplicas: 1
  maxReplicas: 5
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

Every service gets the same three files (deployment + service + HPA) with only the name, port, and image changing.

### Scaling from Phase 1 to Phase 2:

```yaml
# Phase 1: single replica, single node
spec:
  replicas: 1
  resources:
    requests: { memory: "256Mi", cpu: "100m" }

# Phase 2: just change the numbers
spec:
  replicas: 3                          # 3 pods, K8s spreads across nodes
  resources:
    requests: { memory: "512Mi", cpu: "250m" }

# Or let HPA handle it automatically:
# minReplicas: 2, maxReplicas: 10
```

That's it. No code changes. `kubectl apply -f k8s/` and K8s does the rest.

---

## 4. GitHub Actions — CI/CD Pipeline

### Repository structure for CI/CD:

```
.github/
  workflows/
    ci-identity-service.yml        # Runs on changes to services/identity-service/**
    ci-rate-inventory-service.yml  # Runs on changes to services/rate-inventory-service/**
    ci-reservation-service.yml
    ci-channel-engine.yml
    ci-notification-service.yml
    ci-admin-service.yml
    ci-web-app.yml                 # Runs on changes to web-app/**
    deploy-staging.yml             # Manual trigger or auto after CI
    deploy-production.yml          # Manual trigger with approval
```

### CI workflow for a service (reusable pattern):

```yaml
# .github/workflows/ci-identity-service.yml
name: CI — Identity Service

on:
  push:
    branches: [main, develop]
    paths:
      - 'services/identity-service/**'
      - 'shared/**'
  pull_request:
    paths:
      - 'services/identity-service/**'
      - 'shared/**'

env:
  SERVICE_NAME: identity-service
  SERVICE_DIR: services/identity-service
  AWS_REGION: ap-south-1
  ECR_REGISTRY: 123456789.dkr.ecr.ap-south-1.amazonaws.com

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports: [5432:5432]
        options: >-
          --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
      redis:
        image: redis:7-alpine
        ports: [6379:6379]

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        working-directory: ${{ env.SERVICE_DIR }}
        run: |
          pip install -e ".[dev]"
          pip install -e ../../shared

      - name: Lint
        working-directory: ${{ env.SERVICE_DIR }}
        run: ruff check . && ruff format --check .

      - name: Test
        working-directory: ${{ env.SERVICE_DIR }}
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET_KEY: test-secret-key
        run: pytest --cov=app --cov-report=xml -v

      - name: Check coverage
        working-directory: ${{ env.SERVICE_DIR }}
        run: |
          coverage report --fail-under=70

  build-and-push:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to ECR
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push
        id: meta
        working-directory: ${{ env.SERVICE_DIR }}
        run: |
          IMAGE_TAG="${{ env.ECR_REGISTRY }}/${{ env.SERVICE_NAME }}:${{ github.sha }}"
          docker build -t $IMAGE_TAG .
          docker push $IMAGE_TAG
          echo "tags=$IMAGE_TAG" >> $GITHUB_OUTPUT

  deploy-staging:
    needs: build-and-push
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Update kubeconfig
        run: aws eks update-kubeconfig --name abodeatab-cluster --region ${{ env.AWS_REGION }}

      - name: Deploy to staging
        run: |
          kubectl set image deployment/${{ env.SERVICE_NAME }} \
            ${{ env.SERVICE_NAME }}=${{ needs.build-and-push.outputs.image_tag }} \
            -n abodeatab-staging
          kubectl rollout status deployment/${{ env.SERVICE_NAME }} -n abodeatab-staging --timeout=300s
```

### Production deployment (manual approval):

```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  workflow_dispatch:
    inputs:
      service:
        description: 'Service to deploy'
        required: true
        type: choice
        options:
          - identity-service
          - rate-inventory-service
          - reservation-service
          - channel-engine
          - notification-service
          - admin-service
          - web-app
      image_tag:
        description: 'Image tag (commit SHA)'
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production          # Requires manual approval in GitHub settings

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-south-1

      - name: Update kubeconfig
        run: aws eks update-kubeconfig --name abodeatab-cluster --region ap-south-1

      - name: Deploy (rolling update)
        run: |
          IMAGE="${{ secrets.ECR_REGISTRY }}/${{ inputs.service }}:${{ inputs.image_tag }}"
          kubectl set image deployment/${{ inputs.service }} \
            ${{ inputs.service }}=$IMAGE \
            -n abodeatab-production
          kubectl rollout status deployment/${{ inputs.service }} \
            -n abodeatab-production --timeout=300s

      - name: Verify health
        run: |
          kubectl get pods -n abodeatab-production -l app=${{ inputs.service }}
          echo "Deployment successful"
```

---

## 5. Step-by-Step Setup Order

### Week 0 (before Sprint 1):

| Step | Action | Output |
|------|--------|--------|
| 1 | Create GitHub repo `abodeatab-platform` | Empty monorepo |
| 2 | Set up monorepo folder structure (see `02_MONOREPO_STRUCTURE.md`) | All folders + placeholder files |
| 3 | Create AWS account, set up IAM users for CI/CD | AWS credentials in GitHub Secrets |
| 4 | Create ECR repositories (one per service) | 7 ECR repos ready |
| 5 | Create EKS cluster (1 node, t3.xlarge) | Running K8s cluster |
| 6 | Create RDS PostgreSQL instance (db.t3.medium, Multi-AZ off for Phase 1) | Database endpoint |
| 7 | Create ElastiCache Redis instance (cache.t3.micro) | Redis endpoint |
| 8 | Install Kong Ingress Controller on EKS | API Gateway running |
| 9 | Create K8s namespace `abodeatab-staging` | Namespace ready |
| 10 | Set up GitHub Actions workflows | CI/CD ready |

### Sprint 1:
| Step | Action |
|------|--------|
| 11 | Build Identity Service (auth, users, RBAC, MFA) |
| 12 | Build Admin Service (tenant onboarding, config) |
| 13 | Write K8s manifests for both services |
| 14 | Deploy to staging via CI/CD |
| 15 | Build React web app shell (login, layout, routing) |
| 16 | Deploy web app to staging |

### Sprint 2:
| Step | Action |
|------|--------|
| 17 | Build Rate & Inventory Service |
| 18 | Build Reservation Service |
| 19 | Deploy both to staging |
| 20 | Build frontend: rooms, inventory calendar, reservations inbox |

### Sprint 3:
| Step | Action |
|------|--------|
| 21 | Set up Kafka (Amazon MSK or self-hosted) |
| 22 | Build Channel Engine + OTA adapters |
| 23 | Build Notification Service |
| 24 | Deploy all, wire up Kafka event flows |
| 25 | Build frontend: channels, notifications |

---

## 6. Local Development Workflow

```bash
# Clone and start everything
git clone git@github.com:abodeatab/abodeatab-platform.git
cd abodeatab-platform

# Start all infrastructure + services
docker-compose up -d

# Check status
docker-compose ps

# View logs for one service
docker-compose logs -f identity-service

# Run tests for one service
cd services/identity-service
pip install -e ".[dev]"
pytest -v

# Run migrations for one service
cd services/identity-service
alembic upgrade head

# Access the API
curl http://localhost:8000/api/v1/auth/login  # Via Kong gateway
curl http://localhost:8001/api/v1/auth/login   # Direct to service

# Access the web app
open http://localhost:3000
```

---

## 7. Production Deployment Strategy

### Blue-green rolling update (default):
K8s performs a rolling update automatically when you change the image tag:
1. K8s creates new pod with new image
2. New pod passes health check (readinessProbe)
3. K8s shifts traffic to new pod
4. K8s terminates old pod
5. If new pod fails health check, K8s stops the rollout and keeps old pods

### Rollback:
```bash
# If something goes wrong
kubectl rollout undo deployment/identity-service -n abodeatab-production

# Check rollout history
kubectl rollout history deployment/identity-service -n abodeatab-production
```

### Database migrations in production:
- Migrations run as a K8s Job BEFORE the new pods start
- The Job runs `alembic upgrade head` against the service's schema
- If migration fails, the deployment is aborted
- Always write backwards-compatible migrations (don't drop columns that old code still reads)

### Monitoring checklist:
- CloudWatch alarms on: pod restart count, CPU > 80%, memory > 80%, 5xx error rate > 1%
- OpenTelemetry traces: every request gets a trace ID that flows across all services
- Structured logs: every service logs JSON to CloudWatch Logs, searchable by trace ID
- PagerDuty/OpsGenie integration for critical alerts (channel failures, service down)
