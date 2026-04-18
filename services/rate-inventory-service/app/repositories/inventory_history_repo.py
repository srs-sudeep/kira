"""Repository for inventory_history — append-only."""

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory_history import InventoryHistory
from app.schemas.inventory_history import InventoryHistoryQuery


class InventoryHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def record(
        self,
        room_type_id: uuid.UUID,
        rate_plan_id: uuid.UUID,
        d: date,
        field_changed: str,
        old_value: str | None,
        new_value: str | None,
        changed_by: uuid.UUID,
    ) -> InventoryHistory:
        entry = InventoryHistory(
            room_type_id=room_type_id,
            rate_plan_id=rate_plan_id,
            date=d,
            field_changed=field_changed,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
        )
        self._s.add(entry)
        await self._s.flush()
        return entry

    async def bulk_record(self, entries: list[InventoryHistory]) -> None:
        self._s.add_all(entries)
        await self._s.flush()

    async def list_filtered(self, q: InventoryHistoryQuery) -> tuple[list[InventoryHistory], int]:
        base = select(InventoryHistory)
        if q.room_type_id:
            base = base.where(InventoryHistory.room_type_id == q.room_type_id)
        if q.rate_plan_id:
            base = base.where(InventoryHistory.rate_plan_id == q.rate_plan_id)
        if q.date_from:
            base = base.where(InventoryHistory.date >= q.date_from)
        if q.date_to:
            base = base.where(InventoryHistory.date <= q.date_to)
        if q.changed_by:
            base = base.where(InventoryHistory.changed_by == q.changed_by)

        total = (await self._s.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
        rows = (
            (
                await self._s.execute(
                    base.order_by(InventoryHistory.changed_at.desc())
                    .offset((q.page - 1) * q.page_size)
                    .limit(q.page_size)
                )
            )
            .scalars()
            .all()
        )
        return list(rows), total
