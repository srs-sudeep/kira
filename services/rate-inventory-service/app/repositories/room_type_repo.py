"""Repository for room_types."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room_type import RoomType


class RoomTypeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, room_type_id: uuid.UUID) -> RoomType | None:
        return (await self._s.execute(select(RoomType).where(RoomType.id == room_type_id))).scalar_one_or_none()

    async def list_active(self, page: int, page_size: int) -> tuple[list[RoomType], int]:
        base = select(RoomType).where(RoomType.is_active.is_(True))
        total = (await self._s.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
        rows = (
            (
                await self._s.execute(
                    base.order_by(RoomType.sort_order, RoomType.name).offset((page - 1) * page_size).limit(page_size)
                )
            )
            .scalars()
            .all()
        )
        return list(rows), total

    async def create(self, **kwargs) -> RoomType:
        rt = RoomType(**kwargs)
        self._s.add(rt)
        await self._s.flush()
        await self._s.refresh(rt)
        return rt

    async def update(self, room_type: RoomType, **kwargs) -> RoomType:
        for k, v in kwargs.items():
            setattr(room_type, k, v)
        await self._s.flush()
        await self._s.refresh(room_type)
        return room_type

    async def soft_delete(self, room_type: RoomType) -> None:
        room_type.is_active = False
        await self._s.flush()
