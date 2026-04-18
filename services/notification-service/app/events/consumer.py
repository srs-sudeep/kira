"""Kafka consumer for notification-service.

Subscribed topics:
  - reservation.created  → notify front_desk + property_owner (in-app + email)
  - reservation.cancelled → notify front_desk + property_owner (in-app + email)
  - channel.sync.failed  → notify property_owner + revenue_manager (in-app + email)

For each event:
  1. Resolve the tenant schema from payload.tenant_id
  2. SET LOCAL search_path to that schema
  3. Query public.users for eligible recipients by role
  4. For each recipient, check notification_preferences
  5. Create in-app Notification records (if in_app_enabled)
  6. Enqueue email Celery tasks (if email_enabled)
"""

import asyncio
import json
import uuid

import structlog
from aiokafka import AIOKafkaConsumer

from app.config import settings

logger = structlog.get_logger(__name__)

# Role sets per event type
_ROLES_FOR_EVENT: dict[str, tuple[str, ...]] = {
    "new_booking": ("front_desk", "property_owner"),
    "cancellation": ("front_desk", "property_owner"),
    "channel_failure": ("property_owner", "revenue_manager"),
}


async def _get_recipients(
    session,
    tenant_id: uuid.UUID,
    roles: tuple[str, ...],
) -> list[dict]:
    """Return list of {id, first_name, last_name, email} from public.users for the tenant."""
    from sqlalchemy import text

    rows = (
        await session.execute(
            text(
                "SELECT id, first_name, last_name, email "
                "FROM public.users "
                "WHERE tenant_id = :tid AND role = ANY(:roles) AND is_active = true"
            ),
            {"tid": str(tenant_id), "roles": list(roles)},
        )
    ).fetchall()
    return [
        {
            "id": uuid.UUID(str(r[0])),
            "first_name": r[1],
            "last_name": r[2],
            "email": r[3],
        }
        for r in rows
    ]


async def _dispatch(
    session,
    tenant_id: uuid.UUID,
    schema_name: str,
    event_type: str,
    title: str,
    message: str,
    data: dict,
    email_task_kwargs_builder,  # callable(recipient) -> dict | None
) -> None:
    """Create in-app notifications and enqueue email tasks for eligible recipients."""
    from sqlalchemy import text

    from app.repositories.notification_repo import NotificationRepository
    from app.repositories.preference_repo import PreferenceRepository

    await session.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))

    roles = _ROLES_FOR_EVENT.get(event_type, ())
    recipients = await _get_recipients(session, tenant_id, roles)
    if not recipients:
        logger.debug("no_recipients_for_event", event_type=event_type, tenant=str(tenant_id))
        return

    notif_repo = NotificationRepository(session)
    pref_repo = PreferenceRepository(session)

    for recipient in recipients:
        user_id: uuid.UUID = recipient["id"]

        # In-app notification
        if await pref_repo.is_enabled(user_id, event_type, "in_app"):
            await notif_repo.create(
                user_id=user_id,
                type=event_type,
                title=title,
                message=message,
                data=data,
            )

        # Email notification — only if recipient has an email address
        if recipient["email"] and await pref_repo.is_enabled(user_id, event_type, "email"):
            kwargs = email_task_kwargs_builder(recipient)
            if kwargs is not None:
                _dispatch_email_task(event_type, kwargs)

    await session.commit()
    logger.info(
        "notifications_dispatched",
        event_type=event_type,
        tenant=str(tenant_id),
        recipients=len(recipients),
    )


def _dispatch_email_task(event_type: str, kwargs: dict) -> None:
    from app.tasks.email_sender import (
        send_cancellation_alert,
        send_channel_failure_alert,
        send_new_booking_alert,
    )

    if event_type == "new_booking":
        send_new_booking_alert.delay(**kwargs)
    elif event_type == "cancellation":
        send_cancellation_alert.delay(**kwargs)
    elif event_type == "channel_failure":
        send_channel_failure_alert.delay(**kwargs)


