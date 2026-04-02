"""KIRA shared Kafka event schemas — used by producers and consumers across services."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class KiraEvent(BaseModel):
    """Base envelope for all KIRA Kafka events."""

    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str
    tenant_id: uuid.UUID
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any]


# ---------------------------------------------------------------------------
# ARI events (published by rate-inventory-service)
# ---------------------------------------------------------------------------

class ARIUpdatedPayload(BaseModel):
    room_type_id: uuid.UUID
    rate_plan_id: uuid.UUID
    date_from: str  # ISO-8601 date
    date_to: str
    rate: float
    availability: int


class ARIUpdatedEvent(KiraEvent):
    event_type: str = "ari.updated"
    payload: ARIUpdatedPayload  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Reservation events (published by reservation-service)
# ---------------------------------------------------------------------------

class ReservationCreatedPayload(BaseModel):
    reservation_id: uuid.UUID
    channel: str
    room_type_id: uuid.UUID
    rate_plan_id: uuid.UUID
    check_in: str
    check_out: str
    guest_name: str
    total_amount: float


class ReservationCreatedEvent(KiraEvent):
    event_type: str = "reservation.created"
    payload: ReservationCreatedPayload  # type: ignore[assignment]


class ReservationCancelledPayload(BaseModel):
    reservation_id: uuid.UUID
    channel: str
    cancelled_at: datetime
    reason: str | None = None


class ReservationCancelledEvent(KiraEvent):
    event_type: str = "reservation.cancelled"
    payload: ReservationCancelledPayload  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Channel sync events (published by channel-engine)
# ---------------------------------------------------------------------------

class ChannelSyncFailedPayload(BaseModel):
    channel: str
    room_type_id: uuid.UUID | None = None
    error_code: str
    error_message: str
    retry_count: int = 0


class ChannelSyncFailedEvent(KiraEvent):
    event_type: str = "channel.sync.failed"
    payload: ChannelSyncFailedPayload  # type: ignore[assignment]
