"""JWT decoding and per-request tenant search_path injection (same pattern as rate-inventory)."""

import uuid
from typing import Annotated, AsyncGenerator

import structlog
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.exceptions import ForbiddenError, NotFoundError, UnauthorizedError

logger = structlog.get_logger(__name__)

ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

_schema_cache: dict[uuid.UUID, str] = {}


def _decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired token.") from exc
    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type.")
    return payload


async def _resolve_schema(tenant_id: uuid.UUID, db: AsyncSession) -> str:
    if tenant_id in _schema_cache:
        return _schema_cache[tenant_id]
    result = await db.execute(
        text("SELECT schema_name FROM public.tenants WHERE id = :id AND is_active = true"),
        {"id": str(tenant_id)},
    )
    row = result.fetchone()
    if not row:
        raise NotFoundError("Tenant", str(tenant_id))
    schema_name: str = row[0]
    _schema_cache[tenant_id] = schema_name
    return schema_name


async def get_tenant_db(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AsyncGenerator[AsyncSession, None]:
    if not token:
        raise UnauthorizedError("Authentication required.")
    payload = _decode_token(token)
    tenant_id_str: str | None = payload.get("tenant_id")
    if not tenant_id_str:
        raise ForbiddenError("Token does not contain a tenant context.")
    try:
        tenant_id = uuid.UUID(tenant_id_str)
    except ValueError:
        raise UnauthorizedError("Malformed token: invalid tenant_id.")
    schema_name = await _resolve_schema(tenant_id, db)
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    yield db


async def get_current_user_id(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> uuid.UUID:
    if not token:
        raise UnauthorizedError("Authentication required.")
    payload = _decode_token(token)
    try:
        return uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise UnauthorizedError("Malformed token.")


async def get_current_user_role(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> str:
    if not token:
        raise UnauthorizedError("Authentication required.")
    return _decode_token(token).get("role", "")


async def get_tenant_id_from_token(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> uuid.UUID:
    if not token:
        raise UnauthorizedError("Authentication required.")
    payload = _decode_token(token)
    try:
        return uuid.UUID(payload["tenant_id"])
    except (KeyError, ValueError, TypeError):
        raise ForbiddenError("Token does not contain a valid tenant_id.")


def require_roles(*roles: str):
    async def _check(role: Annotated[str, Depends(get_current_user_role)]) -> str:
        if role not in roles:
            raise ForbiddenError(f"Role '{role}' not permitted. Required: {list(roles)}.")
        return role

    return _check


# Type aliases used in router function signatures
TenantDB = Annotated[AsyncSession, Depends(get_tenant_db)]
CurrentUserID = Annotated[uuid.UUID, Depends(get_current_user_id)]
CurrentTenantID = Annotated[uuid.UUID, Depends(get_tenant_id_from_token)]
RawToken = Annotated[str | None, Depends(oauth2_scheme)]
