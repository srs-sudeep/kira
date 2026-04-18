"""Repository for public.permissions and public.role_permissions."""

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.permission import Permission, RolePermission


class PermissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ── Permission CRUD ───────────────────────────────────────────────────────

    async def list_all(self) -> list[Permission]:
        result = await self._s.execute(select(Permission).order_by(Permission.resource, Permission.action))
        return list(result.scalars().all())

    async def get_by_id(self, permission_id: uuid.UUID) -> Permission | None:
        result = await self._s.execute(select(Permission).where(Permission.id == permission_id))
        return result.scalar_one_or_none()

    async def get_by_resource_action(self, resource: str, action: str) -> Permission | None:
        result = await self._s.execute(
            select(Permission).where(
                Permission.resource == resource,
                Permission.action == action,
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        resource: str,
        action: str,
        description: str | None = None,
    ) -> Permission:
        perm = Permission(resource=resource, action=action, description=description)
        self._s.add(perm)
        await self._s.flush()
        await self._s.refresh(perm)
        return perm

    async def update(self, perm: Permission, **kwargs) -> Permission:
        for key, value in kwargs.items():
            setattr(perm, key, value)
        await self._s.flush()
        await self._s.refresh(perm)
        return perm

    async def delete(self, perm: Permission) -> None:
        await self._s.delete(perm)
        await self._s.flush()

    # ── Role-Permission mappings ──────────────────────────────────────────────

    async def get_permissions_for_role(self, role: str) -> list[Permission]:
        result = await self._s.execute(
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role == role)
            .order_by(Permission.resource, Permission.action)
        )
        return list(result.scalars().all())

    async def get_permission_codes_for_role(self, role: str) -> set[str]:
        perms = await self.get_permissions_for_role(role)
        return {p.code for p in perms}

    async def role_has_permission(self, role: str, resource: str, action: str) -> bool:
        result = await self._s.execute(
            select(func.count())
            .select_from(RolePermission)
            .join(Permission, RolePermission.permission_id == Permission.id)
            .where(
                RolePermission.role == role,
                Permission.resource == resource,
                Permission.action == action,
            )
        )
        return result.scalar_one() > 0

    async def assign_permission_to_role(self, *, role: str, permission_id: uuid.UUID) -> RolePermission:
        result = await self._s.execute(
            select(RolePermission).where(
                RolePermission.role == role,
                RolePermission.permission_id == permission_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        rp = RolePermission(role=role, permission_id=permission_id)
        self._s.add(rp)
        await self._s.flush()
        await self._s.refresh(rp, attribute_names=["permission"])
        return rp

    async def revoke_permission_from_role(self, *, role: str, permission_id: uuid.UUID) -> bool:
        result = await self._s.execute(
            delete(RolePermission).where(
                RolePermission.role == role,
                RolePermission.permission_id == permission_id,
            )
        )
        await self._s.flush()
        return result.rowcount > 0

    async def get_all_role_permissions(self) -> list[RolePermission]:
        result = await self._s.execute(
            select(RolePermission).options(selectinload(RolePermission.permission)).order_by(RolePermission.role)
        )
        return list(result.scalars().all())
