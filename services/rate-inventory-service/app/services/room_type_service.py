"""Room type CRUD business logic."""

import math
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.repositories.room_type_repo import RoomTypeRepository
from app.schemas.room_type import (
    RoomTypeCreate,
    RoomTypeListResponse,
    RoomTypeResponse,
    RoomTypeUpdate,
)

logger = structlog.get_logger(__name__)


class RoomTypeService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = RoomTypeRepository(session)

    async def list(self, page: int = 1, page_size: int = 50) -> RoomTypeListResponse:
        items, total = await self._repo.list_active(page, page_size)
        return RoomTypeListResponse(
            items=[RoomTypeResponse.model_validate(r) for r in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=max(1, math.ceil(total / page_size)),
        )

    async def get(self, room_type_id: uuid.UUID) -> RoomTypeResponse:
        rt = await self._repo.get_by_id(room_type_id)
        if rt is None or not rt.is_active:
            raise NotFoundError("RoomType", str(room_type_id))
        return RoomTypeResponse.model_validate(rt)

    async def create(self, req: RoomTypeCreate) -> RoomTypeResponse:
        rt = await self._repo.create(**req.model_dump())
        logger.info("room_type_created", id=str(rt.id), name=rt.name)
        return RoomTypeResponse.model_validate(rt)

    async def update(self, room_type_id: uuid.UUID, req: RoomTypeUpdate) -> RoomTypeResponse:
        rt = await self._repo.get_by_id(room_type_id)
        if rt is None or not rt.is_active:
            raise NotFoundError("RoomType", str(room_type_id))
        updates = req.model_dump(exclude_none=True)
        if not updates:
            return RoomTypeResponse.model_validate(rt)
        updated = await self._repo.update(rt, **updates)
        logger.info("room_type_updated", id=str(rt.id))
        return RoomTypeResponse.model_validate(updated)

    async def delete(self, room_type_id: uuid.UUID) -> None:
        rt = await self._repo.get_by_id(room_type_id)
        if rt is None or not rt.is_active:
            raise NotFoundError("RoomType", str(room_type_id))
        await self._repo.soft_delete(rt)
        logger.info("room_type_deleted", id=str(room_type_id))
