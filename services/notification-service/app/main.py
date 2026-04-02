"""Project Kira — notification-service entry point."""
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.events.consumer import notification_consumer
from app.exception_handlers import register_exception_handlers
from app.health import router as health_router
from app.routers.notification_router import router as notification_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("notification-service starting", port=settings.port)
    await notification_consumer.start()
    yield
    await notification_consumer.stop()
    logger.info("notification-service stopped")


app = FastAPI(
    title="Project Kira — Notification Service",
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
app.include_router(notification_router, prefix="/api/v1")
