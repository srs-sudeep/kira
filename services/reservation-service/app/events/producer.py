"""Kafka producer — publishes reservation.created / modified / cancelled."""

import json
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import structlog
from aiokafka import AIOKafkaProducer

from app.config import settings

logger = structlog.get_logger(__name__)

TOPIC_CREATED = "reservation.created"
TOPIC_MODIFIED = "reservation.modified"
TOPIC_CANCELLED = "reservation.cancelled"


def _serialise(obj: Any) -> str:
    """JSON serialiser that handles UUID, date, datetime, Decimal."""
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serialisable")


class KafkaProducerClient:
    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=_serialise).encode(),
            key_serializer=lambda k: k.encode() if k else None,
        )
        await self._producer.start()
        logger.info("kafka_producer_started")

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
            logger.info("kafka_producer_stopped")

    async def _publish(self, topic: str, key: str, payload: dict) -> None:
        if not self._producer:
            logger.warning("kafka_producer_not_started — skipping", topic=topic)
            return
        try:
            await self._producer.send_and_wait(topic, value=payload, key=key)
            logger.debug("event_published", topic=topic, key=key)
        except Exception as exc:
            # Non-fatal — reservation is committed in DB
            logger.error("kafka_publish_failed", topic=topic, exc=str(exc))

    async def reservation_created(
        self,
        *,
        reservation_id: uuid.UUID,
        tenant_id: uuid.UUID,
        confirmation_number: str,
        source: str,
        room_type_id: uuid.UUID,
        rate_plan_id: uuid.UUID,
        check_in: date,
        check_out: date,
        total_amount: Decimal,
        guest_id: uuid.UUID,
    ) -> None:
        payload = {
            "event": "reservation.created",
            "reservation_id": reservation_id,
            "tenant_id": tenant_id,
            "confirmation_number": confirmation_number,
            "source": source,
            "room_type_id": room_type_id,
            "rate_plan_id": rate_plan_id,
            "check_in": check_in,
            "check_out": check_out,
            "total_amount": total_amount,
            "guest_id": guest_id,
        }
        await self._publish(TOPIC_CREATED, f"{tenant_id}:{reservation_id}", payload)

    async def reservation_modified(
        self,
        *,
        reservation_id: uuid.UUID,
        tenant_id: uuid.UUID,
        changed_fields: list[str],
    ) -> None:
        payload = {
            "event": "reservation.modified",
            "reservation_id": reservation_id,
            "tenant_id": tenant_id,
            "changed_fields": changed_fields,
        }
        await self._publish(TOPIC_MODIFIED, f"{tenant_id}:{reservation_id}", payload)

    async def reservation_cancelled(
        self,
        *,
        reservation_id: uuid.UUID,
        tenant_id: uuid.UUID,
        confirmation_number: str,
        cancellation_reason: str,
        room_type_id: uuid.UUID,
        rate_plan_id: uuid.UUID,
        check_in: date,
        check_out: date,
    ) -> None:
        payload = {
            "event": "reservation.cancelled",
            "reservation_id": reservation_id,
            "tenant_id": tenant_id,
            "confirmation_number": confirmation_number,
            "cancellation_reason": cancellation_reason,
            "room_type_id": room_type_id,
            "rate_plan_id": rate_plan_id,
            "check_in": check_in,
            "check_out": check_out,
        }
        await self._publish(TOPIC_CANCELLED, f"{tenant_id}:{reservation_id}", payload)


kafka_producer = KafkaProducerClient()
