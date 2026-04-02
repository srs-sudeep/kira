"""Pydantic v2 schemas for inventory history log."""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class InventoryHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    room_type_id: uuid.UUID
    rate_plan_id: uuid.UUID
    date: date
    field_changed: str
    old_value: str | None
    new_value: str | None
    changed_by: uuid.UUID
    changed_at: datetime


class InventoryHistoryListResponse(BaseModel):
    items: list[InventoryHistoryResponse]
    total: int
    page: int
    page_size: int
    pages: int


class InventoryHistoryQuery(BaseModel):
    room_type_id: uuid.UUID | None = None
    rate_plan_id: uuid.UUID | None = None
    date_from: date | None = None
    date_to: date | None = None
    changed_by: uuid.UUID | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
