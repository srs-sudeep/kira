"""Pydantic v2 schemas for channels."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

OtaCode = Literal[
    "booking_com",
    "expedia",
    "makemytrip",
    "airbnb",
    "agoda",
    "tripadvisor",
    "hotelbeds",
]
ChannelStatus = Literal["connected", "disconnected", "error", "pending_certification"]


# ── Write requests ────────────────────────────────────────────────────────────


class ChannelCreate(BaseModel):
    ota_code: OtaCode
    display_name: str = Field(min_length=1, max_length=255)
    credentials: dict[str, Any]  # API keys, hotel_id, etc. — encrypted before storage
    config: dict[str, Any] = Field(default_factory=dict)


class ChannelUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    credentials: dict[str, Any] | None = None
    config: dict[str, Any] | None = None
    is_active: bool | None = None


# ── Response schemas ──────────────────────────────────────────────────────────


class ChannelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ota_code: str
    display_name: str
    status: str
    last_sync_at: datetime | None
    error_message: str | None
    consecutive_failures: int
    config: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ChannelListResponse(BaseModel):
    items: list[ChannelResponse]
    total: int


class ChannelHealthItem(BaseModel):
    id: uuid.UUID
    display_name: str
    ota_code: str
    status: str
    last_sync_at: datetime | None
    consecutive_failures: int
    is_active: bool


class HealthDashboardResponse(BaseModel):
    total: int
    connected: int
    error: int
    disconnected: int
    pending_certification: int
    channels: list[ChannelHealthItem]


class SyncTriggeredResponse(BaseModel):
    channel_id: uuid.UUID
    message: str
    task_id: str | None = None
