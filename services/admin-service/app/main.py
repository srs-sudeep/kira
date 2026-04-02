"""Project Kira — admin-service entry point."""
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.exception_handlers import register_exception_handlers
from app.health import router as health_router
from app.routers.tenant_router import router as tenant_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("admin-service starting", port=settings.port)
    yield
    logger.info("admin-service stopped")


app = FastAPI(
    title="Project Kira — Admin Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=False,
    excluded_handlers=["/health", "/metrics"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

register_exception_handlers(app)
app.include_router(health_router)
app.include_router(tenant_router, prefix="/api/v1")
