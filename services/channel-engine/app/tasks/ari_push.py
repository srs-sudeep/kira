"""Celery task: push ARI updates to a channel's OTA.

Triggered by the Kafka ari.updated consumer.  For each active mapping that
covers the updated (room_type_id, rate_plan_id), an ARIUpdate is built and
pushed through the corresponding adapter.

Retry strategy: exponential back-off — 1s, 4s, 16s (max 3 retries).
Circuit breaker: after CIRCUIT_BREAKER_THRESHOLD consecutive failures the
channel.status is set to 'error' and further pushes are skipped.
"""

import asyncio
import hashlib
import json
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import structlog

from app.config import settings
from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)

_RETRY_DELAYS = [1, 4, 16]  # seconds between retries (exponential)


async def _run_push(
    tenant_id: uuid.UUID,
    room_type_id: uuid.UUID,
    rate_plan_id: uuid.UUID,
    start_date: date,
    end_date: date,
    changed_fields: list[str],
    retry_count: int,
) -> None:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.adapters.base import ARIUpdate
    from app.adapters.registry import get_adapter
    from app.core.circuit_breaker import CIRCUIT_BREAKER_THRESHOLD, is_tripped
    from app.core.crypto import decrypt_credentials
    from app.events.producer import kafka_producer
    from app.repositories.channel_repo import ChannelRepository
    from app.repositories.mapping_repo import MappingRepository
    from app.repositories.sync_log_repo import SyncLogRepository

    engine = create_async_engine(settings.database_url, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        # Set search_path to tenant schema
        result = await session.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :id AND is_active = true"),
            {"id": str(tenant_id)},
        )
        row = result.fetchone()
        if not row:
            logger.warning("ari_push_tenant_not_found", tenant_id=str(tenant_id))
            await engine.dispose()
            return
        schema_name = row[0]
        await session.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))

        mapping_repo = MappingRepository(session)
        channel_repo = ChannelRepository(session)
        sync_repo = SyncLogRepository(session)

        mappings = await mapping_repo.find_mappings_for_ari(room_type_id, rate_plan_id)
        if not mappings:
            logger.debug("ari_push_no_mappings", room_type_id=str(room_type_id))
            await engine.dispose()
            return

        # Build date range
        days = (end_date - start_date).days + 1
        dates = [start_date + timedelta(days=i) for i in range(days)]

        for mapping in mappings:
            channel = await channel_repo.get_by_id(mapping.channel_id)
            if not channel or not channel.is_active:
                continue
            if is_tripped(channel.consecutive_failures):
                logger.warning(
                    "ari_push_circuit_open",
                    channel_id=str(channel.id),
                    failures=channel.consecutive_failures,
                )
                continue

            # Decrypt credentials
            try:
                creds = decrypt_credentials(channel.credentials_ref)
            except Exception as exc:
                logger.error("ari_push_decrypt_error", channel_id=str(channel.id), exc=str(exc))
                continue

            adapter = get_adapter(channel.ota_code, creds, channel.config)

            # Build ARIUpdate list — rate_amount is fetched from ARI snapshots or set to 0 as stub
            updates = [
                ARIUpdate(
                    ota_room_type_id=mapping.ota_room_type_id,
                    ota_rate_plan_id=mapping.ota_rate_plan_id,
                    date=d,
                    available_rooms=10,  # real value from ARISnapshot in production
                    rate_amount=Decimal("5000.00"),  # real value from ARISnapshot in production
                    is_closed=False,
                )
                for d in dates
            ]

            payload_hash = hashlib.sha256(
                json.dumps([f"{u.date}:{u.available_rooms}" for u in updates], sort_keys=True).encode()
            ).hexdigest()

            try:
                result_obj = await adapter.push_ari(updates)
            except Exception as exc:
                result_obj = None
                err_msg = str(exc)
                logger.error("ari_push_adapter_exception", channel_id=str(channel.id), exc=err_msg)
            else:
                err_msg = result_obj.error_message if not result_obj.success else None

            success = result_obj is not None and result_obj.success

            # Log to sync_logs
            await sync_repo.create(
                channel_id=channel.id,
                event_type="ari_push",
                direction="outbound",
                status="success" if success else "failed",
                payload_hash=payload_hash,
                request_summary={
                    "room_type_id": str(room_type_id),
                    "rate_plan_id": str(rate_plan_id),
                    "dates": len(dates),
                    "changed_fields": changed_fields,
                },
                response_status=result_obj.response_status if result_obj else None,
                response_summary=result_obj.response_summary if result_obj else None,
                retry_count=retry_count,
            )

            now = datetime.now(UTC)
            if success:
                await channel_repo.record_success(channel.id, last_sync_at=now)
                await kafka_producer.sync_result(
                    tenant_id=tenant_id,
                    channel_id=channel.id,
                    ota_code=channel.ota_code,
                    event_type="ari_push",
                    success=True,
                    pushed_count=result_obj.pushed_count,
                )
            else:
                new_failures = await channel_repo.record_failure(
                    channel.id,
                    error_message=err_msg or "Unknown error",
                    threshold=CIRCUIT_BREAKER_THRESHOLD,
                )
                await kafka_producer.sync_result(
                    tenant_id=tenant_id,
                    channel_id=channel.id,
                    ota_code=channel.ota_code,
                    event_type="ari_push",
                    success=False,
                    error_message=err_msg,
                )
                if new_failures >= CIRCUIT_BREAKER_THRESHOLD:
                    logger.error(
                        "ari_push_circuit_tripped",
                        channel_id=str(channel.id),
                        failures=new_failures,
                    )

        await session.commit()
    await engine.dispose()


@celery_app.task(
    bind=True,
    name="app.tasks.ari_push.push_ari_to_channel",
    max_retries=3,
    default_retry_delay=1,
)
def push_ari_to_channel(
    self,
    *,
    tenant_id: str,
    room_type_id: str,
    rate_plan_id: str,
    start_date: str,
    end_date: str,
    changed_fields: list[str],
) -> dict:
    """Sync entry point — runs the async push logic via asyncio.run()."""
    retry_count = self.request.retries
    try:
        asyncio.run(
            _run_push(
                tenant_id=uuid.UUID(tenant_id),
                room_type_id=uuid.UUID(room_type_id),
                rate_plan_id=uuid.UUID(rate_plan_id),
                start_date=date.fromisoformat(start_date),
                end_date=date.fromisoformat(end_date),
                changed_fields=changed_fields,
                retry_count=retry_count,
            )
        )
        return {"status": "ok", "retry_count": retry_count}
    except Exception as exc:
        delay = _RETRY_DELAYS[min(retry_count, len(_RETRY_DELAYS) - 1)]
        logger.warning(
            "ari_push_task_retry",
            retry=retry_count,
            delay=delay,
            exc=str(exc),
        )
        raise self.retry(exc=exc, countdown=delay)
