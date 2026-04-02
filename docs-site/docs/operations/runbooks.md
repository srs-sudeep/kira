---
title: Runbooks
description: Step-by-step diagnosis and resolution for the most common KIRA production incidents.
sidebar_position: 6
---

# Runbooks

Each runbook follows: **Symptoms → Diagnosis commands → Resolution steps.**

---

## Service Won't Start

### Symptoms
- Pod in `CrashLoopBackOff` or `Error` state
- `kubectl get pods -n kira` shows `RESTARTS > 0`
- Service unreachable; other services report connection errors

### Diagnosis

```bash
# Check pod status and restart count
kubectl get pods -n kira | grep <service-name>

# Check recent pod events (probe failures, OOM kills, image pull errors)
kubectl describe pod <pod-name> -n kira

# Check application logs from the last crashed container
kubectl logs <pod-name> -n kira --previous

# Check the current container's logs (if partially started)
kubectl logs <pod-name> -n kira
```

Common error patterns in logs:

| Log message | Cause |
|---|---|
| `Connection refused` to postgres/redis | Dependency not ready; wrong host/port in env |
| `password authentication failed` | Wrong DATABASE_URL in secret |
| `ModuleNotFoundError` | Missing package; image build failed or used wrong tag |
| `pydantic_core.ValidationError` | Required env var missing or wrong type |
| `OOMKilled` (in `kubectl describe`) | Pod hit memory limit; increase `resources.limits.memory` |

### Resolution

1. **Missing env var:** Update the K8s secret or ConfigMap and restart:
   ```bash
   kubectl rollout restart deployment/<service> -n kira
   ```

2. **Wrong image tag:** Redeploy with the correct tag:
   ```bash
   kubectl set image deployment/<service> <service>=<registry>/<image>:<correct-tag> -n kira
   ```

3. **Database unreachable:** Verify RDS endpoint and security group allow traffic from EKS nodes. Check the RDS console for maintenance or failover events.

4. **OOMKilled:** Edit the deployment resources patch and increase memory limit, then `kubectl apply -k k8s/overlays/production/`.

---

## Channel Sync Failing

### Symptoms
- `ChannelCircuitOpen` or `ChannelSyncFailingLong` alert fires
- Property manager reports OTA is showing different availability than KIRA
- `channel.sync.failed` Kafka messages accumulating

### Diagnosis

```bash
# Check which channels have open circuit breakers
kubectl exec -it deployment/channel-engine -n kira -- \
  python -c "
import asyncio
from app.database import get_session
from app.repositories.channel_repository import ChannelRepository

async def check():
    async with get_session() as session:
        repo = ChannelRepository(session)
        channels = await repo.get_all_for_tenant('all')
        for c in channels:
            print(c.id, c.name, c.status, c.consecutive_failures)

asyncio.run(check())
"

# Check recent sync log via API
curl -H "Authorization: Bearer <token>" \
  https://api.kira.abodeab.com/api/v1/channels/<channel-id>/sync-log?page_size=20

# Check channel-engine logs for error details
kubectl logs deployment/channel-engine -n kira | grep "sync_failed" | tail -20
```

### Resolution

1. **OTA API returning 4xx (auth error):** Channel credentials may have expired. Update them via the dashboard or API (`PATCH /api/v1/channels/<id>`) and trigger a manual sync:
   ```bash
   curl -X POST -H "Authorization: Bearer <token>" \
     https://api.kira.abodeab.com/api/v1/channels/<channel-id>/sync
   ```

2. **OTA API temporarily down (5xx):** Circuit breaker is working as intended. Wait 5 minutes for auto-recovery. If the OTA is known to be down for longer, silence the alert.

3. **Rate limit hit:** Check the OTA developer console for rate limit errors. Reduce `booking_pull_interval` in channel-engine config or implement per-OTA rate limiting.

4. **Manually reset circuit breaker:** If the OTA is back up but the circuit is still open (stuck state):
   ```bash
   kubectl exec -it deployment/channel-engine -n kira -- \
     python -c "
   import asyncio
   from app.database import get_session
   from app.repositories.channel_repository import ChannelRepository

   async def reset():
       async with get_session() as session:
           repo = ChannelRepository(session)
           await repo.reset_circuit_breaker('<channel-id>')
           await session.commit()
           print('Reset done')

   asyncio.run(reset())
   "
   ```

---

## Database Connection Exhausted

### Symptoms
- `asyncpg.TooManyConnectionsError` in logs
- All services returning 500 errors simultaneously
- RDS CloudWatch metric `DatabaseConnections` at maximum

### Diagnosis

```bash
# Check current connection count from RDS metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=kira-production \
  --start-time $(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Maximum

# Check which hosts are holding connections (run on the RDS instance)
kubectl exec -it deployment/identity-service -n kira -- \
  python -c "
import asyncio, asyncpg

async def check():
    conn = await asyncpg.connect('$DATABASE_URL')
    rows = await conn.fetch(
        \"SELECT client_addr, count(*) FROM pg_stat_activity GROUP BY client_addr ORDER BY count DESC\"
    )
    for r in rows:
        print(r)
    await conn.close()

asyncio.run(check())
"
```

### Resolution

1. **Immediate relief — terminate idle connections:**
   ```sql
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE state = 'idle'
     AND query_start < now() - interval '5 minutes';
   ```

