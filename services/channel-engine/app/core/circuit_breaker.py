"""Circuit breaker logic for OTA channels.

A channel trips open after CIRCUIT_BREAKER_THRESHOLD consecutive failures.
Tripped channels are marked status='error' and skipped during ARI pushes.
Recovery is manual (PATCH /channels/{id}) or automatic after AUTO_RECOVERY_MINUTES.

This module only contains the threshold check helpers; state is persisted on the
Channel.consecutive_failures and Channel.status DB columns — not in memory — so
it works correctly across multiple Celery workers.
"""
from app.config import settings

CIRCUIT_BREAKER_THRESHOLD: int = settings.circuit_breaker_threshold
AUTO_RECOVERY_MINUTES: int = 5


def is_tripped(consecutive_failures: int) -> bool:
    """Return True if the channel circuit breaker should be open."""
    return consecutive_failures >= CIRCUIT_BREAKER_THRESHOLD
