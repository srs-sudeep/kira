---
title: Operations cheat sheet
description: Dense reference for production checks, kubectl one-liners, logs, metrics, and where the long-form docs live.
sidebar_position: 0
---

# Operations cheat sheet

Use this page as a **fast index**. For narrative and edge cases, follow the links at the end of each section.

---

## First 5 minutes on an incident

1. **Scope:** Which tenant, service, and region? Any change window?
2. **Kubernetes:** `kubectl get pods -n kira`, `kubectl describe pod <pod> -n kira`, `kubectl logs <pod> -n kira` (add `--previous` if CrashLoop).
3. **Dependencies:** RDS/ElastiCache/Kafka reachable from nodes? Security groups unchanged?
4. **Alerts:** Grafana → Alerting; Prometheus → **Alerts**; PagerDuty/OpsGenie for firing rules.
5. **Mitigate then fix:** scale up, toggle feature flag, circuit breaker — then root-cause.

Runbooks with commands: **[Runbooks](./runbooks.md)**.

---

## kubectl (production `kira` namespace)

| Goal | Command |
|------|---------|
| Pods | `kubectl get pods -n kira -o wide` |
| Events | `kubectl get events -n kira --sort-by='.lastTimestamp' \| tail -30` |
| Logs (follow) | `kubectl logs -f deployment/<service> -n kira` |
| Previous crash | `kubectl logs <pod> -n kira --previous` |
| Shell | `kubectl exec -it deployment/<service> -n kira -- /bin/bash` |
| Restart | `kubectl rollout restart deployment/<service> -n kira` |
| Rollback | `kubectl rollout undo deployment/<service> -n kira` |
| HPA | `kubectl get hpa -n kira` |

Staging uses namespace **`kira-staging`** (see [Kubernetes](../deployment/kubernetes.md)).

---

## Logs

| Where | How |
|-------|-----|
| **Local** | Grafana → Explore → **Loki**; labels `service`, `container`. |
| **EKS** | CloudWatch Logs (if shipped) or kubectl logs; for Loki-based stacks see [Logging](./logging.md). |

Log format (JSON / `structlog`): [Logging — Structured JSON](./logging.md#structured-json-logging).

---

## Metrics and dashboards

| Tool | Typical use |
|------|-------------|
| **Grafana** | SLO dashboards, Loki, Prometheus Explore. |
| **Prometheus** | `up`, scrape errors, `rate(http_requests_total[5m])`. |
| **Alertmanager** | Silences, routing, on-call schedules. |

Provisioning paths and scrape config: [Monitoring](./monitoring.md).

---

## Data and backups

| Task | Pointer |
|------|---------|
| RDS snapshot / PITR | [Backup and recovery](./backup-and-recovery.md) |
| pg_dump / restore (runbook-style) | Same page + [Runbooks](./runbooks.md) |

---

## TLS and ingress

Certificate checks and ACM renewal: [Runbooks — SSL](./runbooks.md#ssl-certificate-expiring) and [SSL and domains](../deployment/ssl-and-domains.md).

---

## Scaling and capacity

HPA, node groups, Kafka partition planning: [Scaling](./scaling.md).

---

## DLQ and Kafka

Topic naming and replay checklist: [Runbooks — Replay DLQ](./runbooks.md#replay-dead-letter-queue-messages) · [Event-driven architecture](../architecture/event-driven.md#dead-letter-queue).

---

## Related

| Doc | Use when |
|-----|----------|
| [Alerting](./alerting.md) | Rule catalogue, PagerDuty wiring |
| [Runbooks](./runbooks.md) | Step-by-step incidents |
| [Monitoring](./monitoring.md) | Prometheus/Grafana setup |
| [Logging](./logging.md) | LogQL, Loki, levels |
| [E2E production](../deployment/e2e-production.md) | Go-live checklist |
