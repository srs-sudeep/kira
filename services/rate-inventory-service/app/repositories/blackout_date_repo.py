"""Repository for blackout_dates."""

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blackout_date import BlackoutDate


class BlackoutDateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, bd_id: uuid.UUID) -> BlackoutDate | None:
        return (await self._s.execute(select(BlackoutDate).where(BlackoutDate.id == bd_id))).scalar_one_or_none()

    async def get_by_date(self, d: date) -> BlackoutDate | None:
        return (await self._s.execute(select(BlackoutDate).where(BlackoutDate.date == d))).scalar_one_or_none()

    async def list_all(self, page: int, page_size: int) -> tuple[list[BlackoutDate], int]:
        total = (await self._s.execute(select(func.count()).select_from(select(BlackoutDate).subquery()))).scalar_one()
        rows = (
            (
                await self._s.execute(
                    select(BlackoutDate).order_by(BlackoutDate.date).offset((page - 1) * page_size).limit(page_size)
                )
            )
            .scalars()
            .all()
        )
        return list(rows), total

    async def create(self, d: date, reason: str | None) -> BlackoutDate:
        bd = BlackoutDate(date=d, reason=reason)
        self._s.add(bd)
        await self._s.flush()
        await self._s.refresh(bd)
        return bd

    async def delete(self, bd: BlackoutDate) -> None:
        await self._s.delete(bd)
        await self._s.flush()
