"""Pydantic v2 schemas for guest profiles."""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GuestCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str | None = None
    phone: str | None = None
    nationality: str | None = Field(default=None, min_length=2, max_length=3)
    preferences: dict[str, Any] = Field(default_factory=dict)


class GuestUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = None
    phone: str | None = None
    nationality: str | None = Field(default=None, min_length=2, max_length=3)
    preferences: dict[str, Any] | None = None


class GuestBrief(BaseModel):
    """Compact guest representation for inbox/list views — no PII."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str


class GuestResponse(BaseModel):
    """Full guest record with decrypted PII — returned in reservation detail."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    # Decrypted by service layer before constructing this schema
    email: str | None
    phone: str | None
    nationality: str | None
    preferences: dict[str, Any]
    created_at: datetime
    updated_at: datetime
