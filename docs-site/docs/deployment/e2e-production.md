---
title: End-to-End Production Deployment
description: Complete checklist from zero AWS infrastructure to a running KIRA production cluster.
sidebar_position: 0
---

# End-to-End Production Deployment

A single-page checklist covering **every step** from an empty AWS account to a production-ready KIRA deployment. Each section links to the detailed guide.

---

## Phase 1 — AWS Account & Prerequisites

| Step                                       | Command / Action                                                                               | Docs                                                      |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| Install AWS CLI, Terraform, kubectl, Helm  | `brew install awscli terraform kubectl helm`                                                   | [Prerequisites](./aws-production.md#prerequisites)        |
| Configure AWS CLI                          | `aws configure` (region: `ap-south-1`)                                                         | —                                                         |
| Create CI/CD IAM user                      | `aws iam create-user --user-name kira-cicd`                                                    | [IAM Setup](./aws-production.md#step-1-aws-account-setup) |
| Store secrets in GitHub Actions            | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `ECR_REGISTRY`, `EKS_CLUSTER_NAME` | —                                                         |
| Create Terraform state bucket + lock table | See [Backend Setup](./aws-production.md#terraform-backend-setup-one-time)                      | —                                                         |

---

## Phase 2 — Provision Infrastructure

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values (account ID, domain, region)

terraform init
terraform plan -out=plan.tfplan
terraform apply plan.tfplan
```

**Resources created:** VPC (2 AZs), EKS cluster (1–3 t3.xlarge), RDS PostgreSQL 16, ElastiCache Redis, ECR repos (7), S3 buckets, Secrets Manager entries, WAF rules.

Save the Terraform outputs:

```bash
terraform output -json > /tmp/kira-infra.json
```

Key outputs needed for next steps:

- `eks_cluster_name` — for kubeconfig
- `rds_endpoint` — database hostname
- `redis_endpoint` — cache hostname
- `ecr_registry` — image push target

---

## Phase 3 — Configure Kubernetes

### Connect to EKS

```bash
aws eks update-kubeconfig --name kira-production --region ap-south-1
kubectl get nodes    # Should show 2 ready nodes
```

### Install Kong Ingress Controller

```bash
helm repo add kong https://charts.konghq.com && helm repo update
helm install kong kong/kong -n kong-system --create-namespace \
  --set proxy.type=LoadBalancer \
  --set ingressController.installCRDs=false
```

### Apply Kubernetes manifests

```bash
# Create namespace and configmaps
kubectl apply -k k8s/base/

# Apply production overlay (image tags, replicas, resource limits)
kubectl apply -k k8s/overlays/production/
```

### Create Kubernetes secrets

```bash
# Pull from AWS Secrets Manager and create K8s secrets
for svc in identity-service rate-inventory-service reservation-service \
           channel-engine notification-service admin-service; do
  SECRET_JSON=$(aws secretsmanager get-secret-value \
    --secret-id "kira/production/$svc" \
    --query SecretString --output text)
  kubectl create secret generic "$svc-secrets" \
    --from-literal=secrets="$SECRET_JSON" \
    -n kira --dry-run=client -o yaml | kubectl apply -f -
done
```

---

## Phase 4 — Build & Push Images

First push is manual; subsequent ones go through CI/CD.

```bash
# Login to ECR
aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-south-1.amazonaws.com

# Build and push each service
for svc in identity-service rate-inventory-service reservation-service \
           channel-engine notification-service admin-service; do
  docker build -f docker/$svc.Dockerfile \
    -t <account-id>.dkr.ecr.ap-south-1.amazonaws.com/kira/$svc:latest \
    services/$svc/
  docker push <account-id>.dkr.ecr.ap-south-1.amazonaws.com/kira/$svc:latest
done

# Admin service (needs repo root context)
docker build -f docker/admin-service.Dockerfile \
  -t <account-id>.dkr.ecr.ap-south-1.amazonaws.com/kira/admin-service:latest .
docker push <account-id>.dkr.ecr.ap-south-1.amazonaws.com/kira/admin-service:latest

# Web app
docker build -f docker/web-app.Dockerfile \
  --build-arg VITE_API_BASE_URL=https://api.yourdomain.com \
  -t <account-id>.dkr.ecr.ap-south-1.amazonaws.com/kira/web-app:latest \
  web-app/
docker push <account-id>.dkr.ecr.ap-south-1.amazonaws.com/kira/web-app:latest
```

---

## Phase 5 — Database Setup

### Run migrations

```bash
# Port-forward to RDS through a bastion or use kubectl exec
kubectl run migration-runner --rm -it \
  --image=python:3.13-slim \
  --env="DATABASE_URL=postgresql+asyncpg://kira_admin:<password>@<rds-endpoint>:5432/kira" \
  -n kira -- bash

# Inside the pod:
pip install alembic asyncpg sqlalchemy
# Copy migration files and run alembic upgrade head for each service
```

Or connect via `kubectl port-forward` to service pods that have Alembic:

```bash
for svc in identity-service rate-inventory-service reservation-service \
           channel-engine notification-service admin-service; do
  kubectl exec -n kira deploy/$svc -- python -m alembic upgrade head
done
```

### Create super-admin

```bash
kubectl exec -n kira deploy/identity-service -- python -c "
from app.auth import create_superadmin
import asyncio
asyncio.run(create_superadmin('admin@yourdomain.com', 'YourSecurePassword123!'))
"
```

---

## Phase 6 — DNS & SSL

### Route 53

```bash
# Get Kong LB hostname
KONG_LB=$(kubectl get svc -n kong-system kong-kong-proxy \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Create DNS records (in Route 53 or your DNS provider)
# api.yourdomain.com  → CNAME → $KONG_LB
# app.yourdomain.com  → CNAME → $KONG_LB (or CloudFront)
```

### ACM Certificate

```bash
aws acm request-certificate \
  --domain-name "*.yourdomain.com" \
  --validation-method DNS \
  --region ap-south-1
# Complete DNS validation, then attach to Kong LB
```

See [SSL & Domains](./ssl-and-domains.md) for full details.

---

## Phase 7 — CI/CD Pipeline

After the initial manual deploy, GitHub Actions handles everything automatically:

1. **Push to `main`** → CI runs tests → builds image → pushes to ECR → deploys to staging
2. **Manual approval** → promotes staging image to production

Each service has its own workflow (`.github/workflows/ci-<service>.yml`). Re-enable automatic triggers:

```yaml
# Uncomment in each CI workflow:
on:
  push:
    branches: [main]
    paths:
      - "services/<service>/**"
  pull_request:
    paths:
      - "services/<service>/**"
```

See [CI/CD Pipeline](./cicd-pipeline.md) for full details.

---

## Phase 8 — Monitoring & Alerting

Deploy observability to EKS:

```bash
# Prometheus + Grafana via Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install kube-prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace

# Import KIRA dashboards from observability/grafana/dashboards/
```

Set up CloudWatch alarms for:

- RDS CPU > 80%, storage < 20%
- EKS node count at max
- ElastiCache evictions > 0
- 5xx error rate > 1%

See [Monitoring](../operations/monitoring.md) and [Alerting](../operations/alerting.md).

---

## Production Checklist

| Category           | Item                                          | Status |
| ------------------ | --------------------------------------------- | ------ |
| **Infrastructure** | VPC with private subnets                      | ☐      |
|                    | EKS cluster running                           | ☐      |
|                    | RDS PostgreSQL (Multi-AZ)                     | ☐      |
|                    | ElastiCache Redis (encrypted)                 | ☐      |
|                    | ECR repos created (image scanning on)         | ☐      |
|                    | WAF rules applied                             | ☐      |
| **Security**       | Non-root containers                           | ☐      |
|                    | Secrets in AWS Secrets Manager (not env vars) | ☐      |
|                    | TLS everywhere (ACM + Kong)                   | ☐      |
|                    | CORS restricted to your domain                | ☐      |
|                    | Redis AUTH enabled                            | ☐      |
|                    | Network policies applied                      | ☐      |
| **Data**           | Migrations applied                            | ☐      |
|                    | Super-admin created                           | ☐      |
|                    | RDS automated backups enabled                 | ☐      |
|                    | S3 versioning for Terraform state             | ☐      |
| **Monitoring**     | Prometheus scraping all services              | ☐      |
|                    | Grafana dashboards imported                   | ☐      |
|                    | CloudWatch alarms configured                  | ☐      |
|                    | Log aggregation (Loki / CloudWatch Logs)      | ☐      |
| **CI/CD**          | GitHub secrets configured                     | ☐      |
|                    | CI workflows enabled for push/PR              | ☐      |
|                    | Staging environment tested                    | ☐      |
|                    | Production deploy verified                    | ☐      |
| **DNS**            | API domain → Kong LB                          | ☐      |
|                    | Web domain → CloudFront / LB                  | ☐      |
|                    | SSL certificate issued + validated            | ☐      |

---

## Estimated AWS Costs (Phase 1)

| Resource       | Spec                   | Monthly Cost (ap-south-1) |
| -------------- | ---------------------- | ------------------------- |
| EKS cluster    | Control plane          | ~$73                      |
| EC2 nodes      | 2× t3.xlarge           | ~$240                     |
| RDS PostgreSQL | db.t3.medium, Multi-AZ | ~$120                     |
| ElastiCache    | cache.t3.micro         | ~$13                      |
| NAT Gateway    | Single                 | ~$32                      |
| ECR            | 7 repos, ~2 GB         | ~$1                       |
| S3             | Backups + state        | ~$1                       |
| ALB (via Kong) | Load balancer          | ~$25                      |
| **Total**      |                        | **~$505/month**           |

:::tip Cost reduction

- Use Spot Instances for non-production nodes (save ~60%)
- Use single-AZ RDS for staging (~$60 vs $120)
- Skip MSK and run Kafka on EKS for Phase 1
  :::
