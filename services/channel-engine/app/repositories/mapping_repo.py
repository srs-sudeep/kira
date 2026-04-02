"""Repository for channel_mappings."""
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel_mapping import ChannelMapping


class MappingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, mapping_id: uuid.UUID) -> ChannelMapping | None:
        return (
            await self._s.execute(
                select(ChannelMapping).where(ChannelMapping.id == mapping_id)
            )
        ).scalar_one_or_none()

    async def list_by_channel(self, channel_id: uuid.UUID, *, active_only: bool = False) -> list[ChannelMapping]:
        q = select(ChannelMapping).where(ChannelMapping.channel_id == channel_id)
        if active_only:
            q = q.where(ChannelMapping.is_active.is_(True))
        q = q.order_by(ChannelMapping.created_at)
        return list((await self._s.execute(q)).scalars().all())

    async def get_by_internal_ids(
        self,
        channel_id: uuid.UUID,
        internal_room_type_id: uuid.UUID,
        internal_rate_plan_id: uuid.UUID,
    ) -> ChannelMapping | None:
        """Look up a single active mapping for a room-type/rate-plan pair."""
        return (
            await self._s.execute(
                select(ChannelMapping).where(
                    ChannelMapping.channel_id == channel_id,
                    ChannelMapping.internal_room_type_id == internal_room_type_id,
                    ChannelMapping.internal_rate_plan_id == internal_rate_plan_id,
                    ChannelMapping.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()

    async def find_mappings_for_ari(
        self,
        internal_room_type_id: uuid.UUID,
        internal_rate_plan_id: uuid.UUID,
    ) -> list[ChannelMapping]:
        """Return all active mappings across all channels for a room/rate pair."""
        return list(
            (
                await self._s.execute(
                    select(ChannelMapping).where(
                        ChannelMapping.internal_room_type_id == internal_room_type_id,
                        ChannelMapping.internal_rate_plan_id == internal_rate_plan_id,
                        ChannelMapping.is_active.is_(True),
                    )
                )
            )
            .scalars()
            .all()
        )

    async def create(
        self,
        *,
        channel_id: uuid.UUID,
        internal_room_type_id: uuid.UUID,
        ota_room_type_id: str,
        internal_rate_plan_id: uuid.UUID,
        ota_rate_plan_id: str,
    ) -> ChannelMapping:
        mapping = ChannelMapping(
            channel_id=channel_id,
            internal_room_type_id=internal_room_type_id,
            ota_room_type_id=ota_room_type_id,
            internal_rate_plan_id=internal_rate_plan_id,
            ota_rate_plan_id=ota_rate_plan_id,
        )
        self._s.add(mapping)
        await self._s.flush()
        await self._s.refresh(mapping)
        return mapping

    async def update(self, mapping: ChannelMapping, **kwargs) -> ChannelMapping:
        for k, v in kwargs.items():
            setattr(mapping, k, v)
        await self._s.flush()
        await self._s.refresh(mapping)
        return mapping

    async def delete(self, mapping: ChannelMapping) -> None:
        await self._s.delete(mapping)
        await self._s.flush()

    async def count_by_channel(self, channel_id: uuid.UUID) -> int:
        return (
            await self._s.execute(
                select(func.count()).select_from(ChannelMapping).where(
                    ChannelMapping.channel_id == channel_id
                )
            )
        ).scalar_one()
