"""Pydantic v2 schemas for the RBAC permission system."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserRole


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resource: str
    action: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class PermissionBrief(BaseModel):
    """Compact permission used in role-permission listings."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resource: str
    action: str


class CreatePermissionRequest(BaseModel):
    resource: str = Field(min_length=1, max_length=50, pattern=r"^[a-z_]+$")
    action: str = Field(min_length=1, max_length=50, pattern=r"^[a-z_]+$")
    description: str | None = Field(default=None, max_length=255)


class UpdatePermissionRequest(BaseModel):
    description: str | None = Field(default=None, max_length=255)


class PermissionListResponse(BaseModel):
    items: list[PermissionResponse]
    total: int


class RolePermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    permission_id: uuid.UUID
    permission: PermissionBrief
    created_at: datetime


class AssignPermissionRequest(BaseModel):
    """Assign a permission to a role."""
    role: UserRole
    permission_id: uuid.UUID


class RevokePermissionRequest(BaseModel):
    """Revoke a permission from a role."""
    role: UserRole
    permission_id: uuid.UUID


class RolePermissionsResponse(BaseModel):
    """All permissions for a given role."""
    role: str
    permissions: list[PermissionBrief]
