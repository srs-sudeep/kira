---
title: Logging
description: Structured JSON logging with structlog, log aggregation with Loki and CloudWatch, and how to search logs in Grafana.
sidebar_position: 2
---

# Logging

**What you'll learn:**
- How KIRA services produce structured JSON logs via structlog
- How Promtail ships logs to Loki locally, and how CloudWatch collects them in production
- How to search and filter logs in Grafana
- Log levels and when each is appropriate

---

## Structured JSON Logging

All KIRA services use [structlog](https://www.structlog.org/) to emit structured JSON logs. Every log line is a JSON object, never a plain string.

### Why structured logging

Plain string logs like `"User 123 logged in"` are hard to query. A structured log:

```json
{
  "timestamp": "2026-04-02T10:23:45.123Z",
  "level": "info",
  "event": "user_login",
  "service": "identity-service",
  "tenant_id": "t_abc123",
  "user_id": "u_456def",
  "ip": "203.0.113.42",
  "duration_ms": 34
}
```

This is filterable, aggregatable, and alertable on any field.

### structlog configuration

Each service configures structlog in `app/main.py`:

```python
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)
```

In test/dev environments, `ConsoleRenderer` is used instead of `JSONRenderer` for human-readable output.

### Emitting a log

```python
import structlog

logger = structlog.get_logger()

async def create_reservation(data: ReservationCreate, tenant_id: str) -> Reservation:
    logger.info(
        "reservation_create_started",
        tenant_id=tenant_id,
        room_type_id=str(data.room_type_id),
        check_in=str(data.check_in),
    )
    reservation = await reservation_repo.create(data)
    logger.info(
        "reservation_created",
        reservation_id=str(reservation.id),
        source=reservation.source,
    )
    return reservation
```

:::danger No print() statements
`print()` bypasses structlog and produces unstructured output that cannot be aggregated or queried. Use `logger.info()`, `logger.warning()`, `logger.error()` everywhere.
:::

### Binding context variables

Use `structlog.contextvars` to bind fields that should appear on every log line within a request:

```python
from structlog.contextvars import bind_contextvars, clear_contextvars

# In middleware, after JWT validation:
bind_contextvars(
    tenant_id=request.state.tenant_id,
    user_id=request.state.user_id,
    request_id=request.headers.get("X-Request-ID"),
)
```

Once bound, every log call within that request automatically includes `tenant_id`, `user_id`, and `request_id`.

---

## Log Levels

| Level | When to use | Example |
|---|---|---|
| `DEBUG` | Detailed diagnostic info — disabled in production | SQL query params, Kafka message body |
| `INFO` | Normal operations — one line per significant action | reservation created, user logged in, sync started |
| `WARNING` | Unexpected but recoverable — worth investigating | retry attempt, slow query (>500ms), missing optional config |
| `ERROR` | Operation failed — needs attention | OTA API returned 500, Kafka publish failed after retries |
| `CRITICAL` | System is unusable — immediate action required | Database unreachable, decryption key missing |

In production, `LOG_LEVEL=INFO` is set in the ConfigMap. `DEBUG` logs are never written to production.

---

## Local Log Aggregation (Loki + Grafana Alloy)

When running with `docker-compose.observability.yml`, **Grafana Alloy** collects container logs and ships them to Loki. (Promtail reached **end of life** in March 2026; Alloy is the supported agent.)

```
Docker API (containers) → Grafana Alloy → Loki → Grafana
```

Alloy config lives at `observability/alloy/config.alloy` (River). It discovers Compose project `kira`, adds labels `container`, `service`, and `project`, parses JSON `structlog` lines (level / event / timestamp), normalises `warn` → `warning`, and drops `debug` lines (same behaviour as the former Promtail pipeline). Alloy’s debug UI: `http://localhost:12345`.

### Searching logs in Grafana (Loki)

1. Open Grafana at `http://localhost:3001`
2. Click **Explore** → select data source **Loki**
3. Use LogQL to filter:

```logql
# All logs from identity-service
{service="identity-service"}

# ERROR logs from any service
{service=~".+"} |= `"level":"error"`

# Logs for a specific tenant
{service="reservation-service"} | json | tenant_id="t_abc123"

# Failed sync events in channel-engine
{service="channel-engine"} | json | event="channel_sync_failed"
```

4. Switch to **Table** view to see parsed JSON fields as columns

---

## Production Log Aggregation (CloudWatch)

In production (EKS), the Fluent Bit DaemonSet (part of the AWS EKS add-on) ships container logs to CloudWatch Logs.

Log group structure:

```
/kira/production/identity-service
/kira/production/rate-inventory-service
/kira/production/channel-engine
... (one group per service)
```

### Searching in CloudWatch Logs Insights

```sql
-- Find all errors in the last hour
fields @timestamp, event, tenant_id, user_id, @message
| filter level = "error"
| sort @timestamp desc
| limit 50

-- Reservation creation latency by tenant
fields @timestamp, tenant_id, duration_ms
| filter event = "reservation_created"
| stats avg(duration_ms), p95(duration_ms) by tenant_id

-- Channel sync failures today
fields @timestamp, channel_id, ota, error
| filter event = "channel_sync_failed"
| sort @timestamp desc
```

:::tip Correlate with Grafana
The Grafana CloudWatch datasource can query CloudWatch Logs Insights directly. Add `CloudWatch` as a datasource in Grafana and use it alongside Prometheus metrics in the same dashboard.
:::

---

## Request ID Tracing

Every request that passes through Kong gets an `X-Request-ID` header (UUID). Services bind this to structlog context:

```python
request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
bind_contextvars(request_id=request_id)
```

To trace a full request chain across services:

```logql
# In Grafana/Loki — find all logs for request ID abc123
{service=~".+"} | json | request_id="abc-123-..."
```

This is especially useful for debugging a reservation creation that triggered ARI updates and a sync across multiple services.

---

## Log Retention

| Environment | Retention | Storage |
|---|---|---|
| Local dev | Until `docker compose down -v` | Loki volume |
| Staging (CloudWatch) | 7 days | CloudWatch Logs |
| Production (CloudWatch) | 90 days | CloudWatch Logs |

Production logs older than 90 days are expired automatically via CloudWatch log group retention policy (set in Terraform).