2. **Reduce pod count temporarily:**
   ```bash
   kubectl scale deployment identity-service --replicas=1 -n kira
   # repeat for other services contributing to the connection count
   ```

3. **Root cause — connection leak:** Search logs for unclosed SQLAlchemy sessions. All database access should use `async with get_session() as session:` context manager.

4. **Long-term fix:** Deploy PgBouncer in transaction pooling mode. See [Scaling — PgBouncer](./scaling.md#pgbouncer-connection-pooling).

---

## Kafka Consumer Lag Increasing

### Symptoms
- `KafkaConsumerLagHigh` alert fires
- ARI updates not reaching OTAs (lag on `ari.updated`)
- Reservation confirmation emails delayed (lag on `reservation.created`)

### Diagnosis

```bash
# Check lag via Kafka UI at http://localhost:8080 (local) or port-forward in production

# Or via kafka-consumer-groups CLI
kubectl exec -it <kafka-pod> -n kira -- \
  kafka-consumer-groups \
    --bootstrap-server localhost:9092 \
    --describe \
    --group channel-engine

# Check channel-engine Celery worker logs
kubectl logs deployment/channel-engine-worker -n kira | tail -50

# Check if workers are running
kubectl get pods -n kira | grep worker
```

### Resolution

1. **Consumer pod is down:** Restart the worker deployment:
   ```bash
   kubectl rollout restart deployment/channel-engine-worker -n kira
   ```

2. **Consumer is slow (processing backlog):** Scale up the worker:
   ```bash
   kubectl scale deployment channel-engine-worker --replicas=5 -n kira
   ```
   *Note: the number of effective parallel consumers is limited by the number of partitions on the topic. If the topic has 3 partitions, more than 3 consumer pods will be idle.*

3. **Topic has too few partitions for the load:** Increase partitions (see [Scaling — Kafka](./scaling.md#adding-partitions)) then scale workers.

4. **Broker disk full:** Check MSK broker disk usage in CloudWatch (`KafkaBytesOutPerSec`, `GlobalPartitionCount`). Delete old consumer group offsets for inactive groups or increase topic retention.

---

## Disk Space Running Out

### Symptoms
- `DiskSpaceLow` or `DiskSpaceCritical` alert fires
- Pod logs contain "no space left on device" errors
- Database write failures

### Diagnosis

```bash
# Check node disk usage
kubectl top nodes

# Check which pod directories are large
kubectl exec -it <node-debug-pod> -- df -h

# For RDS disk, check CloudWatch FreeStorageSpace metric
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name FreeStorageSpace \
  --dimensions Name=DBInstanceIdentifier,Value=kira-production \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Minimum
```

### Resolution

**EKS node disk full:**
1. Identify large directories: Docker image cache is usually the culprit
2. Run `docker image prune -f` on the node (via a privileged debug pod)
3. Increase the EKS node's EBS volume size in Terraform

**RDS disk full:**
1. Immediate: enable RDS autoscaling (`max_allocated_storage`) in Terraform — RDS will expand automatically
2. Check for bloated tables: `SELECT relname, pg_size_pretty(pg_relation_size(oid)) FROM pg_class ORDER BY pg_relation_size(oid) DESC LIMIT 10;`
3. Run `VACUUM FULL` on bloated tables (causes a brief lock — schedule during low traffic)

**Kafka disk full:**
1. Reduce retention period on high-volume topics (e.g., `ari.updated` from 24h to 12h)
2. Increase MSK broker storage in Terraform

---

## SSL Certificate Expiring {#ssl-certificate-expiring}

### Symptoms
- `SSLCertExpiringSoon` alert fires (< 14 days remaining)
- Email from AWS: "Your certificate is about to expire"

### Diagnosis

```bash
# Check certificate expiry
echo | openssl s_client -connect api.kira.abodeab.com:443 2>/dev/null \
  | openssl x509 -noout -dates

# Check ACM certificate status
aws acm describe-certificate \
  --certificate-arn <arn> \
  --region ap-south-1 \
  --query 'Certificate.{Status:Status,NotAfter:NotAfter,RenewalStatus:RenewalSummary.RenewalStatus}'
```

### Resolution

ACM certificates renew automatically if the DNS validation CNAME records are still in Route 53. If the certificate is not auto-renewing:

1. Check that the DNS validation CNAME records exist in Route 53:
   ```bash
   aws acm describe-certificate --certificate-arn <arn> \
     --query 'Certificate.DomainValidationOptions[*].ResourceRecord'
   ```

2. If the CNAME records were accidentally deleted, re-run `terraform apply` — Terraform will recreate them from `aws_route53_record.cert_validation`.

3. If the certificate is in `FAILED` status (expired before renewal):
   ```bash
   # Request a new certificate
   aws acm request-certificate \
     --domain-name kira.abodeab.com \
     --subject-alternative-names "*.kira.abodeab.com" \
     --validation-method DNS \
     --region ap-south-1
   ```
   Then add DNS validation records and update the ALB listener's `certificate_arn` in Terraform.

:::tip ACM auto-renewal requires DNS records to stay intact
Never delete the `_acme-challenge.*` CNAME records from Route 53. If you need to re-create the hosted zone, export the DNS records first.
:::
