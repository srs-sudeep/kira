"""Kafka producer for the rate-inventory-service.

Publishes:
  - ari.updated  — every time ARI changes (calendar edit, bulk, stop-sell, seasonal apply)
"""
import json
import uuid
from datetime import date
from typing import Any

import structlog
from aiokafka import AIOKafkaProducer

from app.config import settings

logger = structlog.get_logger(__name__)

TOPIC_ARI_UPDATED = "ari.updated"


class ARIUpdatedEvent:
    """Value object representing a single ari.updated Kafka message."""

    def __init__(
        self,
        tenant_id: uuid.UUID,
        room_type_id: uuid.UUID,
        rate_plan_id: uuid.UUID,
        start_date: date,
        end_date: date,
        changed_fields: list[str],
        source: str = "manual",
    ) -> None:
        self.tenant_id = tenant_id
        self.room_type_id = room_type_id
        self.rate_plan_id = rate_plan_id
        self.start_date = start_date
        self.end_date = end_date
        self.changed_fields = changed_fields
        self.source = source  # "manual" | "seasonal_rule" | "stop_sell" | "blackout"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": str(self.tenant_id),
            "room_type_id": str(self.room_type_id),
            "rate_plan_id": str(self.rate_plan_id),
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "changed_fields": self.changed_fields,
            "source": self.source,
        }


class KafkaProducerClient:
    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
        await self._producer.start()
        logger.info("kafka_producer_started", brokers=settings.kafka_bootstrap_servers)

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
            logger.info("kafka_producer_stopped")

    async def publish_ari_updated(self, event: ARIUpdatedEvent) -> None:
        if not self._producer:
            logger.warning("kafka_producer_not_started — skipping publish")
            return
        try:
            await self._producer.send_and_wait(
                TOPIC_ARI_UPDATED,
                value=event.to_dict(),
                key=f"{event.tenant_id}:{event.room_type_id}:{event.rate_plan_id}",
            )
            logger.debug(
                "ari_updated_published",
                room_type_id=str(event.room_type_id),
                rate_plan_id=str(event.rate_plan_id),
                dates=f"{event.start_date}/{event.end_date}",
            )
        except Exception as exc:
            logger.error("kafka_publish_failed", topic=TOPIC_ARI_UPDATED, exc=str(exc))
            # Non-fatal: ARI is already committed in the DB — don't roll back for Kafka failure


# Module-level singleton — started/stopped in app lifespan
kafka_producer = KafkaProducerClient()
