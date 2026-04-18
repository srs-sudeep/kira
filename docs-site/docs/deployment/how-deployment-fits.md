---
title: How deployment fits together
description: Mental model for local Docker Compose vs EKS production, which AWS services you touch, small traffic vs scale-up, and the minikube overlay.
sidebar_position: 0
---

# How deployment fits together

Use this page when the **split between Compose, Kubernetes, Terraform, and AWS** feels unclear. Deep procedures live in the linked guides; here is the **map**.

---

## The mental model (three layers)

| Layer | What it is | In this repo |
| ----- | ---------- | ------------- |
| **1. App packaging** | Each service is a **Docker image** (API, web, workers). | `docker/*.Dockerfile`, CI builds and pushes to **ECR**. |
| **2. Runtime on a cluster** | Images run as **Pods**; scaling, networking, secrets = **Kubernetes**. | `k8s/` (Kustomize), **EKS** in AWS for staging/production. |
| **3. Managed data & network** | Databases and queues are **AWS managed** (or Phase-1 shortcuts). | **Terraform** under `infra/terraform/` — VPC, **RDS**, **ElastiCache**, **MSK** (optional), **EKS**, etc. |

**Local dev** skips layer 2 for the full stack: **Docker Compose** runs the same *containers* on one machine (Postgres, Redis, Kafka, APIs, web). That is **not** mini-EKS; it is the fastest way to develop.

**Production** uses **EKS** so you get rolling updates, health checks, HPAs, and isolation — same *idea* as Compose (containers + env), different *orchestrator*.

---

## How code gets to production (happy path)

1. You merge to `main`; **GitHub Actions** runs tests and builds images.
2. Images are tagged with the **git SHA** and pushed to **ECR**.
3. **Staging** (EKS namespace `kira-staging`) is updated automatically (typical pattern — see [CI/CD pipeline](./cicd-pipeline.md)).
4. **Production** is promoted when **you** choose (e.g. workflow with `image_tag`) — see [Deployment overview](./overview.md).

You do **not** manually `docker compose` on a server for production; you **`kubectl apply`** / GitOps / CI applies manifests that point at ECR images and **Secrets** (DB URLs, JWT secrets, …).

---

## AWS: what you actually work with

These are the **building blocks** this project's docs assume (see [Deployment overview](./overview.md) and [AWS production](./aws-production.md)):

| AWS service | Role in KIRA |
| ----------- | ------------- |
| **EKS** | Where all app **Pods** run (APIs, web, workers, Kong, …). |
| **ECR** | **Private Docker registry** — each microservice image. |
| **RDS (PostgreSQL)** | Real **tenant/app data** — replaces the Compose `postgres` container. |
| **ElastiCache (Redis)** | Cache, Celery broker, etc. — replaces Compose `redis`. |
| **MSK** (optional early) | **Kafka** — event bus. Expensive; [AWS production](./aws-production.md) describes **Phase 1** options (e.g. Kafka on EKS) before MSK. |
| **VPC, subnets, NAT, SGs** | Networking between EKS, RDS, Redis, MSK. |
| **IAM** | Permissions for CI, nodes, and humans (`kubectl`, Terraform). |
| **S3, Route 53, ACM, Secrets Manager** | Assets, DNS/TLS, secret storage — see full Terraform layout in AWS doc. |
| **CloudWatch** | Logs and metrics (plus optional Grafana path in docs). |

**Few users now, more later:** you still use the **same services**; you change **sizes and counts** (smaller RDS/ElastiCache SKUs, fewer **EKS nodes**, `minReplicas` on HPAs, optional skip of **MSK** until traffic needs it). Staging already assumes **1 replica** per service; production defaults to **2+** with HPA — tune when you are small.

---

## Local: Docker Compose **or** minikube?

| Approach | Use it when |
| -------- | ----------- |
| **Docker Compose** (`docker/docker-compose.yml`, `kira dev up`, `make up`) | **Daily development** — full stack on your laptop, hot reload, matches how the team works. **Start here.** |
| **minikube overlay** (`k8s/overlays/minikube/`) | **Test the full K8s deployment path** with in-cluster Postgres, Redis, and Kafka — no AWS account needed. See [Local Kubernetes validation](./local-kubernetes.md). |

The **minikube overlay** ships a complete Kustomize overlay with StatefulSet Postgres, single-node Redis, and KRaft Kafka so KIRA boots on a local cluster. Use it to:

- **Validate K8s manifests, probes, and service networking end-to-end.**
- **Test secret wiring, ConfigMap overrides, and image loading.**
- **Practise `kubectl` workflows before touching EKS.**

It **cannot** replicate RDS Multi-AZ, ElastiCache clustering, MSK durability, real TLS/DNS, or HPAs (no metrics-server by default).

- **Develop the product → Compose.**
- **Test K8s deployment path → minikube overlay.**
- **Ship to users → EKS + Terraform + CI as in the AWS guide.**

---

## Where to read next

| Goal | Doc |
| ---- | --- |
| Run everything locally | [End-to-end local dev](../getting-started/e2e-local-dev.md), [Local Docker](./local-docker.md) |
| Understand EKS manifests | [Kubernetes](./kubernetes.md) |
| Provision AWS + EKS | [AWS production](./aws-production.md) |
| Full prod checklist | [End-to-end production](./e2e-production.md) |
| CI → ECR → deploy | [CI/CD pipeline](./cicd-pipeline.md) |
| Deploy on minikube | [Local Kubernetes validation](./local-kubernetes.md) |

---

## Short answers

**"How does production work if I use K8s and infra?"**  
Terraform (or your IaC) creates **VPC + EKS + RDS + Redis + (Kafka)**. CI builds **images** to **ECR**. **Kubernetes** in EKS runs those images using **`k8s/`** manifests and **Secrets** that point at RDS/Redis/Kafka endpoints.

**"Do I need minikube locally?"**  
**No** for normal KIRA development — use **Compose**. Use the **minikube overlay** when you want to test the real Kubernetes deployment path (manifests, probes, secrets, networking) without AWS.

**"Which AWS services for a small user base?"**  
Same list as above, **smaller SKUs** and optional **MSK** deferral; see cost / Phase-1 notes in [AWS production](./aws-production.md).
