"""Kafka producer for channel-engine.

Publishes:
  - channel.sync.result  — success/failure of each ARI push or booking pull
  - channel.booking.raw  — normalised booking data for reservation-service to consume
"""
import json
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import structlog
from aiokafka import AIOKafkaProducer

from app.config import settings

logger = structlog.get_logger(__name__)


def _serialise(obj: Any) -> str:
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON-serialisable")


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
            logger.error("kafka_publish_failed", topic=topic, exc=str(exc))

    async def sync_result(
        self,
        *,
        tenant_id: uuid.UUID,
        channel_id: uuid.UUID,
        ota_code: str,
        event_type: str,
        success: bool,
        pushed_count: int = 0,
        pulled_count: int = 0,
        error_message: str | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "event": "channel.sync.result",
            "tenant_id": tenant_id,
            "channel_id": channel_id,
            "ota_code": ota_code,
            "event_type": event_type,
            "success": success,
            "pushed_count": pushed_count,
            "pulled_count": pulled_count,
            "error_message": error_message,
        }
        await self._publish(
            settings.kafka_topic_sync_result,
            f"{tenant_id}:{channel_id}",
            payload,
        )

    async def booking_raw(
        self,
        *,
        tenant_id: uuid.UUID,
        channel_id: uuid.UUID,
        schema_name: str,
        ota_code: str,
        channel_reservation_id: str,
        internal_room_type_id: uuid.UUID,
        internal_rate_plan_id: uuid.UUID,
        ota_room_type_id: str,
        ota_rate_plan_id: str,
        check_in: date,
        check_out: date,
        total_amount: Decimal,
        currency: str,
        adults: int,
        children: int,
        guest_first_name: str,
        guest_last_name: str,
        guest_email: str | None,
        guest_phone: str | None,
        guest_nationality: str | None,
        special_requests: str | None,
    ) -> None:
        payload: dict[str, Any] = {
            "event": "channel.booking.raw",
            "tenant_id": tenant_id,
            "schema_name": schema_name,
            "channel_id": channel_id,
            "source": ota_code,
            "channel_reservation_id": channel_reservation_id,
            "room_type_id": internal_room_type_id,
            "rate_plan_id": internal_rate_plan_id,
            "ota_room_type_id": ota_room_type_id,
            "ota_rate_plan_id": ota_rate_plan_id,
            "check_in": check_in,
            "check_out": check_out,
            "total_amount": total_amount,
            "currency": currency,
            "adults": adults,
            "children": children,
            "guest": {
                "first_name": guest_first_name,
                "last_name": guest_last_name,
                "email": guest_email,
                "phone": guest_phone,
                "nationality": guest_nationality,
            },
            "special_requests": special_requests,
        }
        await self._publish(
            settings.kafka_topic_booking_raw,
            f"{tenant_id}:{channel_reservation_id}",
            payload,
        )


kafka_producer = KafkaProducerClient()
