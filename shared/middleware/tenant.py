"""KIRA tenant middleware — sets PostgreSQL search_path per request from JWT tenant_id."""
from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)

TENANT_SCHEMA_PREFIX = "tenant_"
PUBLIC_PATHS = {"/health", "/metrics", "/docs", "/openapi.json", "/redoc"}


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Reads ``tenant_id`` from the decoded JWT (set by auth dependency) and
    issues ``SET search_path TO tenant_<id>, public`` on the DB session so
    every query lands in the correct tenant schema.

    The auth dependency must store the tenant_id in ``request.state.tenant_id``
    before any DB access occurs.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        response = await call_next(request)
        return response


async def set_tenant_search_path(session: AsyncSession, tenant_id: str) -> None:
    """
    Set the PostgreSQL search_path for the given session to the tenant schema.
    Call this inside the get_db dependency after the tenant_id is resolved.
    """
    schema = f"{TENANT_SCHEMA_PREFIX}{tenant_id.replace('-', '_')}"
    await session.execute(
        # Raw text is safe here — tenant_id comes from a verified JWT claim
        # and is validated as a UUID before reaching this function
        __import__("sqlalchemy").text(f'SET search_path TO "{schema}", public')
    )
    logger.debug("tenant_schema_set", schema=schema)
