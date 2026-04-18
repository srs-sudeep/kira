"""User management business logic: list, invite, update, delete."""

import math
import secrets
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.repositories.user_repo import UserRepository
from app.schemas.user import InviteUserRequest, UpdateUserRequest, UserListResponse, UserResponse
from app.tasks.email_tasks import send_invite_email

logger = structlog.get_logger(__name__)

# Roles permitted to manage users within a tenant
MANAGER_ROLES = {"super_admin", "property_owner"}


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._user_repo = UserRepository(session)
        self._audit_repo = AuditRepository(session)

    async def list_users(
        self,
        *,
        tenant_id: uuid.UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> UserListResponse:
        users, total = await self._user_repo.list_by_tenant(tenant_id, page, page_size)
        return UserListResponse(
            items=[UserResponse.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
            pages=max(1, math.ceil(total / page_size)),
        )

    async def get_user(self, user_id: uuid.UUID, *, actor: User) -> User:
        user = await self._user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise NotFoundError("User", str(user_id))
        # Non-super-admins can only see users in their own tenant
        if actor.role != "super_admin" and user.tenant_id != actor.tenant_id:
            raise ForbiddenError()
        return user

    async def invite_user(
        self,
        req: InviteUserRequest,
        *,
        actor: User,
        tenant_name: str = "Your property",
    ) -> User:
        if actor.role not in MANAGER_ROLES:
            raise ForbiddenError("Only property owners and super admins can invite users.")

        # Non-super-admins can only invite into their own tenant
        target_tenant = req.tenant_id if actor.role == "super_admin" else actor.tenant_id
        if target_tenant is None:
            raise ForbiddenError("Tenant context is required to invite a user.")

        existing = await self._user_repo.get_by_email(req.email)
        if existing:
            raise ConflictError(f"Email '{req.email}' is already registered.")

        temp_password = secrets.token_urlsafe(12)
        user = await self._user_repo.create(
            email=req.email,
            hashed_password=hash_password(temp_password),
            first_name=req.first_name,
            last_name=req.last_name,
            role=req.role,
            tenant_id=target_tenant,
        )
        await self._audit_repo.create(
            action="user.invited",
            tenant_id=target_tenant,
            user_id=actor.id,
            resource_type="user",
            resource_id=str(user.id),
            after_state={"email": user.email, "role": user.role},
        )
        # Dispatch invite email asynchronously via Celery
        send_invite_email.delay(
            to_email=user.email,
            first_name=user.first_name,
            temp_password=temp_password,
            tenant_name=tenant_name,
        )
        logger.info("user_invited", user_id=str(user.id), by=str(actor.id))
        return user

    async def update_user(
        self,
        user_id: uuid.UUID,
        req: UpdateUserRequest,
        *,
        actor: User,
    ) -> User:
        if actor.role not in MANAGER_ROLES:
            raise ForbiddenError("Insufficient permissions to update users.")

        user = await self._user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise NotFoundError("User", str(user_id))
        if actor.role != "super_admin" and user.tenant_id != actor.tenant_id:
            raise ForbiddenError()

        before = {"role": user.role, "is_active": user.is_active}
        updates = req.model_dump(exclude_none=True)
        if not updates:
            return user

        updated = await self._user_repo.update(user, **updates)
        await self._audit_repo.create(
            action="user.updated",
            tenant_id=user.tenant_id,
            user_id=actor.id,
            resource_type="user",
            resource_id=str(user.id),
            before_state=before,
            after_state=updates,
        )
        logger.info("user_updated", user_id=str(user.id), by=str(actor.id))
        return updated

    async def delete_user(self, user_id: uuid.UUID, *, actor: User) -> None:
        if actor.role not in MANAGER_ROLES:
            raise ForbiddenError("Insufficient permissions to delete users.")

        user = await self._user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise NotFoundError("User", str(user_id))
        if actor.role != "super_admin" and user.tenant_id != actor.tenant_id:
            raise ForbiddenError()
        if str(user.id) == str(actor.id):
            raise ForbiddenError("Cannot delete your own account.")

        await self._user_repo.soft_delete(user)
        await self._audit_repo.create(
            action="user.deleted",
            tenant_id=user.tenant_id,
            user_id=actor.id,
            resource_type="user",
            resource_id=str(user.id),
        )
        logger.info("user_soft_deleted", user_id=str(user.id), by=str(actor.id))
