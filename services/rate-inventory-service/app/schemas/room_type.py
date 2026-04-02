"""Pydantic v2 schemas for room types."""
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

BeddingType = Literal["single", "double", "twin", "king", "queen", "mixed"]


class RoomTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    max_occupancy: int = Field(2, ge=1)
    default_occupancy: int = Field(2, ge=1)
    bedding_type: BeddingType | None = None
    amenities: list[Any] = Field(default_factory=list)
    images: list[Any] = Field(default_factory=list)
    physical_inventory: int = Field(0, ge=0)
    sort_order: int = Field(0, ge=0)


class RoomTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    max_occupancy: int | None = Field(default=None, ge=1)
    default_occupancy: int | None = Field(default=None, ge=1)
    bedding_type: BeddingType | None = None
    amenities: list[Any] | None = None
    images: list[Any] | None = None
    physical_inventory: int | None = Field(default=None, ge=0)
    sort_order: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class RoomTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    max_occupancy: int
    default_occupancy: int
    bedding_type: str | None
    amenities: list[Any]
    images: list[Any]
    physical_inventory: int
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RoomTypeListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[RoomTypeResponse]
    total: int
    page: int
    page_size: int
    pages: int
