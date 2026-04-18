"""KIRA Kafka helpers — thin wrappers around aiokafka for consistent event publishing."""

from __future__ import annotations

import json
import uuid
from typing import Any

import structlog
from aiokafka import AIOKafkaProducer

logger = structlog.get_logger(__name__)

# Topic name constants — import these instead of hard-coding strings in services
TOPIC_ARI_UPDATED = "ari.updated"
TOPIC_RESERVATION_CREATED = "reservation.created"
TOPIC_RESERVATION_CANCELLED = "reservation.cancelled"
TOPIC_CHANNEL_SYNC_FAILED = "channel.sync.failed"


async def build_producer(bootstrap_servers: str) -> AIOKafkaProducer:
    """Create and start an AIOKafkaProducer."""
    producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v, default=str).encode(),
        key_serializer=lambda k: k.encode() if isinstance(k, str) else k,
        acks="all",
        enable_idempotence=True,
    )
    await producer.start()
    return producer


async def publish_event(
    producer: AIOKafkaProducer,
    topic: str,
    payload: dict[str, Any],
    key: str | None = None,
) -> None:
    """
    Publish a single event to Kafka.

    :param producer: A started AIOKafkaProducer.
    :param topic: Kafka topic name.
    :param payload: Event payload dict (must be JSON-serialisable).
    :param key: Optional partition key — defaults to a new UUID string.
    """
    partition_key = key or str(uuid.uuid4())
    try:
        await producer.send_and_wait(topic, value=payload, key=partition_key)
        logger.info("kafka_event_published", topic=topic, key=partition_key)
    except Exception:
        logger.exception("kafka_publish_failed", topic=topic, key=partition_key)
        raise
