"""Pydantic v2 schemas for user management."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.schemas.email_types import LooseEmailStr

UserRole = Literal[
    "super_admin",
    "property_owner",
    "revenue_manager",
    "front_desk",
    "read_only",
]


class UserBrief(BaseModel):
    """Compact user representation used in nested/list contexts."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    role: UserRole


class UserResponse(BaseModel):
    """Full user record returned to API consumers."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    role: UserRole
    tenant_id: uuid.UUID | None
    is_active: bool
    mfa_enabled: bool
    last_login_at: datetime | None
    failed_login_attempts: int
    locked_until: datetime | None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class UserListResponse(BaseModel):
    """Paginated wrapper for user queries."""

    model_config = ConfigDict(from_attributes=True)

    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    pages: int


class InviteUserRequest(BaseModel):
    email: LooseEmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: UserRole
    # Inviting super_admin omits tenant_id; all other roles require it
    tenant_id: uuid.UUID | None = None


class UpdateUserRequest(BaseModel):
    """All fields optional — only supplied fields are updated (PATCH semantics)."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    role: UserRole | None = None
    is_active: bool | None = None