async def _handle_reservation_created(session, payload: dict) -> None:
    tenant_id = uuid.UUID(payload["tenant_id"])
    schema_name = await _resolve_schema(session, tenant_id)

    confirmation = payload.get("confirmation_number", "N/A")
    check_in = payload.get("check_in", "")
    check_out = payload.get("check_out", "")
    total_amount = str(payload.get("total_amount", ""))
    currency = payload.get("currency", "INR")

    title = f"New Booking: {confirmation}"
    message = f"Guest reservation {confirmation} confirmed. Check-in: {check_in}, Check-out: {check_out}."

    def build_email(recipient: dict) -> dict:
        return {
            "to_email": recipient["email"],
            "recipient_name": f"{recipient['first_name']} {recipient['last_name']}",
            "confirmation_number": confirmation,
            "guest_name": payload.get("guest_name", "Guest"),
            "check_in": check_in,
            "check_out": check_out,
            "room_type": str(payload.get("room_type_id", "")),
            "total_amount": total_amount,
            "currency": currency,
        }

    await _dispatch(
        session,
        tenant_id,
        schema_name,
        event_type="new_booking",
        title=title,
        message=message,
        data={"confirmation_number": confirmation, "check_in": check_in, "check_out": check_out},
        email_task_kwargs_builder=build_email,
    )


async def _handle_reservation_cancelled(session, payload: dict) -> None:
    tenant_id = uuid.UUID(payload["tenant_id"])
    schema_name = await _resolve_schema(session, tenant_id)

    confirmation = payload.get("confirmation_number", "N/A")
    reason = payload.get("cancellation_reason", "Not specified")

    title = f"Reservation Cancelled: {confirmation}"
    message = f"Reservation {confirmation} was cancelled. Reason: {reason}."

    def build_email(recipient: dict) -> dict:
        return {
            "to_email": recipient["email"],
            "recipient_name": f"{recipient['first_name']} {recipient['last_name']}",
            "confirmation_number": confirmation,
            "guest_name": payload.get("guest_name", "Guest"),
            "cancellation_reason": reason,
        }

    await _dispatch(
        session,
        tenant_id,
        schema_name,
        event_type="cancellation",
        title=title,
        message=message,
        data={"confirmation_number": confirmation, "reason": reason},
        email_task_kwargs_builder=build_email,
    )


async def _handle_channel_sync_failed(session, payload: dict) -> None:
    tenant_id = uuid.UUID(payload["tenant_id"])
    schema_name = await _resolve_schema(session, tenant_id)

    channel_name = payload.get("channel_name", payload.get("ota_code", "Unknown"))
    ota_code = payload.get("ota_code", "")
    error_message = payload.get("error_message", "Sync failed")

    title = f"Channel Sync Failed: {channel_name}"
    message = f"Channel '{channel_name}' ({ota_code}) encountered a sync error: {error_message}."

    def build_email(recipient: dict) -> dict:
        return {
            "to_email": recipient["email"],
            "recipient_name": f"{recipient['first_name']} {recipient['last_name']}",
            "channel_name": channel_name,
            "ota_code": ota_code,
            "error_message": error_message,
        }

    await _dispatch(
        session,
        tenant_id,
        schema_name,
        event_type="channel_failure",
        title=title,
        message=message,
        data={"channel_name": channel_name, "ota_code": ota_code, "error": error_message},
        email_task_kwargs_builder=build_email,
    )


async def _resolve_schema(session, tenant_id: uuid.UUID) -> str:
    from sqlalchemy import text

    row = (
        await session.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :id AND is_active = true"),
            {"id": str(tenant_id)},
        )
    ).fetchone()
    if not row:
        raise ValueError(f"Tenant not found: {tenant_id}")
    return row[0]


_HANDLERS = {
    settings.kafka_topic_reservation_created: _handle_reservation_created,
    settings.kafka_topic_reservation_cancelled: _handle_reservation_cancelled,
    settings.kafka_topic_channel_sync_failed: _handle_channel_sync_failed,
}


class NotificationConsumer:
    def __init__(self) -> None:
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        topics = list(_HANDLERS.keys())
        self._consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_consumer_group,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        await self._consumer.start()
        self._task = asyncio.create_task(self._consume_loop())
        logger.info("notification_consumer_started", topics=topics)

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._consumer:
            await self._consumer.stop()
        logger.info("notification_consumer_stopped")

    async def _consume_loop(self) -> None:
        assert self._consumer is not None
        async for msg in self._consumer:
            try:
                handler = _HANDLERS.get(msg.topic)
                if handler is None:
                    continue
                await self._process(handler, msg.value)
            except Exception as exc:
                logger.error(
                    "notification_consumer_error",
                    topic=msg.topic,
                    exc=str(exc),
                    offset=msg.offset,
                )

    async def _process(self, handler, payload: dict) -> None:
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        engine = create_async_engine(settings.database_url, echo=False)
        SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with SessionLocal() as session:
                await handler(session, payload)
        except Exception as exc:
            logger.error("notification_handler_failed", exc=str(exc))
        finally:
            await engine.dispose()


notification_consumer = NotificationConsumer()
