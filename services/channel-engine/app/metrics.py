"""Custom Prometheus metrics for the channel-engine service.

Import and increment these counters/histograms/gauges at the appropriate
points in service logic. Example usage in sync_service.py:

    from app.metrics import channel_sync_total, channel_sync_duration
    import time

    start = time.perf_counter()
    try:
        await self._push_to_ota(channel, ari_data)
        channel_sync_total.labels(ota=channel.ota, status="success").inc()
    except Exception as exc:
        channel_sync_total.labels(ota=channel.ota, status="failed").inc()
        channel_sync_failures.labels(ota=channel.ota, error_type=type(exc).__name__).inc()
        raise
    finally:
        channel_sync_duration.labels(ota=channel.ota).observe(time.perf_counter() - start)
"""

from prometheus_client import Counter, Gauge, Histogram

# ── Sync operations ───────────────────────────────────────────────────────────

channel_sync_total = Counter(
    "channel_sync_total",
    "Total channel sync operations attempted.",
    ["ota", "status"],  # ota: booking_com | expedia | mmt; status: success | failed
)

channel_sync_duration = Histogram(
    "channel_sync_duration_seconds",
    "End-to-end duration of a channel sync operation (from task start to OTA response).",
    ["ota"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

channel_sync_failures = Counter(
    "channel_sync_failures_total",
    "Total channel sync failures, labelled by OTA and Python exception type.",
    ["ota", "error_type"],  # error_type: TimeoutError | HTTPStatusError | ChannelSyncError
)

# ── ARI push ──────────────────────────────────────────────────────────────────

ari_push_total = Counter(
    "ari_push_total",
    "Total ARI (availability/rate/inventory) push operations to each OTA.",
    ["ota"],
)

ari_push_duration = Histogram(
    "ari_push_duration_seconds",
    "Duration of a single ARI push to an OTA API.",
    ["ota"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
)

# ── Circuit breaker ───────────────────────────────────────────────────────────

circuit_breaker_state = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state per channel: 0=closed (healthy), 1=open (failing).",
    ["channel_id", "ota"],
)

# ── Active channels ───────────────────────────────────────────────────────────

active_channels = Gauge(
    "active_channels",
    "Number of currently active (enabled, circuit closed) channel connections per OTA.",
    ["ota"],
)

# ── Kafka consumer ────────────────────────────────────────────────────────────

ari_events_consumed = Counter(
    "ari_events_consumed_total",
    "Total ari.updated Kafka events consumed by the channel-engine.",
    ["tenant_id"],
)

ari_events_processing_duration = Histogram(
    "ari_events_processing_duration_seconds",
    "Time to process a single ari.updated event (from consumer receive to all OTA pushes dispatched).",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
)
