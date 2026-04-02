---
title: Alerting
description: Alert rules, PagerDuty and OpsGenie integration, and escalation policy for KIRA production.
sidebar_position: 3
---

# Alerting

**What you'll learn:**
- The full alert catalogue with conditions and severities
- How Alertmanager routes alerts to PagerDuty or OpsGenie
- The escalation policy for critical vs. warning alerts

---

## Alert Rules

Alert rules are defined in Prometheus (YAML files loaded by Alertmanager). They evaluate against metrics every 15 seconds.

### Service Health

```yaml
groups:
  - name: kira.service_health
    rules:
      - alert: ServiceDown
        expr: up{job=~".*-service|channel-engine"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "{{ $labels.job }} is down"
          description: "Prometheus cannot scrape {{ $labels.job }} for 2 minutes."

      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{status=~"5.."}[5m])
          / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High 5xx error rate on {{ $labels.job }}"
          description: "Error rate is {{ $value | humanizePercentage }} over the last 5 minutes."

      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            rate(http_request_duration_seconds_bucket[5m])
          ) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "p95 latency > 2s on {{ $labels.job }}"
```

### Channel Sync

```yaml
  - name: kira.channel_sync
    rules:
      - alert: ChannelCircuitOpen
        expr: circuit_breaker_state{job="channel-engine"} == 1
        for: 0m
        labels:
          severity: warning
        annotations:
          summary: "Circuit breaker open for channel {{ $labels.channel_id }}"
          description: "OTA sync has failed {{ $value }} consecutive times. Auto-recovery in 5 minutes."

      - alert: ChannelSyncFailingLong
        expr: |
          rate(channel_sync_total{status="failed"}[30m])
          / rate(channel_sync_total[30m]) > 0.5
        for: 30m
        labels:
          severity: critical
        annotations:
          summary: "Channel sync failure rate > 50% for 30 minutes"
          description: "Channel {{ $labels.channel_id }} ({{ $labels.ota }}) has > 50% failure rate."
```

### Kafka

```yaml
  - name: kira.kafka
    rules:
      - alert: KafkaConsumerLagHigh
        expr: kafka_consumer_lag > 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Consumer lag > 1000 on {{ $labels.topic }}"
          description: "Consumer group {{ $labels.group }} is {{ $value }} messages behind on {{ $labels.topic }}."

      - alert: KafkaConsumerLagCritical
        expr: kafka_consumer_lag > 10000
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Consumer lag > 10,000 on {{ $labels.topic }}"
```

### Infrastructure

```yaml
  - name: kira.infrastructure
    rules:
      - alert: HighCPU
        expr: |
          rate(container_cpu_usage_seconds_total{namespace="kira"}[5m]) > 0.8
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "CPU > 80% on pod {{ $labels.pod }}"

      - alert: HighMemory
        expr: |
          container_memory_working_set_bytes{namespace="kira"}
          / container_spec_memory_limit_bytes{namespace="kira"} > 0.85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Memory > 85% on pod {{ $labels.pod }}"

      - alert: DiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.15
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk space < 15% on {{ $labels.instance }}"

      - alert: DiskSpaceCritical
        expr: |
          (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.05
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Disk space < 5% on {{ $labels.instance }}"

      - alert: SSLCertExpiringSoon
        expr: probe_ssl_earliest_cert_expiry - time() < 86400 * 14
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "SSL certificate expires in < 14 days"
```

---

## Alert Severity Levels

| Severity | Meaning | Response time |
|---|---|---|
| `critical` | Production is down or severely degraded | Immediate (PagerDuty call) |
| `warning` | Degraded performance or imminent failure | Within 4 hours (OpsGenie ticket) |
| `info` | Noteworthy but no action required | Review during business hours |

---

## Alertmanager Configuration

Alertmanager routes alerts based on severity:

```yaml
# observability/alertmanager/alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: [alertname, job]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: default

  routes:
    - match:
        severity: critical
      receiver: pagerduty
      repeat_interval: 1h

    - match:
        severity: warning
      receiver: opsgenie
      repeat_interval: 4h

receivers:
  - name: default
    slack_configs:
      - api_url: $SLACK_WEBHOOK_URL
        channel: '#kira-alerts'

  - name: pagerduty
    pagerduty_configs:
      - service_key: $PAGERDUTY_SERVICE_KEY
        severity: critical
    slack_configs:
      - api_url: $SLACK_WEBHOOK_URL
        channel: '#kira-incidents'

  - name: opsgenie
    opsgenie_configs:
      - api_key: $OPSGENIE_API_KEY
        teams: [kira-oncall]
        priority: P3
    slack_configs:
      - api_url: $SLACK_WEBHOOK_URL
        channel: '#kira-alerts'

inhibit_rules:
  # If a service is completely down, suppress its error rate alert
  - source_match:
      alertname: ServiceDown
    target_match:
      alertname: HighErrorRate
    equal: [job]
```

---

## PagerDuty Integration

1. In PagerDuty, create a new service: **KIRA Production**
2. Add an integration: select **Prometheus** → copy the integration key
3. Set the integration key as `$PAGERDUTY_SERVICE_KEY` in Alertmanager config (via K8s secret)

PagerDuty will call the on-call engineer for any `critical` alert. The on-call schedule rotates weekly.

---

## OpsGenie Integration

1. In OpsGenie, create a team: `kira-oncall`
2. Create an API integration and copy the API key
3. Set as `$OPSGENIE_API_KEY` in Alertmanager config

Warning alerts create OpsGenie tickets assigned to the `kira-oncall` team. These appear in the OpsGenie web interface and mobile app. They do not call anyone.

---

## Escalation Policy

```
Fired → Alertmanager routes by severity
  │
  ├─ critical → PagerDuty
  │    ├─ 0 min  → On-call engineer notified (push + call)
  │    ├─ 5 min  → If not acknowledged → call again
  │    ├─ 15 min → If not acknowledged → escalate to tech lead
  │    └─ 30 min → If not acknowledged → escalate to engineering manager
  │
  └─ warning → OpsGenie
       ├─ Ticket created, assigned to kira-oncall team
       └─ Unacked after 4h → re-notify + bump priority
```

---

## Silencing Alerts During Maintenance

When performing planned maintenance (e.g., applying K8s manifests, running migrations):

1. Open Alertmanager UI: `https://alertmanager.kira.abodeab.com` (or `http://localhost:9093` locally)
2. Click **New Silence**
3. Set matcher: `job=~".*"` and your maintenance window duration
4. Add a comment explaining the reason

Or via CLI:

```bash
# Silence all alerts for 30 minutes
curl -XPOST http://localhost:9093/api/v2/silences \
  -H 'Content-Type: application/json' \
  -d '{
    "matchers": [{"name": "job", "value": ".*", "isRegex": true}],
    "startsAt": "2026-04-02T10:00:00Z",
    "endsAt": "2026-04-02T10:30:00Z",
    "createdBy": "your-name",
    "comment": "Planned migration deployment"
  }'
```
