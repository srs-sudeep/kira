"""Kafka consumer — subscribes to ari.updated and dispatches ARI push tasks.

When an ari.updated event arrives, we look up all active channel mappings for
the (room_type_id, rate_plan_id) pair, build per-channel task payloads, and
enqueue Celery tasks to push the ARI to each mapped OTA.

We intentionally keep the consumer thin — no DB writes happen here.  All
heavy lifting (adapter calls, sync logging, circuit breaker) is in the Celery task.
"""
import asyncio
import json
import uuid
from datetime import date

import structlog
from aiokafka import AIOKafkaConsumer

from app.config import settings

logger = structlog.get_logger(__name__)

TOPIC_ARI_UPDATED = settings.kafka_topic_ari_updated


class ARIUpdatedConsumer:
    def __init__(self) -> None:
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            TOPIC_ARI_UPDATED,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_consumer_group,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        await self._consumer.start()
        self._task = asyncio.create_task(self._consume_loop())
        logger.info("ari_consumer_started", topic=TOPIC_ARI_UPDATED)

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._consumer:
            await self._consumer.stop()
        logger.info("ari_consumer_stopped")

    async def _consume_loop(self) -> None:
        assert self._consumer is not None
        async for msg in self._consumer:
            try:
                await self._handle(msg.value)
            except Exception as exc:
                logger.error(
                    "ari_consumer_handle_error",
                    exc=str(exc),
                    offset=msg.offset,
                )

    async def _handle(self, payload: dict) -> None:
        """Dispatch a Celery task for each active mapping found for this ARI event."""
        from app.tasks.ari_push import push_ari_to_channel

        tenant_id_str: str = payload.get("tenant_id", "")
        room_type_id_str: str = payload.get("room_type_id", "")
        rate_plan_id_str: str = payload.get("rate_plan_id", "")
        start_date_str: str = payload.get("start_date", "")
        end_date_str: str = payload.get("end_date", "")
        changed_fields: list[str] = payload.get("changed_fields", [])

        if not all([tenant_id_str, room_type_id_str, rate_plan_id_str, start_date_str, end_date_str]):
            logger.warning("ari_consumer_incomplete_payload", payload=payload)
            return

        try:
            tenant_id = uuid.UUID(tenant_id_str)
            room_type_id = uuid.UUID(room_type_id_str)
            rate_plan_id = uuid.UUID(rate_plan_id_str)
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
        except (ValueError, TypeError) as exc:
            logger.error("ari_consumer_parse_error", exc=str(exc))
            return

        # Enqueue Celery task — the task itself queries mappings and calls adapters
        push_ari_to_channel.apply_async(
            kwargs={
                "tenant_id": str(tenant_id),
                "room_type_id": str(room_type_id),
                "rate_plan_id": str(rate_plan_id),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "changed_fields": changed_fields,
            }
        )
        logger.info(
            "ari_push_task_enqueued",
            room_type_id=room_type_id_str,
            rate_plan_id=rate_plan_id_str,
        )


ari_consumer = ARIUpdatedConsumer()
