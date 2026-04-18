"""KIRA Identity Service — FastAPI dependency injection helpers."""

import uuid
from typing import Annotated, Callable

import structlog
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database import get_db
from app.exceptions import ForbiddenError, UnauthorizedError
from app.models.user import User
from app.repositories.permission_repo import PermissionRepository
from app.repositories.user_repo import UserRepository

logger = structlog.get_logger(__name__)

DBSession = Annotated[AsyncSession, Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: DBSession,
) -> User:
    if not token:
        raise UnauthorizedError("Authentication required.")

    payload = decode_access_token(token)
    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError("Malformed token: missing subject.")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedError("Malformed token: invalid subject format.")

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive.")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: str) -> Callable:
    """Dependency factory that enforces role-based access.

    Usage:
        @router.get("/", dependencies=[Depends(require_roles("super_admin", "property_owner"))])
    or inject the user:
        @router.get("/")
        async def endpoint(actor: Annotated[User, Depends(require_roles("super_admin"))]):
            ...
    """

    async def _check(current_user: CurrentUser) -> User:
        if current_user.role not in roles:
            raise ForbiddenError(f"Role '{current_user.role}' is not permitted. Required: {list(roles)}.")
        return current_user

    return _check


def require_permission(resource: str, action: str) -> Callable:
    """Dependency factory that enforces permission-based access.

    Checks the role_permissions table to see if the user's role has the
    requested resource:action permission.  super_admin always passes.

    Usage:
        @router.post("/rooms", dependencies=[Depends(require_permission("rooms", "create"))])
    or inject the user:
        actor: Annotated[User, Depends(require_permission("rooms", "create"))]
    """

    async def _check(current_user: CurrentUser, db: DBSession) -> User:
        if current_user.role == "super_admin":
            return current_user

        repo = PermissionRepository(db)
        has = await repo.role_has_permission(current_user.role, resource, action)
        if not has:
            raise ForbiddenError(f"Permission '{resource}:{action}' is not granted to role '{current_user.role}'.")
        return current_user

    return _check


def get_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None


def get_user_agent(request: Request) -> str | None:
    return request.headers.get("User-Agent")
