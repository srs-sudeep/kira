"""JWT authentication dependencies for admin-service.

Admin-service works exclusively in the public schema — no tenant schema switching.
Auth extracts user_id, role, and tenant_id from the JWT for authorization.
"""
import uuid
from typing import Annotated

import structlog
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.exceptions import ForbiddenError, UnauthorizedError

logger = structlog.get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired token.") from exc


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> uuid.UUID:
    payload = _decode_token(token)
    return uuid.UUID(payload["sub"])


async def get_current_user_role(token: str = Depends(oauth2_scheme)) -> str:
    payload = _decode_token(token)
    return payload.get("role", "")


async def get_tenant_id_from_token(token: str = Depends(oauth2_scheme)) -> uuid.UUID:
    payload = _decode_token(token)
    tid = payload.get("tenant_id")
    if not tid:
        raise UnauthorizedError("No tenant_id in token.")
    return uuid.UUID(tid)


def require_roles(*roles: str):
    """Dependency factory — raises ForbiddenError if the token role is not in *roles*."""
    async def _check(role: str = Depends(get_current_user_role)) -> None:
        if role not in roles:
            raise ForbiddenError(f"Access requires one of: {list(roles)}")
    return Depends(_check)


# ── Typed aliases ─────────────────────────────────────────────────────────────
CurrentUserID = Annotated[uuid.UUID, Depends(get_current_user_id)]
CurrentUserRole = Annotated[str, Depends(get_current_user_role)]
CurrentTenantID = Annotated[uuid.UUID, Depends(get_tenant_id_from_token)]
DB = Annotated[AsyncSession, Depends(get_db)]
