"""Pydantic v2 schemas for audit event queries and responses."""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditEventResponse(BaseModel):
    """Serialised representation of a single audit_events row."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID | None
    user_id: uuid.UUID | None
    action: str
    resource_type: str | None
    resource_id: str | None
    before_state: dict[str, Any] | None
    after_state: dict[str, Any] | None
    ip_address: str | None
    user_agent: str | None
    # Exposed as 'metadata' in the API even though the ORM attribute is 'event_metadata'
    event_metadata: dict[str, Any] | None = Field(None, serialization_alias="metadata")
    created_at: datetime


class AuditEventListResponse(BaseModel):
    """Paginated audit event list."""

    model_config = ConfigDict(from_attributes=True)

    items: list[AuditEventResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AuditFilterParams(BaseModel):
    """Query-parameter schema for GET /audit-events.

    Router should unpack this via `Depends(AuditFilterParams)` using FastAPI's
    query-param injection so each field maps to a URL query string.
    """

    tenant_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    action: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    # ISO-8601 datetime bounds; both are inclusive
    from_dt: datetime | None = Field(None, alias="from")
    to_dt: datetime | None = Field(None, alias="to")
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
