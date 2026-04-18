---
title: Local Kubernetes validation
description: Deploy KIRA on minikube with the bundled overlay, or dry-run manifests without a cluster — full walkthrough and limits.
sidebar_position: 4
---

# Local Kubernetes validation

KIRA's **daily dev** is **Docker Compose** (`docker/docker-compose.yml`). The **`k8s/`** tree is for **real clusters** (staging/production on **EKS**).

For testing the **Kubernetes deployment path** without AWS, use the **minikube overlay** (`k8s/overlays/minikube/`). It bundles in-cluster Postgres, Redis, and Kafka so the full KIRA stack boots on a single-node cluster.

---

## Quick reference

| Tier | What | Tools needed |
|------|------|-------------|
| **Tier 1** — Cluster health | Confirm `kubectl` works, nodes are ready | minikube / kind / k3d |
| **Tier 2** — Dry-run manifests | Validate YAML without side effects | `kubectl --dry-run=client` |
| **Tier 3** — Full minikube deploy | Run all KIRA services on a local cluster | minikube, Docker, `kubectl` |

---

## Tier 1 — Is your dev cluster healthy?

Use any **local** control plane: **[minikube](https://minikube.sigs.k8s.io/)**, **[kind](https://kind.sigs.k8s.io/)**, **Docker Desktop Kubernetes**, or **k3d**. Install `kubectl`, point it at the cluster, then:

```bash
kubectl config current-context
kubectl cluster-info
kubectl get nodes
kubectl get --raw='/readyz?verbose'
```

If these succeed, your **cluster** is fine. That does **not** mean KIRA's full stack is deployable — that requires images, secrets, and infrastructure.

---

## Tier 2 — Validate manifests without applying

Use **client-side dry-run** on individual files (safe, no cluster changes):

```bash
kubectl apply --dry-run=client -f k8s/base/namespace.yaml
kubectl apply --dry-run=client -f k8s/base/configmap.yaml
```

Preview the full rendered YAML for any overlay:

```bash
kubectl kustomize k8s/overlays/minikube/
kubectl kustomize k8s/overlays/staging/
```

:::note
Staging/production overlays embed **`${ECR_REGISTRY}`** in `images:` entries. Plain `kubectl kustomize` does not expand shell variables; CI uses env substitution or `kubectl set image` after apply.
:::

---

## Tier 3 — Full minikube deployment

The **minikube overlay** (`k8s/overlays/minikube/`) includes everything needed to run KIRA on a local cluster:

| Component | What it provides |
|-----------|-----------------|
| `infra/postgres.yaml` | Single-replica StatefulSet with PVC, init script that creates all 6 service databases |
| `infra/redis.yaml` | Single-replica Deployment + ClusterIP Service |
| `infra/kafka.yaml` | Single-broker KRaft Deployment (same `confluentinc/cp-kafka:7.6.0` as local dev) |
| `secrets.yaml` | Dev-only secrets matching `secrets-template.yaml` (DATABASE_URLs point at in-cluster Postgres) |
| `configmap-patch.yaml` | Overrides `kira-config` for minikube: `ENVIRONMENT=minikube`, `LOG_LEVEL=DEBUG`, local CORS |
| `kustomization.yaml` | Ties it all together: namespace `kira-minikube`, local image tags, `imagePullPolicy: Never`, single replica, HPAs disabled |

### Prerequisites

- **[minikube](https://minikube.sigs.k8s.io/docs/start/)** installed and running
- **Docker** (minikube's default driver)
- **kubectl** configured to talk to minikube (`minikube start` does this automatically)

### Step 1 — Start minikube

```bash
# 4 CPUs and 8 GB RAM recommended for the full stack
minikube start --cpus=4 --memory=8192
```

### Step 2 — Build and load images

Build each service image and load it into minikube's image cache. The overlay tags everything as `:local` with `imagePullPolicy: Never`, so images must exist inside minikube.

```bash
# Point your shell at minikube's Docker daemon
eval $(minikube docker-env)

# Build all service images (adjust paths if your Dockerfiles differ)
SERVICES=(admin-service identity-service rate-inventory-service reservation-service channel-engine notification-service)
for svc in "${SERVICES[@]}"; do
  docker build -t "kira-${svc}:local" -f "docker/${svc}.Dockerfile" .
done

# Build web-app
docker build -t kira-web-app:local -f docker/web-app.Dockerfile .
```

Alternatively, build outside minikube and load:

```bash
for svc in "${SERVICES[@]}"; do
  docker build -t "kira-${svc}:local" -f "docker/${svc}.Dockerfile" .
  minikube image load "kira-${svc}:local"
done
docker build -t kira-web-app:local -f docker/web-app.Dockerfile .
minikube image load kira-web-app:local
```

### Step 3 — Apply the overlay

```bash
kubectl apply -k k8s/overlays/minikube/
```

This creates:
- Namespace `kira-minikube`
- In-cluster Postgres (StatefulSet), Redis, Kafka
- All 6 backend services + web-app + channel-engine worker
- ConfigMap, Secrets, HPAs (pinned to 1 replica)

### Step 4 — Wait for pods

```bash
kubectl -n kira-minikube get pods -w
```

Postgres may take 30-60 seconds to initialise. Services will restart a few times if they connect before Postgres/Redis/Kafka are ready (readiness probes handle this).

### Step 5 — Access the app

Port-forward the web-app and any API service you want to reach:

```bash
# Web UI
kubectl -n kira-minikube port-forward svc/web-app 3000:3000 &

# Identity service API (example)
kubectl -n kira-minikube port-forward svc/identity-service 8001:8001 &
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Step 6 — Run migrations

Services expect their databases to have the schema applied. Exec into any running pod to run Alembic:

```bash
for svc in "${SERVICES[@]}"; do
  kubectl -n kira-minikube exec deploy/$svc -- python -m alembic upgrade head
done
```

### Tear down

```bash
kubectl delete namespace kira-minikube
# or
minikube delete
```

---

## What minikube **can** test

- Full Kubernetes deployment: Pods, Services, readiness/liveness probes
- Service-to-service networking via K8s DNS
- Secret wiring and ConfigMap overrides
- Image loading and `imagePullPolicy` behavior
- `kubectl` workflows: logs, exec, port-forward, rollout
- Kustomize overlay structure and patches

## What minikube **cannot** replicate

- **RDS Multi-AZ** — minikube Postgres is a single pod with no replication
- **ElastiCache clustering** — single Redis pod, no failover
- **MSK durability** — single Kafka broker, no partition replication
- **HPAs** — minikube has no metrics-server by default (install the addon if needed)
- **Real TLS / DNS** — no Route 53, ACM, or Ingress controller configured
- **IAM / IRSA** — no AWS identity integration
- **Production-grade storage** — PVCs use minikube's hostpath provisioner

---

## Recommended workflow

1. **Daily dev:** Compose — [Local Docker](./local-docker.md).
2. **Test K8s deployment:** minikube overlay (this page).
3. **First real deploy:** Follow [AWS production](./aws-production.md) and [Kubernetes](./kubernetes.md); use staging before production.

---

## Related

- [How deployment fits together](./how-deployment-fits.md) — Compose vs EKS mental model.
- [Deployment overview](./overview.md) — Compose vs EKS roles.
- [Runbooks](../operations/runbooks.md) — `kubectl` troubleshooting once workloads are running.
