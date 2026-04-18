---
title: AWS Production Deployment
description: Step-by-step guide to deploying KIRA on AWS — from zero to a running production cluster with EKS, RDS, ElastiCache, MSK, Kong, and CI/CD.
sidebar_position: 2
---

# AWS Production Deployment

**What you'll learn:**
- How to provision the full AWS infrastructure with Terraform
- How to configure EKS, install Kong, and deploy all services
- How to set up DNS, SSL, and CI/CD automation
- A production readiness checklist and cost estimate

---

## Prerequisites

Before starting, install and configure:

| Tool | Version | Install |
|---|---|---|
| AWS CLI | v2 | `brew install awscli` or [aws.amazon.com/cli](https://aws.amazon.com/cli/) |
| Terraform | v1.5+ | `brew install terraform` or [terraform.io](https://terraform.io) |
| kubectl | v1.29+ | `brew install kubectl` |
| Helm | v3.14+ | `brew install helm` |

Configure the AWS CLI with your credentials:

```bash
aws configure
# AWS Access Key ID: <your key>
# AWS Secret Access Key: <your secret>
# Default region name: ap-south-1
# Default output format: json
```

---

## Step 1: AWS Account Setup

### Create IAM user for CI/CD

Create a dedicated IAM user for GitHub Actions — never use root credentials or your personal admin credentials in CI.

```bash
# Create user
aws iam create-user --user-name kira-cicd

# Create access keys (save these — shown only once)
aws iam create-access-key --user-name kira-cicd
```

### Attach IAM policies

The CI/CD user needs permissions to push to ECR and deploy to EKS. Create a custom policy in `infra/iam/cicd-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECRFullAccess",
      "Effect": "Allow",
      "Action": ["ecr:*"],
      "Resource": "*"
    },
    {
      "Sid": "EKSDeployAccess",
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters",
        "eks:AccessKubernetesApi"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SecretsManagerRead",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:ap-south-1:*:secret:kira/*"
    }
  ]
}
```

```bash
aws iam create-policy \
  --policy-name KiraCICDPolicy \
  --policy-document file://infra/iam/cicd-policy.json

aws iam attach-user-policy \
  --user-name kira-cicd \
  --policy-arn arn:aws:iam::<account-id>:policy/KiraCICDPolicy
```

Your personal AWS user needs broader permissions to run Terraform: EKS, ECR, RDS, ElastiCache, MSK, VPC, IAM, S3, Secrets Manager, Route 53, ACM, CloudWatch.

### Store credentials in GitHub

In your GitHub repository: **Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | Access key ID for `kira-cicd` |
| `AWS_SECRET_ACCESS_KEY` | Secret access key for `kira-cicd` |
| `AWS_REGION` | `ap-south-1` |
| `ECR_REGISTRY` | `<account-id>.dkr.ecr.ap-south-1.amazonaws.com` |
| `EKS_CLUSTER_NAME` | `kira-production` (set after Terraform apply) |

---

## Step 2: Infrastructure Provisioning with Terraform

### Infra folder structure

```
infra/
├── terraform/
│   ├── main.tf              # provider config, backend
│   ├── variables.tf         # input variables
│   ├── outputs.tf           # EKS endpoint, RDS hostname, etc.
│   ├── terraform.tfvars     # your values (gitignored)
│   ├── terraform.tfvars.example
│   ├── vpc.tf               # VPC, subnets, NAT gateway
│   ├── eks.tf               # EKS cluster + node group
│   ├── rds.tf               # PostgreSQL RDS
│   ├── elasticache.tf       # Redis
│   ├── msk.tf               # Kafka (or skip for Phase 1)
│   ├── ecr.tf               # container registries
│   ├── s3.tf                # static assets + backups
│   └── secrets.tf           # Secrets Manager entries
└── iam/
    └── cicd-policy.json
```

### Terraform backend setup (one-time)

Create the S3 bucket and DynamoDB table for Terraform state **before** running `terraform init`. Do this manually once:

```bash
# State bucket
aws s3api create-bucket \
  --bucket kira-terraform-state-<account-id> \
  --region ap-south-1 \
  --create-bucket-configuration LocationConstraint=ap-south-1

aws s3api put-bucket-versioning \
  --bucket kira-terraform-state-<account-id> \
  --versioning-configuration Status=Enabled

# Lock table
aws dynamodb create-table \
  --table-name kira-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-south-1
```

Configure `main.tf` to use this backend:

```hcl
terraform {
  required_version = ">= 1.5"

  backend "s3" {
    bucket         = "kira-terraform-state-<account-id>"
    key            = "production/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "kira-terraform-locks"
    encrypt        = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Project     = "kira"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
```

### Key resource configurations

**VPC** — 2 public + 2 private subnets across 2 AZs, single NAT gateway:

```hcl
# vpc.tf
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "kira-${var.environment}"
  cidr = "10.0.0.0/16"

  azs             = ["ap-south-1a", "ap-south-1b"]
  public_subnets  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets = ["10.0.11.0/24", "10.0.12.0/24"]

  enable_nat_gateway     = true
  single_nat_gateway     = true    # Phase 1: one NAT = ~$32/mo; HA NAT = ~$64/mo
  enable_dns_hostnames   = true
  enable_dns_support     = true

  # Required tags for EKS to discover subnets
  public_subnet_tags  = { "kubernetes.io/role/elb" = "1" }
  private_subnet_tags = { "kubernetes.io/role/internal-elb" = "1" }
}
```

**EKS cluster** — managed node group, 1–3 t3.xlarge nodes, Cluster Autoscaler compatible:

```hcl
# eks.tf
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "kira-${var.environment}"
  cluster_version = "1.29"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access = true

  eks_managed_node_groups = {
    kira = {
      instance_types = ["t3.xlarge"]
      min_size       = 1
      max_size       = 3
      desired_size   = 2

      # Required for Cluster Autoscaler
      labels = { role = "worker" }
      taints = []
    }
  }
}
```

**RDS PostgreSQL 16** — db.t3.medium, Multi-AZ in production, 7-day backup retention:

```hcl
# rds.tf
resource "aws_db_instance" "kira" {
  identifier        = "kira-${var.environment}"
  engine            = "postgres"
  engine_version    = "16.2"
  instance_class    = "db.t3.medium"
  allocated_storage = 50
  storage_encrypted = true

  db_name  = "kira"
  username = "kira_admin"
  password = random_password.db_password.result

  multi_az               = var.environment == "production"
  backup_retention_period = 7
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:04:00-sun:05:00"
  deletion_protection     = var.environment == "production"
  skip_final_snapshot     = var.environment != "production"

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.kira.name
}
```

**ElastiCache Redis** — cache.t3.micro for Phase 1, cluster mode off:

```hcl
# elasticache.tf
resource "aws_elasticache_replication_group" "kira" {
  replication_group_id = "kira-${var.environment}"
  description          = "KIRA Redis cluster"

  node_type            = "cache.t3.micro"
  num_cache_clusters   = 1      # Phase 1: single node; Phase 2: add replica
  engine_version       = "7.1"
  port                 = 6379

  subnet_group_name  = aws_elasticache_subnet_group.kira.name
  security_group_ids = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}
```

**Amazon MSK (Kafka)** — 2 brokers, kafka.t3.small:

```hcl
# msk.tf — skip this for Phase 1 cost reduction; run Kafka on EKS instead
resource "aws_msk_cluster" "kira" {
  cluster_name           = "kira-${var.environment}"
  kafka_version          = "3.6.0"
  number_of_broker_nodes = 2

  broker_node_group_info {
    instance_type   = "kafka.t3.small"
    client_subnets  = module.vpc.private_subnets
    security_groups = [aws_security_group.msk.id]

    storage_info {
      ebs_storage_info { volume_size = 50 }
    }
  }

  encryption_info {
    encryption_in_transit { client_broker = "TLS" }
  }
}
```

:::tip Phase 1 cost reduction: skip MSK
At ~$150/month, MSK is a significant cost for early-stage deployments. For Phase 1, run Kafka as a pod on EKS using the same `confluentinc/cp-kafka:7.6.0` image from local dev (single broker, ephemeral storage). Replace with MSK when you need durability guarantees or when the ops burden grows.
:::

**ECR** — one repository per service:

```hcl
# ecr.tf
locals {
  services = [
    "identity-service", "rate-inventory-service", "reservation-service",
    "channel-engine", "notification-service", "admin-service", "web-app"
  ]
}

resource "aws_ecr_repository" "services" {
  for_each = toset(local.services)
  name     = "kira/${each.key}"

  image_scanning_configuration { scan_on_push = true }
}

resource "aws_ecr_lifecycle_policy" "cleanup" {
  for_each   = aws_ecr_repository.services
  repository = each.value.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 20 images"
      selection = {
        tagStatus     = "tagged"
        tagPrefixList = ["sha-"]
        countType     = "imageCountMoreThan"
        countNumber   = 20
      }
      action = { type = "expire" }
    }]
  })
}
```

**Secrets Manager** — store all sensitive values:

```hcl
# secrets.tf
resource "aws_secretsmanager_secret" "identity_service" {
  name = "kira/${var.environment}/identity-service"
}

resource "aws_secretsmanager_secret_version" "identity_service" {
  secret_id = aws_secretsmanager_secret.identity_service.id
  secret_string = jsonencode({
    DATABASE_URL  = "postgresql+asyncpg://kira_admin:${random_password.db_password.result}@${aws_db_instance.kira.address}:5432/kira"
    SECRET_KEY    = random_password.app_secret.result
    JWT_SECRET_KEY = random_password.jwt_secret.result
  })
}
# Repeat for each service with its specific secrets
```

### Apply Terraform

```bash
cd infra/terraform

# Copy and fill in your values
cp terraform.tfvars.example terraform.tfvars

# Initialise — downloads providers, configures S3 backend
terraform init

# Preview — read every line before applying
terraform plan

# Apply — this takes 20–30 minutes
terraform apply
```

:::warning Terraform apply is slow the first time
EKS (10–15 min), RDS (8–10 min), and MSK (15–20 min) take the longest. Do not interrupt the apply. If it fails partway, run `terraform apply` again — Terraform is idempotent.
:::

After apply, save the outputs — you'll need them in subsequent steps:

```bash
terraform output
# eks_cluster_endpoint = "https://..."
# rds_hostname = "kira-production.xxxxx.ap-south-1.rds.amazonaws.com"
# redis_primary_endpoint = "kira-production.xxxxx.cache.amazonaws.com"
# ecr_registry = "123456789.dkr.ecr.ap-south-1.amazonaws.com"
```

### Cost estimate

| Resource | Spec | Monthly (USD) |
|---|---|---|
| EKS control plane | Managed | $73 |
| EC2 worker nodes | 2× t3.xlarge | $240 |
| RDS PostgreSQL 16 | db.t3.medium, Multi-AZ | $100 |
| ElastiCache Redis | cache.t3.micro | $15 |
| MSK Kafka | 2× kafka.t3.small | $150 |
| ECR | ~5 GB images | $2 |
| S3 + Route 53 | minimal | $6 |
| NAT Gateway | 1 | $32 |
| ALB (via Kong) | 1 | $25 |
| **Total (Phase 1 full)** | | **~$643/mo** |

**Phase 1 minimum (cut costs early):** 1 EKS node ($120 instead of $240), Kafka on EKS ($0 instead of $150), no RDS Multi-AZ ($50 instead of $100) → **~$320/mo**.

---

## Step 3: ECR Setup

### Authenticate Docker to ECR

```bash
aws ecr get-login-password --region ap-south-1 \
  | docker login --username AWS --password-stdin \
    123456789.dkr.ecr.ap-south-1.amazonaws.com
```

### Build and push images (first time)

CI/CD handles this automatically after setup, but the first push must be done manually:

```bash
ECR="123456789.dkr.ecr.ap-south-1.amazonaws.com"
TAG=$(git rev-parse --short HEAD)

# Build and push each service
for SERVICE in identity-service rate-inventory-service reservation-service \
               channel-engine notification-service admin-service; do
  docker build \
    -f services/$SERVICE/Dockerfile \
    -t $ECR/kira/$SERVICE:$TAG \
    -t $ECR/kira/$SERVICE:latest \
    .
  docker push $ECR/kira/$SERVICE:$TAG
  docker push $ECR/kira/$SERVICE:latest
done
```

:::note Build context is the repo root
Each Dockerfile copies from `shared/`, so the build context must be `.` (the repo root), not the service directory. This matches the `docker/docker-compose.yml` pattern (paths are written relative to the `docker/` compose file location).
:::

---

## Step 4: EKS Cluster Configuration

### Configure kubectl

```bash
aws eks update-kubeconfig \
  --name kira-production \
  --region ap-south-1

# Verify
kubectl get nodes
# NAME                                       STATUS   ROLES    AGE
# ip-10-0-11-xxx.ap-south-1.compute.internal   Ready    <none>   5m
```

### Install metrics-server (required for HPA)

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verify
kubectl top nodes
```

### Install Kong Ingress Controller

```bash
helm repo add kong https://charts.konghq.com
helm repo update

helm install kong kong/ingress \
  --namespace kong \
  --create-namespace \
  --set controller.ingressClass=kong \
  --set proxy.type=LoadBalancer

# Get the ALB hostname (takes ~2 minutes to provision)
kubectl get svc -n kong kong-kong-proxy
# EXTERNAL-IP: xxxxxx.ap-south-1.elb.amazonaws.com
```

Save that `EXTERNAL-IP` — you'll point Route 53 at it in Step 7.

### Install Cluster Autoscaler

```bash
helm repo add autoscaler https://kubernetes.github.io/autoscaler

helm install cluster-autoscaler autoscaler/cluster-autoscaler \
  --namespace kube-system \
  --set autoDiscovery.clusterName=kira-production \
  --set awsRegion=ap-south-1 \
  --set rbac.serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=arn:aws:iam::<account-id>:role/ClusterAutoscalerRole
```

The IAM role for Cluster Autoscaler needs `autoscaling:DescribeAutoScalingGroups`, `autoscaling:SetDesiredCapacity`, and related permissions. Add this role to your Terraform config.

### Create namespaces

```bash
kubectl apply -f k8s/base/namespace.yaml
# Creates: kira (production) and kira-staging namespaces
```

### Create ConfigMaps

Edit `k8s/base/configmap.yaml` with production values (RDS hostname, Redis endpoint, MSK bootstrap servers), then:

```bash
kubectl apply -f k8s/base/configmap.yaml -n kira
kubectl apply -f k8s/base/configmap.yaml -n kira-staging
```

### Create secrets for each service

Pull values from AWS Secrets Manager and create K8s secrets:

```bash
ECR="123456789.dkr.ecr.ap-south-1.amazonaws.com"

# Helper function
create_secret() {
  local SERVICE=$1
  local NAMESPACE=$2
  local SECRET_JSON=$(aws secretsmanager get-secret-value \
    --secret-id "kira/production/$SERVICE" \
    --query SecretString --output text)

  kubectl create secret generic kira-${SERVICE}-secret \
    --from-literal=DATABASE_URL=$(echo $SECRET_JSON | jq -r .DATABASE_URL) \
    --from-literal=SECRET_KEY=$(echo $SECRET_JSON | jq -r .SECRET_KEY) \
    --from-literal=JWT_SECRET_KEY=$(echo $SECRET_JSON | jq -r .JWT_SECRET_KEY) \
    -n $NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -
}

for SVC in identity-service rate-inventory-service reservation-service \
            channel-engine notification-service admin-service; do
  create_secret $SVC kira
  create_secret $SVC kira-staging
done
```

:::danger Never commit secrets to Git
Use `kubectl create secret` commands or Sealed Secrets / External Secrets Operator. The `k8s/base/secrets-template.yaml` documents the required keys but contains no real values.
:::

---

## Step 5: Database Setup

### Verify RDS connectivity

Before running migrations, verify your EKS pods can reach RDS. The RDS security group must allow inbound port 5432 from the EKS node security group.

```bash
# Run a test pod in the cluster
kubectl run pg-test \
  --image=postgres:16-alpine \
  --restart=Never \
  --rm -it \
  -n kira \
  -- psql "postgresql://kira_admin:<password>@<rds-hostname>:5432/kira" -c "\l"
```

### Run database migrations via K8s Job

Run migrations for each service before deploying the service pods:

```yaml
# k8s/jobs/migrate-identity.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: migrate-identity
  namespace: kira
spec:
  template:
    spec:
      containers:
        - name: migrate
          image: 123456789.dkr.ecr.ap-south-1.amazonaws.com/kira/identity-service:<tag>
          command: ["uv", "run", "alembic", "upgrade", "head"]
          envFrom:
            - secretRef:
                name: kira-identity-service-secret
            - configMapRef:
                name: kira-config
      restartPolicy: Never
  backoffLimit: 3
```

```bash
# Apply and wait for completion
for SERVICE in identity-service rate-inventory-service reservation-service \
               channel-engine notification-service admin-service; do
  # Update the image tag in the job manifest, then:
  kubectl apply -f k8s/jobs/migrate-${SERVICE}.yaml
  kubectl wait --for=condition=complete job/migrate-${SERVICE} -n kira --timeout=120s
  echo "✓ ${SERVICE} migrated"
done
```

### Create super admin and first tenant

After migrations, seed the initial data:

```bash
kubectl run seed-admin \
  --image=123456789.dkr.ecr.ap-south-1.amazonaws.com/kira/identity-service:<tag> \
  --restart=Never \
  --rm -it \
  -n kira \
  --env-from=secret/kira-identity-service-secret \
  -- python -m app.scripts.seed_super_admin \
     --email admin@kira.abodeab.com \
     --password "$(openssl rand -base64 24)"
```

Then create the first tenant via the admin API:

```bash
# Port-forward admin-service (after it's deployed)
kubectl port-forward svc/admin-service 8006:8006 -n kira &

curl -X POST http://localhost:8006/api/v1/tenants \
  -H "Authorization: Bearer <super-admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Grand Hotel", "subdomain": "grand-hotel", "contact_email": "owner@grandhotel.com"}'
```

---

## Step 6: Deploy Services

### Apply Kustomize production overlay

```bash
# Update ECR registry in kustomization.yaml first
# Edit k8s/overlays/production/kustomization.yaml:
#   images: newName: 123456789.dkr.ecr.ap-south-1.amazonaws.com/kira/<service>

kubectl apply -k k8s/overlays/production/
```

### Verify all pods are running

```bash
kubectl get pods -n kira

# Expected after ~3 minutes:
# NAME                                       READY   STATUS    RESTARTS   AGE
# identity-service-6d8b9f-xxxxx              1/1     Running   0          2m
# identity-service-6d8b9f-yyyyy              1/1     Running   0          2m
# rate-inventory-service-7c9d4f-xxxxx        1/1     Running   0          2m
# ...
```

### Verify health endpoints

```bash
# Test each service health endpoint
for SERVICE_PORT in "identity-service:8001" "rate-inventory-service:8002" \
                    "reservation-service:8003" "channel-engine:8004" \
                    "notification-service:8005" "admin-service:8006"; do
  SERVICE=$(echo $SERVICE_PORT | cut -d: -f1)
  PORT=$(echo $SERVICE_PORT | cut -d: -f2)
  kubectl port-forward svc/$SERVICE $PORT:$PORT -n kira &
  sleep 2
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/health)
  echo "$SERVICE: $STATUS"
  kill %1
