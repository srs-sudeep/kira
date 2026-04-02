"""Repository for channels."""
import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.channel import Channel


class ChannelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, channel_id: uuid.UUID, *, load_relations: bool = False) -> Channel | None:
        q = select(Channel).where(Channel.id == channel_id)
        if load_relations:
            q = q.options(selectinload(Channel.mappings))
        return (await self._s.execute(q)).scalar_one_or_none()

    async def list_all(self, *, active_only: bool = False) -> list[Channel]:
        q = select(Channel).order_by(Channel.created_at)
        if active_only:
            q = q.where(Channel.is_active.is_(True))
        return list((await self._s.execute(q)).scalars().all())

    async def create(
        self,
        *,
        ota_code: str,
        display_name: str,
        credentials_ref: bytes,
        config: dict,
    ) -> Channel:
        channel = Channel(
            ota_code=ota_code,
            display_name=display_name,
            credentials_ref=credentials_ref,
            config=config,
            status="pending_certification",
            consecutive_failures=0,
        )
        self._s.add(channel)
        await self._s.flush()
        await self._s.refresh(channel)
        return channel

    async def update(self, channel: Channel, **kwargs) -> Channel:
        for k, v in kwargs.items():
            setattr(channel, k, v)
        await self._s.flush()
        await self._s.refresh(channel)
        return channel

    async def record_success(self, channel_id: uuid.UUID, last_sync_at: datetime) -> None:
        """Reset circuit breaker and update last_sync_at."""
        await self._s.execute(
            update(Channel)
            .where(Channel.id == channel_id)
            .values(
                consecutive_failures=0,
                status="connected",
                last_sync_at=last_sync_at,
                error_message=None,
            )
        )

    async def record_failure(
        self,
        channel_id: uuid.UUID,
        error_message: str,
        threshold: int,
    ) -> int:
        """Increment consecutive_failures; trip circuit breaker if >= threshold.

        Returns the new consecutive_failures value.
        """
        result = await self._s.execute(
            update(Channel)
            .where(Channel.id == channel_id)
            .values(
                consecutive_failures=Channel.consecutive_failures + 1,
                error_message=error_message,
            )
            .returning(Channel.consecutive_failures)
        )
        new_failures: int = result.scalar_one()
        if new_failures >= threshold:
            await self._s.execute(
                update(Channel)
                .where(Channel.id == channel_id)
                .values(status="error")
            )
        return new_failures

    async def count(self) -> int:
        return (await self._s.execute(select(func.count()).select_from(Channel))).scalar_one()
