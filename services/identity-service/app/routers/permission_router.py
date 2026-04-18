"""Permission management endpoints — super_admin only."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import DBSession, require_roles
from app.models.user import User
from app.schemas.permission import (
    AssignPermissionRequest,
    CreatePermissionRequest,
    PermissionListResponse,
    PermissionResponse,
    RevokePermissionRequest,
    RolePermissionsResponse,
    UpdatePermissionRequest,
)
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/permissions", tags=["Permissions"])

_super_admin = Depends(require_roles("super_admin"))


# ── Permission CRUD ───────────────────────────────────────────────────────────


@router.get("/", response_model=PermissionListResponse)
async def list_permissions(
    db: DBSession,
    actor: Annotated[User, _super_admin],
) -> PermissionListResponse:
    svc = PermissionService(db)
    return await svc.list_permissions()


@router.post("/", response_model=PermissionResponse, status_code=201)
async def create_permission(
    req: CreatePermissionRequest,
    db: DBSession,
    actor: Annotated[User, _super_admin],
) -> PermissionResponse:
    svc = PermissionService(db)
    return await svc.create_permission(req, actor=actor)


@router.patch("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: uuid.UUID,
    req: UpdatePermissionRequest,
    db: DBSession,
    actor: Annotated[User, _super_admin],
) -> PermissionResponse:
    svc = PermissionService(db)
    return await svc.update_permission(permission_id, req, actor=actor)


@router.delete("/{permission_id}", status_code=204)
async def delete_permission(
    permission_id: uuid.UUID,
    db: DBSession,
    actor: Annotated[User, _super_admin],
) -> None:
    svc = PermissionService(db)
    await svc.delete_permission(permission_id, actor=actor)


# ── Role-Permission mappings ──────────────────────────────────────────────────


@router.get("/roles/{role}", response_model=RolePermissionsResponse)
async def get_role_permissions(
    role: str,
    db: DBSession,
    actor: Annotated[User, _super_admin],
) -> RolePermissionsResponse:
    svc = PermissionService(db)
    return await svc.get_role_permissions(role)


@router.post("/roles/assign", response_model=RolePermissionsResponse)
async def assign_permission_to_role(
    req: AssignPermissionRequest,
    db: DBSession,
    actor: Annotated[User, _super_admin],
) -> RolePermissionsResponse:
    svc = PermissionService(db)
    return await svc.assign_permission(req, actor=actor)


@router.post("/roles/revoke", response_model=RolePermissionsResponse)
async def revoke_permission_from_role(
    req: RevokePermissionRequest,
    db: DBSession,
    actor: Annotated[User, _super_admin],
) -> RolePermissionsResponse:
    svc = PermissionService(db)
    return await svc.revoke_permission(req, actor=actor)
