"""Kafka consumer — processes raw booking payloads from channel-engine.

Expected message schema on topic `channel.booking.raw`:
{
  "tenant_id": "<uuid>",
  "schema_name": "<str>",
  "channel_id": "<uuid>",
  "channel_reservation_id": "<str>",
  "source": "booking_com|expedia|...",
  "room_type_id": "<uuid>",
  "rate_plan_id": "<uuid>",
  "check_in": "YYYY-MM-DD",
  "check_out": "YYYY-MM-DD",
  "total_amount": "9999.00",
  "currency": "INR",
  "adults": 2,
  "children": 0,
  "guest": {
    "first_name": "...",
    "last_name": "...",
    "email": "...|null",
    "phone": "...|null",
    "nationality": "IND|null"
  },
  "special_requests": "...|null",
  "cancellation_policy": {...}|null
}
"""

import asyncio
import json
import uuid
from datetime import date
from decimal import Decimal

import structlog
from aiokafka import AIOKafkaConsumer
from sqlalchemy import text

from app.config import settings
from app.core.crypto import encrypt_pii, hash_email
from app.database import AsyncSessionLocal
from app.repositories.guest_repo import GuestRepository
from app.repositories.reservation_repo import ReservationRepository
from app.events.producer import kafka_producer

logger = structlog.get_logger(__name__)

TOPIC_CHANNEL_BOOKING = "channel.booking.raw"
GROUP_ID = "reservation-service-consumer"


class ChannelBookingConsumer:
    def __init__(self) -> None:
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            TOPIC_CHANNEL_BOOKING,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=GROUP_ID,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
        )
        await self._consumer.start()
        self._running = True
        self._task = asyncio.create_task(self._consume_loop())
        logger.info("channel_booking_consumer_started", topic=TOPIC_CHANNEL_BOOKING)

    async def stop(self) -> None:
        self._running = False
        if self._consumer:
            await self._consumer.stop()
        if self._task:
            self._task.cancel()
        logger.info("channel_booking_consumer_stopped")

    async def _consume_loop(self) -> None:
        if not self._consumer:
            return
        try:
            async for msg in self._consumer:
                if not self._running:
                    break
                try:
                    await self._handle(msg.value)
                except Exception as exc:
                    logger.error("channel_booking_handle_error", exc=str(exc))
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.error("channel_booking_consumer_loop_error", exc=str(exc))

    async def _handle(self, payload: dict) -> None:
        """Parse the channel-engine payload and create a reservation."""
        tenant_id = uuid.UUID(payload["tenant_id"])
        schema_name: str = payload["schema_name"]

        async with AsyncSessionLocal() as session:
            try:
                await session.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
                guest_repo = GuestRepository(session)
                res_repo = ReservationRepository(session)

                # ── Guest: match by email_hash or create new ──────────────────
                raw_guest = payload["guest"]
                email_plain: str | None = raw_guest.get("email")
                phone_plain: str | None = raw_guest.get("phone")
                email_hash_val: str | None = hash_email(email_plain) if email_plain else None
                email_enc = encrypt_pii(email_plain) if email_plain else None
                phone_enc = encrypt_pii(phone_plain) if phone_plain else None

                guest = None
                if email_hash_val:
                    guest = await guest_repo.get_by_email_hash(email_hash_val)

                if guest is None:
                    guest = await guest_repo.create(
                        first_name=raw_guest["first_name"],
                        last_name=raw_guest["last_name"],
                        email_encrypted=email_enc,
                        phone_encrypted=phone_enc,
                        email_hash=email_hash_val,
                        nationality=raw_guest.get("nationality"),
                        preferences={},
                    )

                # ── Prevent duplicate channel reservations ────────────────────
                channel_res_id: str | None = payload.get("channel_reservation_id")
                if channel_res_id:
                    existing = await session.execute(
                        text("SELECT id FROM reservations WHERE channel_reservation_id = :crid LIMIT 1"),
                        {"crid": channel_res_id},
                    )
                    if existing.fetchone():
                        logger.info("channel_booking_duplicate_skipped", channel_res_id=channel_res_id)
                        return

                res = await res_repo.create(
                    guest_profile_id=guest.id,
                    room_type_id=uuid.UUID(payload["room_type_id"]),
                    rate_plan_id=uuid.UUID(payload["rate_plan_id"]),
                    check_in=date.fromisoformat(payload["check_in"]),
                    check_out=date.fromisoformat(payload["check_out"]),
                    source=payload["source"],
                    channel_id=uuid.UUID(payload["channel_id"]) if payload.get("channel_id") else None,
                    channel_reservation_id=channel_res_id,
                    adults=payload.get("adults", 1),
                    children=payload.get("children", 0),
                    total_amount=Decimal(str(payload["total_amount"])),
                    currency=payload.get("currency", "INR"),
                    cancellation_policy=payload.get("cancellation_policy"),
                    special_requests=payload.get("special_requests"),
                )

                await session.commit()

                await kafka_producer.reservation_created(
                    reservation_id=res.id,
                    tenant_id=tenant_id,
                    confirmation_number=res.confirmation_number,
                    source=res.source,
                    room_type_id=res.room_type_id,
                    rate_plan_id=res.rate_plan_id,
                    check_in=res.check_in,
                    check_out=res.check_out,
                    total_amount=res.total_amount,
                    guest_id=guest.id,
                )
                logger.info(
                    "channel_booking_created",
                    confirmation=res.confirmation_number,
                    source=res.source,
                )
            except Exception:
                await session.rollback()
                raise


channel_booking_consumer = ChannelBookingConsumer()
