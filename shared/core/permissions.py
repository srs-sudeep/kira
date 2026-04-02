"""KIRA RBAC permission definitions — roles and permission checks."""
from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    SUPER_ADMIN = "super_admin"      # Abode@AB platform staff
    TENANT_ADMIN = "tenant_admin"    # Hotel property manager
    REVENUE_MANAGER = "revenue_manager"
    FRONT_DESK = "front_desk"
    CHANNEL_MANAGER = "channel_manager"
    READ_ONLY = "read_only"


# Ordered by privilege level — higher index = more privilege
_ROLE_HIERARCHY: list[Role] = [
    Role.READ_ONLY,
    Role.FRONT_DESK,
    Role.CHANNEL_MANAGER,
    Role.REVENUE_MANAGER,
    Role.TENANT_ADMIN,
    Role.SUPER_ADMIN,
]

_ROLE_RANK: dict[Role, int] = {r: i for i, r in enumerate(_ROLE_HIERARCHY)}


def has_role(user_roles: list[str], required_role: Role) -> bool:
    """Return True if any of the user's roles meets or exceeds the required role."""
    return any(
        _ROLE_RANK.get(Role(r), -1) >= _ROLE_RANK[required_role]
        for r in user_roles
        if r in _ROLE_RANK
    )


def require_roles(user_roles: list[str], *roles: Role) -> bool:
    """Return True if the user has ALL of the specified roles (exact match, no hierarchy)."""
    user_role_set = set(user_roles)
    return all(r.value in user_role_set for r in roles)


def is_super_admin(user_roles: list[str]) -> bool:
    return Role.SUPER_ADMIN.value in user_roles


def is_tenant_admin(user_roles: list[str]) -> bool:
    return has_role(user_roles, Role.TENANT_ADMIN)
