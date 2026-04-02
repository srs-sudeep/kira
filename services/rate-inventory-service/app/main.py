"""KIRA Rate & Inventory Service — FastAPI application factory."""
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

import app.models  # noqa: F401 — registers all ORM models on Base.metadata
from app.config import settings
from app.database import engine
from app.events.producer import kafka_producer
from app.exception_handlers import register_exception_handlers
from app.health import router as health_router
from app.routers.inventory_router import router as inventory_router
from app.routers.room_type_router import router as room_type_router

logger = structlog.get_logger(__name__)

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", service=settings.service_name, env=settings.environment)
    if settings.environment != "test":
        await kafka_producer.start()
    yield
    if settings.environment != "test":
        await kafka_producer.stop()
    await engine.dispose()
    logger.info("shutdown", service=settings.service_name)


app = FastAPI(
    title="KIRA Rate & Inventory Service",
    version="0.1.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
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
app.include_router(room_type_router, prefix=API_PREFIX)
app.include_router(inventory_router, prefix=API_PREFIX)
