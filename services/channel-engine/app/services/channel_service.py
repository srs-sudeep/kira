"""Channel business logic: create, update, delete, health, sync, mappings."""

import uuid
from collections import Counter

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.registry import get_adapter
from app.core.crypto import encrypt_credentials
from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.repositories.channel_repo import ChannelRepository
from app.repositories.mapping_repo import MappingRepository
from app.repositories.sync_log_repo import SyncLogRepository
from app.schemas.channel import (
    ChannelCreate,
    ChannelHealthItem,
    ChannelListResponse,
    ChannelResponse,
    ChannelUpdate,
    HealthDashboardResponse,
    SyncTriggeredResponse,
)
from app.schemas.mapping import (
    MappingCreate,
    MappingListResponse,
    MappingResponse,
    MappingUpdate,
)
from app.schemas.sync_log import SyncLogPageResponse

logger = structlog.get_logger(__name__)


class ChannelService:
    def __init__(self, session: AsyncSession) -> None:
        self._channel_repo = ChannelRepository(session)
        self._mapping_repo = MappingRepository(session)
        self._sync_repo = SyncLogRepository(session)

    # ── Channel CRUD ──────────────────────────────────────────────────────────

    async def create_channel(self, req: ChannelCreate) -> ChannelResponse:
        # Validate OTA code by ensuring an adapter exists
        adapter = get_adapter(req.ota_code, req.credentials, req.config)

        # Test connection
        connected = await adapter.test_connection()
        error_message = None if connected else "Connection test failed during channel creation."

        credentials_enc = encrypt_credentials(req.credentials)
        channel = await self._channel_repo.create(
            ota_code=req.ota_code,
            display_name=req.display_name,
            credentials_ref=credentials_enc,
            config=req.config,
        )
        if not connected:
            channel = await self._channel_repo.update(
                channel,
                status="error",
                error_message=error_message,
                consecutive_failures=1,
            )
        else:
            channel = await self._channel_repo.update(channel, status="connected")

        logger.info("channel_created", id=str(channel.id), ota=req.ota_code, connected=connected)
        return ChannelResponse.model_validate(channel)

    async def list_channels(self) -> ChannelListResponse:
        channels = await self._channel_repo.list_all()
        return ChannelListResponse(
            items=[ChannelResponse.model_validate(c) for c in channels],
            total=len(channels),
        )

    async def get_channel(self, channel_id: uuid.UUID) -> ChannelResponse:
        channel = await self._channel_repo.get_by_id(channel_id)
        if channel is None:
            raise NotFoundError("Channel", str(channel_id))
        return ChannelResponse.model_validate(channel)

    async def update_channel(self, channel_id: uuid.UUID, req: ChannelUpdate) -> ChannelResponse:
        channel = await self._channel_repo.get_by_id(channel_id)
        if channel is None:
            raise NotFoundError("Channel", str(channel_id))

        updates = req.model_dump(exclude_none=True)

        # Re-encrypt credentials if updated
        if "credentials" in updates:
            new_creds = updates.pop("credentials")
            # Test new credentials
            adapter = get_adapter(channel.ota_code, new_creds, channel.config)
            connected = await adapter.test_connection()
            updates["credentials_ref"] = encrypt_credentials(new_creds)
            if connected:
                updates["status"] = "connected"
                updates["consecutive_failures"] = 0
                updates["error_message"] = None
            else:
                updates["status"] = "error"
                updates["error_message"] = "New credentials failed connection test."

        if not updates:
            return ChannelResponse.model_validate(channel)

        channel = await self._channel_repo.update(channel, **updates)
        logger.info("channel_updated", id=str(channel_id))
        return ChannelResponse.model_validate(channel)

    async def delete_channel(self, channel_id: uuid.UUID) -> None:
        channel = await self._channel_repo.get_by_id(channel_id)
        if channel is None:
            raise NotFoundError("Channel", str(channel_id))
        await self._channel_repo.update(channel, is_active=False, status="disconnected")
        logger.info("channel_deleted", id=str(channel_id))

    # ── Health dashboard ──────────────────────────────────────────────────────

    async def get_health_dashboard(self) -> HealthDashboardResponse:
        channels = await self._channel_repo.list_all()
        status_counts: Counter[str] = Counter(c.status for c in channels)
        items = [
            ChannelHealthItem(
                id=c.id,
                display_name=c.display_name,
                ota_code=c.ota_code,
                status=c.status,
                last_sync_at=c.last_sync_at,
                consecutive_failures=c.consecutive_failures,
                is_active=c.is_active,
            )
            for c in channels
        ]
        return HealthDashboardResponse(
            total=len(channels),
            connected=status_counts.get("connected", 0),
            error=status_counts.get("error", 0),
            disconnected=status_counts.get("disconnected", 0),
            pending_certification=status_counts.get("pending_certification", 0),
            channels=items,
        )

    # ── Manual sync trigger ───────────────────────────────────────────────────

    async def trigger_sync(
        self,
        channel_id: uuid.UUID,
        tenant_id: uuid.UUID,
        schema_name: str,
    ) -> SyncTriggeredResponse:
        channel = await self._channel_repo.get_by_id(channel_id)
        if channel is None:
            raise NotFoundError("Channel", str(channel_id))
        if not channel.is_active:
            raise ValidationError("Cannot sync an inactive channel.")

        from app.tasks.booking_pull import pull_bookings_all_channels

        # Enqueue a one-off booking pull for this channel
        task = pull_bookings_all_channels.apply_async()

        logger.info("manual_sync_triggered", channel_id=str(channel_id))
        return SyncTriggeredResponse(
            channel_id=channel_id,
            message=f"Sync triggered for channel '{channel.display_name}'.",
            task_id=task.id,
        )

    # ── Sync log ──────────────────────────────────────────────────────────────

    async def get_sync_log(
        self,
        channel_id: uuid.UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> SyncLogPageResponse:
        channel = await self._channel_repo.get_by_id(channel_id)
        if channel is None:
            raise NotFoundError("Channel", str(channel_id))
        return await self._sync_repo.paginate(channel_id, page=page, page_size=page_size)

    # ── Channel Mappings ──────────────────────────────────────────────────────

    async def list_mappings(self, channel_id: uuid.UUID) -> MappingListResponse:
        channel = await self._channel_repo.get_by_id(channel_id)
        if channel is None:
            raise NotFoundError("Channel", str(channel_id))
        mappings = await self._mapping_repo.list_by_channel(channel_id)
        return MappingListResponse(
            items=[MappingResponse.model_validate(m) for m in mappings],
            total=len(mappings),
        )

    async def create_mapping(self, channel_id: uuid.UUID, req: MappingCreate) -> MappingResponse:
        channel = await self._channel_repo.get_by_id(channel_id)
        if channel is None:
            raise NotFoundError("Channel", str(channel_id))

        existing = await self._mapping_repo.get_by_internal_ids(
            channel_id, req.internal_room_type_id, req.internal_rate_plan_id
        )
        if existing:
            raise ConflictError(
                f"A mapping for room_type '{req.internal_room_type_id}' and "
                f"rate_plan '{req.internal_rate_plan_id}' already exists on this channel."
            )

        mapping = await self._mapping_repo.create(
            channel_id=channel_id,
            internal_room_type_id=req.internal_room_type_id,
            ota_room_type_id=req.ota_room_type_id,
            internal_rate_plan_id=req.internal_rate_plan_id,
            ota_rate_plan_id=req.ota_rate_plan_id,
        )
        logger.info(
            "mapping_created",
            channel_id=str(channel_id),
            room_type=str(req.internal_room_type_id),
        )
        return MappingResponse.model_validate(mapping)

    async def update_mapping(
        self,
        channel_id: uuid.UUID,
        mapping_id: uuid.UUID,
        req: MappingUpdate,
    ) -> MappingResponse:
        channel = await self._channel_repo.get_by_id(channel_id)
        if channel is None:
            raise NotFoundError("Channel", str(channel_id))
        mapping = await self._mapping_repo.get_by_id(mapping_id)
        if mapping is None or mapping.channel_id != channel_id:
            raise NotFoundError("ChannelMapping", str(mapping_id))

        updates = req.model_dump(exclude_none=True)
        if not updates:
            return MappingResponse.model_validate(mapping)

        mapping = await self._mapping_repo.update(mapping, **updates)
        return MappingResponse.model_validate(mapping)

    async def delete_mapping(self, channel_id: uuid.UUID, mapping_id: uuid.UUID) -> None:
        channel = await self._channel_repo.get_by_id(channel_id)
        if channel is None:
            raise NotFoundError("Channel", str(channel_id))
        mapping = await self._mapping_repo.get_by_id(mapping_id)
        if mapping is None or mapping.channel_id != channel_id:
            raise NotFoundError("ChannelMapping", str(mapping_id))
        await self._mapping_repo.delete(mapping)
        logger.info("mapping_deleted", mapping_id=str(mapping_id))
