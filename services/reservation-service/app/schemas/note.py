"""Pydantic v2 schemas for reservation notes."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    content: str = Field(min_length=1)


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reservation_id: uuid.UUID
    user_id: uuid.UUID
    content: str
    created_at: datetime
