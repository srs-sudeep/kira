"""Repository for ari_snapshots — upsert-heavy, date-range queries."""
import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ari_snapshot import ARISnapshot


class ARIRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(
        self, room_type_id: uuid.UUID, rate_plan_id: uuid.UUID, d: date
    ) -> ARISnapshot | None:
        return (
            await self._s.execute(
                select(ARISnapshot).where(
                    ARISnapshot.room_type_id == room_type_id,
                    ARISnapshot.rate_plan_id == rate_plan_id,
                    ARISnapshot.date == d,
                )
            )
        ).scalar_one_or_none()

    async def get_range(
        self,
        room_type_ids: list[uuid.UUID],
        rate_plan_ids: list[uuid.UUID] | None,
        start_date: date,
        end_date: date,
    ) -> list[ARISnapshot]:
        stmt = select(ARISnapshot).where(
            ARISnapshot.room_type_id.in_(room_type_ids),
            ARISnapshot.date >= start_date,
            ARISnapshot.date <= end_date,
        )
        if rate_plan_ids is not None:
            stmt = stmt.where(ARISnapshot.rate_plan_id.in_(rate_plan_ids))
        rows = (await self._s.execute(stmt.order_by(ARISnapshot.date))).scalars().all()
        return list(rows)

    async def upsert(
        self,
        room_type_id: uuid.UUID,
        rate_plan_id: uuid.UUID,
        d: date,
        defaults: dict[str, Any],
    ) -> ARISnapshot:
        """Insert or update a single ARI cell. Returns the resulting row."""
        stmt = (
            pg_insert(ARISnapshot)
            .values(
                room_type_id=room_type_id,
                rate_plan_id=rate_plan_id,
                date=d,
                **defaults,
            )
            .on_conflict_do_update(
                constraint="uq_ari",
                set_={k: v for k, v in defaults.items()},
            )
            .returning(ARISnapshot)
        )
        result = await self._s.execute(stmt)
        row = result.scalar_one()
        return row

    async def bulk_update_fields(
        self,
        room_type_ids: list[uuid.UUID],
        rate_plan_ids: list[uuid.UUID],
        start_date: date,
        end_date: date,
        updates: dict[str, Any],
    ) -> int:
        """UPDATE existing snapshots matching the criteria. Returns row count."""
        stmt = (
            update(ARISnapshot)
            .where(
                ARISnapshot.room_type_id.in_(room_type_ids),
                ARISnapshot.rate_plan_id.in_(rate_plan_ids),
                ARISnapshot.date >= start_date,
                ARISnapshot.date <= end_date,
            )
            .values(**updates)
        )
        result = await self._s.execute(stmt)
        await self._s.flush()
        return result.rowcount

    async def apply_stop_sell(
        self,
        room_type_ids: list[uuid.UUID],
        rate_plan_ids: list[uuid.UUID] | None,
        start_date: date,
        end_date: date,
        cta_closed: bool = False,
        ctd_closed: bool = False,
    ) -> int:
        stmt = update(ARISnapshot).where(
            ARISnapshot.room_type_id.in_(room_type_ids),
            ARISnapshot.date >= start_date,
            ARISnapshot.date <= end_date,
        )
        if rate_plan_ids is not None:
            stmt = stmt.where(ARISnapshot.rate_plan_id.in_(rate_plan_ids))
        stmt = stmt.values(is_closed=True, cta_closed=cta_closed, ctd_closed=ctd_closed)
        result = await self._s.execute(stmt)
        await self._s.flush()
        return result.rowcount

    async def close_for_date(self, d: date) -> int:
        """Mark all snapshots for a blackout date as closed."""
        stmt = (
            update(ARISnapshot)
            .where(ARISnapshot.date == d)
            .values(is_closed=True)
        )
        result = await self._s.execute(stmt)
        await self._s.flush()
        return result.rowcount

    async def reopen_for_date(self, d: date) -> int:
        stmt = (
            update(ARISnapshot)
            .where(ARISnapshot.date == d)
            .values(is_closed=False)
        )
        result = await self._s.execute(stmt)
        await self._s.flush()
        return result.rowcount
