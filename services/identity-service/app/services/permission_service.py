"""Permission management business logic."""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError
from app.repositories.audit_repo import AuditRepository
from app.repositories.permission_repo import PermissionRepository
from app.schemas.permission import (
    AssignPermissionRequest,
    CreatePermissionRequest,
    PermissionBrief,
    PermissionListResponse,
    PermissionResponse,
    RevokePermissionRequest,
    RolePermissionsResponse,
    UpdatePermissionRequest,
)
from app.models.user import User, VALID_ROLES

logger = structlog.get_logger(__name__)


class PermissionService:
    def __init__(self, session: AsyncSession) -> None:
        self._perm_repo = PermissionRepository(session)
        self._audit_repo = AuditRepository(session)

    async def list_permissions(self) -> PermissionListResponse:
        perms = await self._perm_repo.list_all()
        return PermissionListResponse(
            items=[PermissionResponse.model_validate(p) for p in perms],
            total=len(perms),
        )

    async def create_permission(self, req: CreatePermissionRequest, *, actor: User) -> PermissionResponse:
        existing = await self._perm_repo.get_by_resource_action(req.resource, req.action)
        if existing:
            raise ConflictError(f"Permission '{req.resource}:{req.action}' already exists.")

        perm = await self._perm_repo.create(
            resource=req.resource,
            action=req.action,
            description=req.description,
        )
        await self._audit_repo.create(
            action="permission.created",
            user_id=actor.id,
            tenant_id=actor.tenant_id,
            resource_type="permission",
            resource_id=str(perm.id),
            after_state={"resource": perm.resource, "action": perm.action},
        )
        logger.info("permission_created", code=perm.code, by=str(actor.id))
        return PermissionResponse.model_validate(perm)

    async def update_permission(
        self, permission_id, req: UpdatePermissionRequest, *, actor: User
    ) -> PermissionResponse:
        perm = await self._perm_repo.get_by_id(permission_id)
        if not perm:
            raise NotFoundError("Permission", str(permission_id))

        updates = req.model_dump(exclude_none=True)
        if not updates:
            return PermissionResponse.model_validate(perm)

        updated = await self._perm_repo.update(perm, **updates)
        await self._audit_repo.create(
            action="permission.updated",
            user_id=actor.id,
            tenant_id=actor.tenant_id,
            resource_type="permission",
            resource_id=str(perm.id),
            after_state=updates,
        )
        return PermissionResponse.model_validate(updated)

    async def delete_permission(self, permission_id, *, actor: User) -> None:
        perm = await self._perm_repo.get_by_id(permission_id)
        if not perm:
            raise NotFoundError("Permission", str(permission_id))

        await self._perm_repo.delete(perm)
        await self._audit_repo.create(
            action="permission.deleted",
            user_id=actor.id,
            tenant_id=actor.tenant_id,
            resource_type="permission",
            resource_id=str(perm.id),
        )
        logger.info("permission_deleted", code=perm.code, by=str(actor.id))

    async def get_role_permissions(self, role: str) -> RolePermissionsResponse:
        if role not in VALID_ROLES:
            raise NotFoundError("Role", role)
        perms = await self._perm_repo.get_permissions_for_role(role)
        return RolePermissionsResponse(
            role=role,
            permissions=[PermissionBrief.model_validate(p) for p in perms],
        )

    async def assign_permission(self, req: AssignPermissionRequest, *, actor: User) -> RolePermissionsResponse:
        perm = await self._perm_repo.get_by_id(req.permission_id)
        if not perm:
            raise NotFoundError("Permission", str(req.permission_id))

        await self._perm_repo.assign_permission_to_role(role=req.role, permission_id=req.permission_id)
        await self._audit_repo.create(
            action="role_permission.assigned",
            user_id=actor.id,
            tenant_id=actor.tenant_id,
            resource_type="role_permission",
            after_state={"role": req.role, "permission": perm.code},
        )
        logger.info("permission_assigned", role=req.role, permission=perm.code, by=str(actor.id))
        return await self.get_role_permissions(req.role)

    async def revoke_permission(self, req: RevokePermissionRequest, *, actor: User) -> RolePermissionsResponse:
        perm = await self._perm_repo.get_by_id(req.permission_id)
        if not perm:
            raise NotFoundError("Permission", str(req.permission_id))

        removed = await self._perm_repo.revoke_permission_from_role(role=req.role, permission_id=req.permission_id)
        if removed:
            await self._audit_repo.create(
                action="role_permission.revoked",
                user_id=actor.id,
                tenant_id=actor.tenant_id,
                resource_type="role_permission",
                after_state={"role": req.role, "permission": perm.code},
            )
            logger.info("permission_revoked", role=req.role, permission=perm.code, by=str(actor.id))
        return await self.get_role_permissions(req.role)
