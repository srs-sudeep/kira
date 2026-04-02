---
title: Backup and Recovery
description: PostgreSQL backups, Redis snapshots, Kafka retention, disaster recovery objectives, and step-by-step recovery procedures.
sidebar_position: 4
---

# Backup and Recovery

**What you'll learn:**
- How PostgreSQL, Redis, and Kafka data is backed up
- Recovery time and recovery point objectives
- Step-by-step recovery procedures for common failure scenarios

---

## Recovery Objectives

| Objective | Target | How it is met |
|---|---|---|
| **RTO** (Recovery Time Objective) | < 1 hour | Multi-AZ RDS failover is automatic (~60s). Full restore from snapshot takes ~20 min. |
| **RPO** (Recovery Point Objective) | < 15 minutes | RDS automated backups + transaction logs enable point-in-time recovery to within 5 minutes. |

---

## PostgreSQL Backups

### RDS Automated Backups (production)

RDS is configured with:
- **Automated backups:** enabled, 7-day retention window
- **Backup window:** 02:00–03:00 UTC (low traffic)
- **Multi-AZ:** standby replica in `ap-south-1b` — automatic failover within ~60 seconds on primary failure
- **Point-in-time recovery (PITR):** restore to any second within the 7-day retention window

```hcl
# infra/terraform/rds.tf
resource "aws_db_instance" "kira" {
  backup_retention_period = 7
  backup_window           = "02:00-03:00"
  multi_az                = true
  deletion_protection     = true
}
```

### Manual snapshot before risky operations

Before running migrations or destructive operations:

```bash
aws rds create-db-snapshot \
  --db-instance-identifier kira-production \
  --db-snapshot-identifier kira-pre-migration-$(date +%Y%m%d%H%M) \
  --region ap-south-1
```

### pg_dump for local dev or selective restore

```bash
# Full dump
pg_dump -h localhost -U postgres -d kira -Fc -f kira_$(date +%Y%m%d).dump

# Restore from dump
pg_restore -h localhost -U postgres -d kira -Fc kira_20260402.dump

# Dump a single tenant schema
pg_dump -h localhost -U postgres -d kira \
  -n "tenant_abc123" -Fc -f tenant_abc123_$(date +%Y%m%d).dump
```

---

## Redis Backups

Redis is used for sessions, Celery queues, and circuit breaker state — all of which can be reconstructed from PostgreSQL if lost. Redis data loss means:
- Active user sessions log out (users must re-authenticate)
- In-flight Celery tasks are lost (will re-trigger on next ARI update or reservation event)
- Circuit breaker state resets to closed (OTA sync will attempt normally)

This is acceptable within the RPO window.

### ElastiCache Redis (production)

ElastiCache is configured with daily RDB snapshots:

```hcl
resource "aws_elasticache_replication_group" "kira" {
  snapshot_retention_limit = 3       # keep 3 daily snapshots
  snapshot_window          = "03:00-04:00"
}
```

### Local dev Redis

Redis data in local dev is stored in the `redisdata` Docker named volume. It persists between `docker compose down` restarts. Use `docker compose down -v` to wipe it when you want a clean state.

---

## Kafka Topic Retention

Kafka is not a source of truth — it is a transport layer. Events are published by services and consumed once. The data that matters is in PostgreSQL.

Topic retention policy:

| Topic | Retention | Why |
|---|---|---|
| `ari.updated` | 24 hours | ARI events are large volume; current state is in PostgreSQL |
| `reservation.created` | 7 days | Allows replay if notification-service was down |
| `reservation.cancelled` | 7 days | Same as above |
| `channel.sync.failed` | 7 days | For debugging persistent sync failures |
| `tenant.created` | 30 days | Low volume; useful for audit |

If channel-engine or notification-service is down for an extended period, it can replay events on restart (consumer group offset is committed only after processing). Events older than the retention window are gone — a service down for > 7 days will miss those events.

---

## Disaster Recovery Procedures

### Scenario 1: RDS instance failure (Multi-AZ failover)

**What happens automatically:**
1. RDS detects primary failure
2. Promotes standby in `ap-south-1b` to primary (~60 seconds)
3. DNS record for the RDS endpoint is updated
4. Services reconnect on their next query (SQLAlchemy connection pool retries)

**What you need to do:**
1. Check the RDS console for the failover event
2. Verify all services are healthy: `kubectl get pods -n kira`
3. Check Grafana for elevated error rates during the ~60s failover window
4. Create a new standby (AWS does this automatically within 30 minutes)

### Scenario 2: Full RDS restore from snapshot

Use this when you need to recover from data corruption or accidental deletion.

```bash
# 1. Find the snapshot to restore from
aws rds describe-db-snapshots \
  --db-instance-identifier kira-production \
  --query 'DBSnapshots[*].{ID:DBSnapshotIdentifier,Time:SnapshotCreateTime,Status:Status}' \
  --region ap-south-1

# 2. Restore to a new instance
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier kira-production-restored \
  --db-snapshot-identifier kira-production-2026-04-01-02-00 \
  --db-instance-class db.t3.xlarge \
  --multi-az \
  --region ap-south-1

# 3. Update DATABASE_URL secrets in K8s to point to the new instance
# 4. Restart all pods to pick up the new connection string
kubectl rollout restart deployment -n kira

# 5. Run any migrations missed since the snapshot
# 6. Rename/delete the old instance once verified
```

:::warning Point-in-time recovery for partial data loss
For accidental deletion of specific records (e.g., a tenant schema dropped), use PITR to restore to just before the incident:

```bash
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier kira-production \
  --target-db-instance-identifier kira-pitr-restore \
  --restore-time 2026-04-02T09:55:00Z
```

Restore to a new instance, extract the affected data using pg_dump, and import it into the production instance.
:::

### Scenario 3: EKS node failure

EKS worker nodes are in an Auto Scaling Group. If a node fails:
1. K8s marks the node as `NotReady`
2. Pods on the failed node are rescheduled on healthy nodes within ~2 minutes
3. The ASG replaces the failed node automatically

If all nodes in an AZ fail simultaneously (rare):
1. Cluster Autoscaler requests new nodes in other AZs
2. This takes ~5 minutes
3. Production minimum: 2 replicas per service, spread across AZs — at least one pod survives single-AZ failure

### Scenario 4: Kafka data loss

If a Kafka topic loses messages (broker failure during retention window):
- `ari.updated` events: Trigger a manual ARI re-sync from rate-inventory-service
- `reservation.created/cancelled` events: Notification-service may have missed some emails. Check `notifications` table for gaps and re-send manually via admin API
- `channel.sync.failed` events: These are informational — no data loss, just missing alerts

For MSK, AWS handles broker replacement automatically. The MSK cluster uses 3 brokers with replication factor 2 — losing one broker does not cause data loss.

---

## Backup Testing Schedule

Backups are only useful if restores work. Test quarterly:

| Test | Frequency | Procedure |
|---|---|---|
| RDS PITR restore | Quarterly | Restore to a temporary instance, verify schema and row counts |
| Full snapshot restore | Semi-annually | Full restore to a staging-sized instance, run migrations, smoke test |
| Kafka replay | Quarterly | Set consumer group offset to start of retention, verify events re-process cleanly |
