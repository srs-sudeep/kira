"""Pydantic v2 schemas for channel mappings."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MappingCreate(BaseModel):
    internal_room_type_id: uuid.UUID
    ota_room_type_id: str = Field(min_length=1, max_length=100)
    internal_rate_plan_id: uuid.UUID
    ota_rate_plan_id: str = Field(min_length=1, max_length=100)


class MappingUpdate(BaseModel):
    ota_room_type_id: str | None = Field(default=None, min_length=1, max_length=100)
    ota_rate_plan_id: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None


class MappingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    channel_id: uuid.UUID
    internal_room_type_id: uuid.UUID
    ota_room_type_id: str
    internal_rate_plan_id: uuid.UUID
    ota_rate_plan_id: str
    is_active: bool
    created_at: datetime


class MappingListResponse(BaseModel):
    items: list[MappingResponse]
    total: int
