"""Pydantic v2 schemas for reservations."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.guest import GuestBrief, GuestCreate, GuestResponse
from app.schemas.note import NoteResponse

ReservationStatus = Literal[
    "confirmed", "modified", "cancelled", "no_show", "checked_in", "checked_out"
]
ReservationSource = Literal[
    "booking_com", "expedia", "makemytrip", "airbnb", "agoda",
    "direct", "manual", "phone",
]


# ── Write requests ────────────────────────────────────────────────────────────

class ReservationCreate(BaseModel):
    """Payload for a manual (walk-in / phone) booking."""

    room_type_id: uuid.UUID
    rate_plan_id: uuid.UUID
    check_in: date
    check_out: date
    source: ReservationSource = "manual"
    channel_id: uuid.UUID | None = None
    adults: int = Field(1, ge=1)
    children: int = Field(0, ge=0)
    special_requests: str | None = None
    guest: GuestCreate

    @model_validator(mode="after")
    def dates_valid(self) -> "ReservationCreate":
        if self.check_out <= self.check_in:
            raise ValueError("check_out must be after check_in.")
        return self


class ReservationModify(BaseModel):
    """All fields optional — only provided fields are updated."""

    check_in: date | None = None
    check_out: date | None = None
    room_type_id: uuid.UUID | None = None
    rate_plan_id: uuid.UUID | None = None
    adults: int | None = Field(default=None, ge=1)
    children: int | None = Field(default=None, ge=0)
    special_requests: str | None = None

    @model_validator(mode="after")
    def dates_valid(self) -> "ReservationModify":
        if self.check_in and self.check_out and self.check_out <= self.check_in:
            raise ValueError("check_out must be after check_in.")
        return self


class ReservationCancel(BaseModel):
    cancellation_reason: str = Field(min_length=1, max_length=500)


class ReservationStatusUpdate(BaseModel):
    status: Literal["no_show", "checked_in", "checked_out"]


# ── Response schemas ──────────────────────────────────────────────────────────

class ReservationBrief(BaseModel):
    """Summary row for the unified inbox."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    confirmation_number: str
    source: str
    channel_id: uuid.UUID | None
    room_type_id: uuid.UUID
    rate_plan_id: uuid.UUID
    check_in: date
    check_out: date
    nights: int
    adults: int
    children: int
    total_amount: Decimal
    currency: str
    status: str
    special_requests: str | None
    guest: GuestBrief
    created_at: datetime


class ReservationDetail(BaseModel):
    """Full reservation with decrypted guest PII and notes."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    confirmation_number: str
    source: str
    channel_id: uuid.UUID | None
    channel_reservation_id: str | None
    room_type_id: uuid.UUID
    rate_plan_id: uuid.UUID
    check_in: date
    check_out: date
    nights: int
    adults: int
    children: int
    total_amount: Decimal
    currency: str
    status: str
    cancellation_policy: dict[str, Any] | None
    cancelled_at: datetime | None
    cancellation_reason: str | None
    special_requests: str | None
    guest: GuestResponse
    notes: list[NoteResponse]
    created_at: datetime
    updated_at: datetime


class ReservationInboxResponse(BaseModel):
    items: list[ReservationBrief]
    total: int
    page: int
    page_size: int
    pages: int


class DuplicateGroup(BaseModel):
    email_hash: str
    room_type_id: uuid.UUID
    reservations: list[ReservationBrief]


class DuplicatesResponse(BaseModel):
    groups: list[DuplicateGroup]
    total_duplicates: int


# ── Query / filter params ─────────────────────────────────────────────────────

class InboxFilters(BaseModel):
    status: list[str] | None = None
    source: list[str] | None = None
    channel_id: uuid.UUID | None = None
    check_in_from: date | None = None
    check_in_to: date | None = None
    check_out_from: date | None = None
    check_out_to: date | None = None
    guest_query: str | None = None  # searches first_name/last_name or email_hash
    sort_by: Literal["check_in", "created_at", "total_amount", "confirmation_number"] = "created_at"
    sort_dir: Literal["asc", "desc"] = "desc"
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
