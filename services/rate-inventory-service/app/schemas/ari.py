"""Pydantic v2 schemas for ARI calendar operations."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ARICell(BaseModel):
    """Single ARI snapshot cell as returned in the calendar grid."""

    model_config = ConfigDict(from_attributes=True)

    available_rooms: int
    rate_amount: Decimal
    is_closed: bool
    cta_closed: bool
    ctd_closed: bool
    min_los: int
    max_los: int
    overbooking_buffer: int
    updated_at: datetime


class ARIRatePlanRow(BaseModel):
    rate_plan_id: uuid.UUID
    rate_plan_name: str
    plan_type: str
    base_amount: Decimal
    # keyed by ISO date string ("2024-01-01")
    cells: dict[str, ARICell]


class ARIRoomTypeRow(BaseModel):
    room_type_id: uuid.UUID
    room_type_name: str
    physical_inventory: int
    rate_plans: list[ARIRatePlanRow]


class ARICalendarResponse(BaseModel):
    start_date: date
    end_date: date
    dates: list[str]  # ordered ISO date strings in the range
    room_types: list[ARIRoomTypeRow]


# ── Write requests ────────────────────────────────────────────────────────────

class ARICellUpdate(BaseModel):
    """Update payload for a single (room_type, rate_plan, date) cell."""

    room_type_id: uuid.UUID
    rate_plan_id: uuid.UUID
    date: date
    available_rooms: int | None = Field(default=None, ge=0)
    rate_amount: Decimal | None = Field(default=None, gt=0)
    is_closed: bool | None = None
    cta_closed: bool | None = None
    ctd_closed: bool | None = None
    min_los: int | None = Field(default=None, ge=1)
    max_los: int | None = Field(default=None, ge=1)
    overbooking_buffer: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "ARICellUpdate":
        fields = [
            self.available_rooms, self.rate_amount, self.is_closed,
            self.cta_closed, self.ctd_closed, self.min_los, self.max_los,
            self.overbooking_buffer,
        ]
        if all(f is None for f in fields):
            raise ValueError("At least one field must be provided for an ARI cell update.")
        return self


class ARICalendarPutRequest(BaseModel):
    cells: list[ARICellUpdate] = Field(min_length=1)


class BulkUpdateRequest(BaseModel):
    """Apply the same field values across a date range for multiple room/rate combinations."""

    room_type_ids: list[uuid.UUID] = Field(min_length=1)
    rate_plan_ids: list[uuid.UUID] = Field(min_length=1)
    start_date: date
    end_date: date
    available_rooms: int | None = Field(default=None, ge=0)
    rate_amount: Decimal | None = Field(default=None, gt=0)
    is_closed: bool | None = None
    cta_closed: bool | None = None
    ctd_closed: bool | None = None
    min_los: int | None = Field(default=None, ge=1)
    max_los: int | None = Field(default=None, ge=1)
    overbooking_buffer: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def date_range_valid(self) -> "BulkUpdateRequest":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be >= start_date.")
        return self

    @model_validator(mode="after")
    def at_least_one_update_field(self) -> "BulkUpdateRequest":
        fields = [
            self.available_rooms, self.rate_amount, self.is_closed,
            self.cta_closed, self.ctd_closed, self.min_los, self.max_los,
            self.overbooking_buffer,
        ]
        if all(f is None for f in fields):
            raise ValueError("At least one update field is required.")
        return self


class StopSellRequest(BaseModel):
    """Close all specified room/rate combinations for a date range."""

    room_type_ids: list[uuid.UUID] = Field(min_length=1)
    # None = apply to all rate plans under these room types
    rate_plan_ids: list[uuid.UUID] | None = None
    start_date: date
    end_date: date
    cta_closed: bool = False
    ctd_closed: bool = False

    @model_validator(mode="after")
    def date_range_valid(self) -> "StopSellRequest":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be >= start_date.")
        return self


class ARISnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    room_type_id: uuid.UUID
    rate_plan_id: uuid.UUID
    date: date
    available_rooms: int
    rate_amount: Decimal
    is_closed: bool
    cta_closed: bool
    ctd_closed: bool
    min_los: int
    max_los: int
    overbooking_buffer: int
    updated_at: datetime


class BulkUpdateResponse(BaseModel):
    updated_cells: int
    start_date: date
    end_date: date
