"""Pydantic v2 schemas for blackout dates."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class BlackoutDateCreate(BaseModel):
    date: date
    reason: str | None = None


class BlackoutDateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    date: date
    reason: str | None
    created_at: datetime


class BlackoutDateListResponse(BaseModel):
    items: list[BlackoutDateResponse]
    total: int
