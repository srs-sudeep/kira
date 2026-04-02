"""Custom Prometheus metrics for the notification-service.

Import and increment in notification_service.py after send operations.
Example usage:

    from app.metrics import notifications_sent_total, notifications_failed_total

    try:
        await self._send_email(recipient, template, context)
        notifications_sent_total.labels(type=notification_type, channel="email").inc()
    except Exception as exc:
        notifications_failed_total.labels(
            type=notification_type,
            channel="email",
            error=type(exc).__name__,
        ).inc()
        raise
"""

from prometheus_client import Counter, Gauge, Histogram

# ── Sent / failed ─────────────────────────────────────────────────────────────

notifications_sent_total = Counter(
    "notifications_sent_total",
    "Total notifications successfully sent.",
    ["type", "channel"],
    # type:    new_booking | cancellation | modification | channel_failure |
    #          payment_reminder | check_in_reminder
    # channel: email | in_app
)

notifications_failed_total = Counter(
    "notifications_failed_total",
    "Total notification delivery failures.",
    ["type", "channel", "error"],
    # error: SendGridError | SMTPError | TimeoutError | InvalidEmail | ...
)

# ── Delivery duration ─────────────────────────────────────────────────────────

notification_delivery_duration = Histogram(
    "notification_delivery_duration_seconds",
    "Time from notification creation to successful delivery confirmation.",
    ["type", "channel"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

# ── Queue / backlog ───────────────────────────────────────────────────────────

notification_queue_depth = Gauge(
    "notification_queue_depth",
    "Approximate number of pending notifications in the processing queue.",
    ["type"],
)

# ── Kafka consumer ────────────────────────────────────────────────────────────

notification_events_consumed = Counter(
    "notification_events_consumed_total",
    "Total Kafka events consumed by the notification-service.",
    ["topic"],  # reservation.created | reservation.cancelled | channel.sync.failed
)

notification_events_processing_duration = Histogram(
    "notification_events_processing_duration_seconds",
    "Time to process a Kafka event and dispatch the resulting notification.",
    ["topic"],
    buckets=[0.05, 0.1, 0.5, 1.0, 5.0],
)

# ── Preferences ──────────────────────────────────────────────────────────────

notifications_suppressed_total = Counter(
    "notifications_suppressed_total",
    "Notifications suppressed due to user preferences (opted out).",
    ["type", "channel"],
)
