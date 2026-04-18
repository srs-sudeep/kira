"""Project Kira — reservation-service entry point."""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.events.consumer import channel_booking_consumer
from app.events.producer import kafka_producer
from app.exception_handlers import register_exception_handlers
from app.health import router as health_router
from app.routers.dashboard_router import router as dashboard_router
from app.routers.reservation_router import router as reservation_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("reservation-service starting", port=settings.port)
    await kafka_producer.start()
    await channel_booking_consumer.start()
    yield
    await channel_booking_consumer.stop()
    await kafka_producer.stop()
    logger.info("reservation-service stopped")


app = FastAPI(
    title="Project Kira — Reservation Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Tenant-ID"],
)

Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=False,
    excluded_handlers=["/health", "/metrics"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

register_exception_handlers(app)
app.include_router(health_router)
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(reservation_router, prefix="/api/v1")
