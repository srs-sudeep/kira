"""Repository for rate_plans."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.rate_plan import RatePlan


class RatePlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, rate_plan_id: uuid.UUID) -> RatePlan | None:
        return (
            await self._s.execute(
                select(RatePlan)
                .where(RatePlan.id == rate_plan_id)
                .options(selectinload(RatePlan.derived_plans))
            )
        ).scalar_one_or_none()

    async def list_by_room_type(self, room_type_id: uuid.UUID) -> list[RatePlan]:
        rows = (
            await self._s.execute(
                select(RatePlan)
                .where(RatePlan.room_type_id == room_type_id, RatePlan.is_active.is_(True))
                .order_by(RatePlan.name)
                .options(selectinload(RatePlan.derived_plans))
            )
        ).scalars().all()
        return list(rows)

    async def get_children(self, parent_id: uuid.UUID) -> list[RatePlan]:
        rows = (
            await self._s.execute(
                select(RatePlan).where(RatePlan.derived_from_id == parent_id)
            )
        ).scalars().all()
        return list(rows)

    async def create(self, **kwargs) -> RatePlan:
        rp = RatePlan(**kwargs)
        self._s.add(rp)
        await self._s.flush()
        await self._s.refresh(rp)
        return rp

    async def update(self, rate_plan: RatePlan, **kwargs) -> RatePlan:
        for k, v in kwargs.items():
            setattr(rate_plan, k, v)
        await self._s.flush()
        await self._s.refresh(rate_plan)
        return rate_plan

    async def soft_delete(self, rate_plan: RatePlan) -> None:
        rate_plan.is_active = False
        await self._s.flush()