done
```

### Verify Kong routing

```bash
# Get the Kong proxy IP
KONG_IP=$(kubectl get svc kong-kong-proxy -n kong -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test routing through Kong
curl -H "Host: api.kira.abodeab.com" http://$KONG_IP/api/v1/health
```

---

## Step 7: DNS and SSL

### Request SSL certificate in ACM

```bash
aws acm request-certificate \
  --domain-name kira.abodeab.com \
  --subject-alternative-names "*.kira.abodeab.com" \
  --validation-method DNS \
  --region ap-south-1
```

Get the DNS validation records and add them to Route 53 (Terraform handles this automatically if you defined `aws_route53_record.cert_validation`):

```bash
aws acm describe-certificate \
  --certificate-arn <arn> \
  --query 'Certificate.DomainValidationOptions[*].ResourceRecord'
```

Wait for the certificate status to become `ISSUED` (takes ~2 minutes after DNS propagates):

```bash
aws acm wait certificate-validated --certificate-arn <arn>
echo "Certificate issued"
```

### Create Route 53 DNS records

```bash
# Get Kong's ALB hostname
KONG_ALB=$(kubectl get svc kong-kong-proxy -n kong -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Get the ALB's hosted zone ID
ALB_ZONE=$(aws elbv2 describe-load-balancers \
  --query "LoadBalancers[?DNSName=='$KONG_ALB'].CanonicalHostedZoneId" \
  --output text)

# Create A alias records for api and main domain in Route 53
# (Add to Terraform aws_route53_record resources, then terraform apply)
```

### Configure Kong Ingress with TLS

Create a `KongIngress` resource that terminates SSL at the ALB and forwards to Kong over HTTP:

```yaml
# k8s/base/kong-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: kira-ingress
  namespace: kira
  annotations:
    kubernetes.io/ingress.class: kong
    konghq.com/strip-path: "false"
spec:
  tls:
    - hosts: [api.kira.abodeab.com]
      secretName: kira-tls-secret
  rules:
    - host: api.kira.abodeab.com
      http:
        paths:
          - path: /api/v1/auth
            pathType: Prefix
            backend:
              service: { name: identity-service, port: { number: 8001 } }
          - path: /api/v1/inventory
            pathType: Prefix
            backend:
              service: { name: rate-inventory-service, port: { number: 8002 } }
          # ... remaining services
```

### Verify HTTPS

```bash
# Should return 200
curl -I https://api.kira.abodeab.com/api/v1/health

# HTTP should redirect to HTTPS
curl -I http://api.kira.abodeab.com/api/v1/health
# HTTP/1.1 301 Moved Permanently
# Location: https://api.kira.abodeab.com/api/v1/health
```

---

## Step 8: CI/CD Activation

### Set GitHub Environments

In your GitHub repository: **Settings → Environments**

**staging environment:**
- No protection rules (auto-deploys on every merge to `main`)
- Add environment secrets if they differ from repository secrets

**production environment:**
- Required reviewers: add at least one team member
- This triggers the manual approval gate before production deploys

### Verify CI/CD on first push

Make a small change (update a comment) and push to main:

```bash
git checkout -b chore/test-cicd
echo "# test" >> services/identity-service/app/main.py
git commit -m "chore(identity): test CI/CD pipeline"
git push origin chore/test-cicd
# Open PR → merge to main
```

Watch the **Actions** tab. You should see:
1. `CI — identity-service` workflow triggered
2. `test` job passes (lint + pytest)
3. `build-and-push` job pushes image to ECR
4. `deploy-staging` job updates `kira-staging` namespace

Verify staging deployment:

```bash
kubectl get pods -n kira-staging
kubectl logs deployment/identity-service -n kira-staging | tail -20
```

---

## Step 9: Observability — development vs production

KIRA uses **different observability shapes** on your laptop versus in AWS on purpose: **dev is rich and self-contained**; **production starts small** so you are not running a second full platform beside EKS until you need it.

| | **Development** (`kira dev up --full` / `make up-full`) | **Production (recommended small scale)** | **Production (optional later)** |
|---|----------------------------------------------------------|------------------------------------------|----------------------------------|
| **Where it runs** | Docker Compose (`docker-compose.yml` + `docker-compose.observability.yml`) | **AWS only** — no separate Grafana/Prometheus/Loki **cluster** required | Self-hosted **Helm** on EKS (or **Grafana Cloud**) |
| **Metrics** | Prometheus scrapes services + exporters | **CloudWatch** / **Container Insights** (CPU, memory, request counts) | Prometheus + Grafana (or Mimir remote write) |
| **Logs** | **Grafana Alloy → Loki → Grafana** (same JSON logs as prod) | **CloudWatch Logs** (Fluent Bit / Container Insights DaemonSet) | **Alloy → Loki** (aligns with local **LGTM** stack) |
| **Dashboards** | Grafana on **:3001** (anonymous Viewer for convenience) | CloudWatch console, metrics, **Logs Insights** | Grafana on EKS (VPN / SSO, not public) |
| **Extra UIs** | Kafka UI, pgAdmin, Portainer, Redis Insight | Use **AWS consoles** / `kubectl` when needed | Same UIs as you choose to deploy |

**Same everywhere:** application code still emits **`/metrics`** (Prometheus format) and **JSON logs** via structlog — only the **collector and UI** change between dev (Loki stack) and small prod (CloudWatch).

---

### Recommended for production (small teams, low traffic): AWS CloudWatch

This is the **default recommendation** when you do **not** want a dedicated observability deployment on EKS: one billing line, no extra StatefulSets for Prometheus/Loki, alarms go straight to **SNS → email/PagerDuty**.

```bash
# Example: CloudWatch agent as DaemonSet (Container Insights)
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cwagent/cwagent-serviceaccount.yaml
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cwagent/cwagent-configmap.yaml
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cwagent/cwagent-daemonset.yaml
```

After this, metrics appear in **CloudWatch → Container Insights** and logs in **CloudWatch Logs** (e.g. under `/aws/containerinsights/...`). Query JSON fields with **Logs Insights** — same ideas as LogQL in Grafana, different UI. See **[Logging](../operations/logging.md#production-log-aggregation-cloudwatch)**.

---

### Optional later: self-hosted Grafana stack on EKS (matches the local **LGTM** stack)

When traffic, SLOs, or team size justify it, add **kube-prometheus-stack** + **Loki** + **Grafana Alloy** (not Promtail — EOL) in a `monitoring` namespace. That is the **same technology family** as dev (Grafana / Prometheus / Loki), **not** the same Compose files.

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword="$(openssl rand -base64 16)" \
  --set grafana.service.type=ClusterIP

# Loki: prefer current Grafana Helm charts with Alloy-based log collection (Promtail EOL).
```

Access Grafana via **port-forward** or private ingress — never expose Grafana admin to the public internet.

---

### Summary

- **Dev:** full **Compose** observability stack — use it freely; it does not run in production as-is.  
- **Prod (small):** **CloudWatch** for metrics + logs — **no** separate observability “instance” beyond AWS managed services and small agents.  
- **Prod (scale up):** add **LGTM on EKS** or **Grafana Cloud** when you outgrow CloudWatch-only.

---

## Step 10: Production Checklist

Complete all items before announcing production availability:

**Services**
- [ ] All pods show `Running` with 0 restarts: `kubectl get pods -n kira`
- [ ] All health endpoints return 200 through Kong
- [ ] HPA targets show real CPU values (not `<unknown>`): `kubectl get hpa -n kira`

**Networking**
- [ ] HTTPS working: `curl -I https://api.kira.abodeab.com/api/v1/health`
- [ ] HTTP redirects to HTTPS (301)
- [ ] DNS propagated: `nslookup api.kira.abodeab.com` resolves to ALB
- [ ] Kong rate limiting verified (send 101 requests, 101st should be 429)

**Data**
- [ ] All migrations applied: each service `alembic current` shows `head`
- [ ] Super admin user created and can log in
- [ ] First tenant created and accessible
- [ ] RDS snapshot exists: `aws rds describe-db-snapshots --db-instance-identifier kira-production`

**CI/CD**
- [ ] Staging auto-deploys on merge to `main` (test with a trivial commit)
- [ ] Production deploy workflow requires manual approval
- [ ] Both GitHub Environments configured with correct secrets

**Security**
- [ ] All secrets in AWS Secrets Manager — no plaintext secrets in K8s ConfigMaps
- [ ] ECR image scanning enabled (Terraform sets `scan_on_push = true`)
- [ ] RDS deletion protection enabled
- [ ] Security groups restrict RDS to EKS node SG only (not `0.0.0.0/0`)
- [ ] AWS WAF associated with ALB (add `aws_wafv2_web_acl_association` to Terraform)

**Observability**
- [ ] Metrics visible: **CloudWatch** Container Insights (small prod default) **or** Grafana/Prometheus if you run the optional Helm stack
- [ ] Log search working: find a known event in **CloudWatch Logs Insights** **or** Grafana/Loki
- [ ] At least one alert path live and tested: **CloudWatch alarm → SNS** **or** Prometheus rule (e.g. ServiceDown) via Alertmanager
- [ ] PagerDuty/OpsGenie integration tested (manually fire a test alert)

---

## Scaling Checklist

Reference guide for when to take each scaling action:

| Traffic level | Action |
|---|---|
| **100+ concurrent users** | Add second EKS node; set `reservation-service` and `channel-engine` to 2 replicas |
| **500+ concurrent users** | Add third EKS node; all services at 2+ replicas; add RDS read replica for reporting queries |
| **1 000+ tenants** | Enable Redis cluster mode (2+ shards); increase Kafka partitions on `ari.updated` (3 → 6); review per-tenant schema performance |
| **5 000+ tenants** | Multi-region deployment (ap-southeast-1 for Southeast Asia); dedicated RDS per region; CloudFront for static assets; consider horizontal database sharding |

See [Scaling](../operations/scaling.md) for detailed how-to instructions on each of these actions.
