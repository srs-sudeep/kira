---
title: Local Kubernetes validation
description: Smoke-test a dev Kubernetes cluster and validate KIRA manifests without EKS — what exists today, limits of k8s/, and where full setup is documented.
sidebar_position: 4
---

# Local Kubernetes validation

KIRA’s **application day-to-day dev** is **Docker Compose** (`docker-compose.yml`). The **`k8s/`** tree is for **real clusters** (staging/production on **EKS**). There is **no** bundled overlay that reproduces Postgres + Redis + Kafka + all services on a laptop cluster.

This page fills the gap: **how to check that Kubernetes itself and your `kubectl` setup work**, and **how far you can validate `k8s/` before EKS**.

---

## What is already documented

| Topic | Doc |
|--------|-----|
| Kustomize layout, `kubectl apply -k`, rollouts, HPAs | [Kubernetes](./kubernetes.md) |
| EKS, `aws eks update-kubeconfig`, secrets, deploy order, checklists | [AWS production](./aws-production.md) |
| GitHub Actions → ECR → `kubectl set image` | [CI/CD pipeline](./cicd-pipeline.md) |
| Optional install of `kubectl` / `eksctl` | [Prerequisites](../getting-started/prerequisites.md) |

---

## Tier 1 — Is your dev cluster healthy?

Use any **local** control plane: **Docker Desktop → Kubernetes**, **[kind](https://kind.sigs.k8s.io/)**, **[minikube](https://minikube.sigs.k8s.io/)**, or **k3d**. Install `kubectl`, point it at the cluster, then:

```bash
kubectl config current-context
kubectl cluster-info
kubectl get nodes
# Ready nodes and a valid control plane URL mean the cluster is basically OK
kubectl get --raw='/readyz?verbose'
```

Optional (if you installed [metrics-server](https://github.com/kubernetes-sigs/metrics-server)):

```bash
kubectl top nodes
```

**Interpretation:** If these succeed, your **cluster** is fine. That does **not** mean KIRA’s full stack is deployable from `k8s/` alone (manifests expect **Secrets**, **ECR images**, and external **RDS / Redis / Kafka** or equivalents).

---

## Tier 2 — Validate manifests without applying

Use **client-side dry-run** on individual files (safe, no cluster changes):

```bash
# Example: namespace + config only (adjust paths as needed)
kubectl apply --dry-run=client -f k8s/base/namespace.yaml
kubectl apply --dry-run=client -f k8s/base/configmap.yaml
```

To preview combined YAML, **`kubectl kustomize`** / **`kubectl apply -k`** against **`k8s/base`** may error if Kustomize’s namespace transformer conflicts with multiple `Namespace` objects in the base (see `k8s/base/namespace.yaml`). Until that is simplified, prefer **per-file** dry-runs or fix the base layout in a dedicated change.

**Staging/production overlays** embed **`${ECR_REGISTRY}`** in `kustomization.yaml` `images:` entries. Plain `kubectl kustomize` does not expand shell variables; CI uses env substitution or `kubectl set image` after apply. For a one-off local render, set a placeholder registry in a **copy** of the overlay or use the same `envsubst` pattern as your pipeline.

---

## Tier 3 — “Does KIRA run on my laptop K8s?”

Not out of the box:

- Deployments reference **images** (e.g. ECR or `kira-*:latest`) that you must **build and load** into the local cluster (`kind load docker-image …`, etc.).
- Each service expects **Kubernetes Secrets** (see `k8s/base/secrets-template.yaml`).
- **Data plane** (Postgres, Redis, Kafka) is **not** defined in `k8s/base`; AWS docs assume RDS, ElastiCache, MSK (or Phase-1 shortcuts on EKS).

So **dev-level “is the cluster OK?”** = Tier 1. **Dev-level “is the whole app on K8s?”** = either **staging on EKS** or a **custom** local overlay (not shipped in this repo today).

---

## Recommended workflow

1. **Daily dev:** Compose — [Local Docker](./local-docker.md).
2. **Before touching EKS:** Run Tier 1 on a disposable local cluster to confirm `kubectl` + networking.
3. **First real deploy:** Follow [AWS production](./aws-production.md) and [Kubernetes](./kubernetes.md); use staging before production.

---

## Related

- [Deployment overview](./overview.md) — Compose vs EKS roles.
- [Runbooks](../operations/runbooks.md) — `kubectl` troubleshooting once workloads are running.
