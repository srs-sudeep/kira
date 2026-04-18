"""Pydantic v2 schemas for sync logs."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class SyncLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    channel_id: uuid.UUID
    event_type: str
    direction: str
    payload_hash: str | None
    request_summary: dict[str, Any] | None
    response_status: int | None
    response_summary: dict[str, Any] | None
    retry_count: int
    status: str
    created_at: datetime


class SyncLogPageResponse(BaseModel):
    items: list[SyncLogResponse]
    total: int
    page: int
    page_size: int
    pages: int
