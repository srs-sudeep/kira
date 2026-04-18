"""Pydantic v2 schemas for notification preferences."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    event_type: str
    email_enabled: bool
    in_app_enabled: bool
    updated_at: datetime


class PreferenceUpsert(BaseModel):
    """Single event-type preference to create or update."""

    event_type: str
    email_enabled: bool = True
    in_app_enabled: bool = True


class PreferencesUpdateRequest(BaseModel):
    """Batch upsert — pass one or many preferences at once."""

    preferences: list[PreferenceUpsert]


class PreferencesListResponse(BaseModel):
    user_id: uuid.UUID
    items: list[PreferenceResponse]
