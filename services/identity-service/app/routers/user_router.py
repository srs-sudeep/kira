"""User management endpoints: list, get, invite, update, delete."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import CurrentUser, DBSession, require_roles
from app.models.user import User
from app.schemas.user import InviteUserRequest, UpdateUserRequest, UserListResponse, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

# Only property owners and super admins can manage users
_managers = Depends(require_roles("super_admin", "property_owner"))


@router.get("/", response_model=UserListResponse)
async def list_users(
    db: DBSession,
    actor: Annotated[User, _managers],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> UserListResponse:
    svc = UserService(db)
    # super_admin must supply tenant_id via query; others default to their own tenant
    return await svc.list_users(
        tenant_id=actor.tenant_id,
        page=page,
        page_size=page_size,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    db: DBSession,
    actor: CurrentUser,
) -> UserResponse:
    svc = UserService(db)
    user = await svc.get_user(user_id, actor=actor)
    return UserResponse.model_validate(user)


@router.post("/invite", response_model=UserResponse, status_code=201)
async def invite_user(
    req: InviteUserRequest,
    db: DBSession,
    actor: Annotated[User, _managers],
) -> UserResponse:
    svc = UserService(db)
    user = await svc.invite_user(req, actor=actor)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    req: UpdateUserRequest,
    db: DBSession,
    actor: Annotated[User, _managers],
) -> UserResponse:
    svc = UserService(db)
    updated = await svc.update_user(user_id, req, actor=actor)
    return UserResponse.model_validate(updated)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: uuid.UUID,
    db: DBSession,
    actor: Annotated[User, _managers],
) -> None:
    svc = UserService(db)
    await svc.delete_user(user_id, actor=actor)
