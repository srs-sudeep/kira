"""Custom Prometheus metrics for the reservation-service.

Import and increment these at the appropriate points in service logic.
Example usage in reservation_service.py:

    from app.metrics import reservations_created_total, reservation_processing_duration
    import time

    start = time.perf_counter()
    reservation = await self.repo.create(data)
    reservations_created_total.labels(source=data.source or "direct").inc()
    reservation_processing_duration.labels(operation="create").observe(
        time.perf_counter() - start
    )
"""

from prometheus_client import Counter, Histogram

# ── Reservation lifecycle ─────────────────────────────────────────────────────

reservations_created_total = Counter(
    "reservations_created_total",
    "Total reservations created, labelled by source channel.",
    ["source"],  # booking_com | expedia | mmt | direct | phone | walk_in
)

reservations_modified_total = Counter(
    "reservations_modified_total",
    "Total reservation modifications (date changes, room upgrades, etc.).",
    ["source"],
)

reservations_cancelled_total = Counter(
    "reservations_cancelled_total",
    "Total reservations cancelled.",
    ["source", "reason"],  # reason: guest_request | no_show | overbooking | system
)

reservations_checked_in_total = Counter(
    "reservations_checked_in_total",
    "Total check-ins processed.",
    ["source"],
)

reservations_checked_out_total = Counter(
    "reservations_checked_out_total",
    "Total check-outs processed.",
    ["source"],
)

# ── Processing duration ───────────────────────────────────────────────────────

reservation_processing_duration = Histogram(
    "reservation_processing_duration_seconds",
    "Time to complete a reservation operation (DB write + Kafka publish).",
    ["operation"],  # create | modify | cancel | check_in | check_out
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

# ── Duplicate detection ───────────────────────────────────────────────────────

duplicate_reservation_blocks = Counter(
    "duplicate_reservation_blocks_total",
    "Times a duplicate reservation was detected and blocked.",
    ["source"],
)

# ── Guest profiles ────────────────────────────────────────────────────────────

guest_profiles_created_total = Counter(
    "guest_profiles_created_total",
    "New guest profiles created (vs. matched to existing profile).",
)

guest_profiles_matched_total = Counter(
    "guest_profiles_matched_total",
    "Reservations matched to an existing guest profile via email hash.",
)
