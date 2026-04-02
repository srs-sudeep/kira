"""KIRA Identity Service — FastAPI application factory."""
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.database import engine
from app.exception_handlers import register_exception_handlers
from app.health import router as health_router
from app.routers.audit_router import router as audit_router
from app.routers.auth_router import router as auth_router
from app.routers.user_router import router as user_router

# Ensure all ORM models are registered on Base.metadata before Alembic/tests use it
import app.models  # noqa: F401  — registers User, RefreshToken, AuditEvent

logger = structlog.get_logger(__name__)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Extract tenant_id and user_id from the JWT and attach them to request.state.

    The Identity Service only uses the public schema, so no search_path override
    is needed here — that is handled in the other services.
    """

    async def dispatch(self, request: Request, call_next):
        request.state.tenant_id = None
        request.state.user_id = None

        auth_header: str | None = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()
            try:
                from app.core.security import decode_access_token
                payload = decode_access_token(token)
                if payload.get("tenant_id"):
                    request.state.tenant_id = uuid.UUID(payload["tenant_id"])
                if payload.get("sub"):
                    request.state.user_id = uuid.UUID(payload["sub"])
            except Exception:
                # Non-fatal — unauthenticated routes must still work
                pass

        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", service=settings.SERVICE_NAME, env=settings.ENVIRONMENT)
    yield
    await engine.dispose()
    logger.info("shutdown", service=settings.SERVICE_NAME)


app = FastAPI(
    title="KIRA Identity Service",
    version="0.1.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)

# ── Middleware (outermost first) ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TenantContextMiddleware)

# ── Observability ─────────────────────────────────────────────────────────────
Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=False,
    excluded_handlers=["/health", "/metrics"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# ── Exception handlers ────────────────────────────────────────────────────────
register_exception_handlers(app)

# ── Routers ───────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(health_router)
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(user_router, prefix=API_PREFIX)
app.include_router(audit_router, prefix=API_PREFIX)
