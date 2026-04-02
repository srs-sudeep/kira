---
title: Scaling
description: Horizontal pod autoscaling, EKS node scaling, database read replicas and connection pooling, Redis cluster mode, and Kafka partition scaling.
sidebar_position: 5
---

# Scaling

**What you'll learn:**
- How HPA scales pods in response to CPU load
- When to add EKS nodes and how Cluster Autoscaler handles it
- Database scaling: read replicas and PgBouncer connection pooling
- Redis and Kafka scaling options

---

## Horizontal Pod Autoscaling (HPA)

Every KIRA service has an HPA. When average CPU across all pods in a Deployment exceeds 70%, the HPA adds pods. When CPU drops below 70% for 5 minutes (stabilisation window), it removes them.

### Current HPA settings

| Service | Min pods | Max pods | Scale trigger |
|---|---|---|---|
| identity-service | 2 | 5 | CPU > 70% |
| rate-inventory-service | 2 | 5 | CPU > 70% |
| reservation-service | 2 | 5 | CPU > 70% |
| channel-engine (API) | 2 | 5 | CPU > 70% |
| channel-engine (worker) | 1 | 5 | CPU > 70% |
| notification-service | 2 | 5 | CPU > 70% |
| admin-service | 2 | 5 | CPU > 70% |

*Staging uses min 1, max 3 for all services.*

### Checking HPA status

```bash
kubectl get hpa -n kira

# Expected output (healthy):
# NAME                       REFERENCE                         TARGETS   MINPODS   MAXPODS   REPLICAS
# identity-service           Deployment/identity-service       23%/70%   2         5         2
# channel-engine             Deployment/channel-engine         45%/70%   2         5         3
```

`TARGETS` shows `<current>/<target>`. If you see `<unknown>` in the TARGETS column, the metrics server is not running — check `kubectl top pods -n kira`.

### Adjusting HPA limits

Edit `k8s/base/<service>/hpa.yaml` and apply:

```yaml
spec:
  minReplicas: 3   # increase minimum for sustained high load
  maxReplicas: 10  # increase maximum if 5 is not enough
```

```bash
kubectl apply -k k8s/overlays/production/
```

### Custom metrics scaling

The current HPA scales on CPU only. If channel-engine needs to scale based on Kafka consumer lag instead:

1. Install `keda` (Kubernetes Event-driven Autoscaling) in the cluster
2. Replace the HPA with a `ScaledObject` that reads from the Kafka metrics endpoint
3. Set `lagThreshold` to the target lag per pod

---

## EKS Node Scaling

### Cluster Autoscaler

The EKS Auto Scaling Group has Cluster Autoscaler installed. When:
- A pod cannot be scheduled because no node has enough CPU/memory → Cluster Autoscaler provisions a new node (takes ~3–5 minutes)
- A node is underutilised for 10 minutes → Cluster Autoscaler terminates it (respects pod disruption budgets)

### When to manually add nodes

If you are about to deploy a large feature or expect a traffic spike (OTA integration launch, hotel partner onboarding):

1. Increase the ASG desired count in Terraform:

```hcl
eks_desired_nodes = 5   # up from 3
```

2. Apply: `terraform apply`

3. After the event, reduce back: `eks_desired_nodes = 3`

### Node sizing guidance

Current production node type: `t3.xlarge` (4 vCPU, 16 GB RAM).

With 2 pods minimum per service × 6 services = 12 pods at minimum. Each pod requests 256 MB and 100m CPU. A `t3.xlarge` can comfortably run ~20 KIRA pods.

If individual services need more memory (e.g., large in-memory caches), move to `t3.2xlarge` or consider `c5.2xlarge` (compute optimised) for CPU-heavy workloads.

---

## Database Scaling

### Read replicas

The current RDS setup is a single primary (Multi-AZ for failover, not read scaling). To add a read replica:

```hcl
resource "aws_db_instance" "kira_read" {
  replicate_source_db    = aws_db_instance.kira.identifier
  instance_class         = "db.t3.large"
  publicly_accessible    = false
}
```

Services would need a `READ_REPLICA_URL` env var and explicit use of the replica connection for read-only queries. Only add this when primary CPU or I/O is consistently high. Check the RDS CloudWatch metrics first.

### PgBouncer connection pooling

FastAPI with asyncpg opens persistent connections per pod. With 20 pods × 20 connections = 400 connections, which is fine for RDS `db.t3.xlarge` (max connections ~820).

If you scale to 50+ pods or add more services, deploy PgBouncer in transaction pooling mode:

```yaml
# k8s/base/pgbouncer/deployment.yaml
# pgbouncer pools connections: many pods → fewer DB connections
# Services connect to pgbouncer:5432, not RDS directly
```

Transaction pooling mode is compatible with KIRA's async SQLAlchemy setup. Session pooling mode is **not** compatible because it holds the connection for the duration of the HTTP request.

:::warning Multi-tenant search_path and PgBouncer
PgBouncer transaction mode resets `search_path` between transactions. The `TenantMiddleware` sets `search_path` at the start of each request via `SET search_path TO ...`. In transaction pooling mode, this SET is issued per query batch — verify it applies correctly before deploying PgBouncer in production.
:::

---

## Redis Scaling

### Current setup

ElastiCache with 2 shards, cluster mode enabled. Each shard handles a subset of the keyspace.

### Scaling up

Add shards in Terraform:

```hcl
resource "aws_elasticache_replication_group" "kira" {
  num_node_groups = 4   # up from 2
}
```

ElastiCache can reshard online without downtime (rebalancing takes ~30 minutes).

### What to do if Redis is the bottleneck

1. Check `redis-cli info stats` for `instantaneous_ops_per_sec` and `used_memory`
2. Identify the high-traffic commands with `redis-cli monitor` (sample for 10 seconds — do not leave running in production)
3. If most ops are `GET`/`SET` from Celery, move Celery to a dedicated Redis instance (separate ElastiCache cluster)
4. If session lookups dominate, increase the ElastiCache node size

---

## Kafka Scaling

### Current setup

MSK with 3 brokers (`kafka.t3.small`). Topics have 3 partitions each.

### Adding partitions

More partitions = more consumer parallelism. Add partitions when consumer lag is consistently high and adding more pods doesn't help (because the partition count limits parallelism):

```bash
# Increase ari.updated from 3 to 6 partitions
kafka-topics --bootstrap-server kafka:9092 \
  --alter --topic ari.updated \
  --partitions 6
```

:::warning Partitions can only be increased, never decreased
Adding partitions is safe. You cannot remove partitions from a topic without deleting and recreating it (which loses messages).
:::

### Adding brokers

If broker disk or throughput is the bottleneck, add brokers to MSK:

```hcl
resource "aws_msk_cluster" "kira" {
  number_of_broker_nodes = 6   # up from 3, must be multiple of AZ count
}
```

After adding brokers, rebalance partitions across brokers using `kafka-reassign-partitions`.

### Upgrade broker instance type

For CPU/memory constraints:

```hcl
broker_node_group_info {
  instance_type = "kafka.m5.large"   # up from kafka.t3.small
}
```

This requires a rolling broker restart — MSK handles it with no message loss.
