"""Repository for seasonal_rules."""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.seasonal_rule import SeasonalRule


class SeasonalRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, rule_id: uuid.UUID) -> SeasonalRule | None:
        return (await self._s.execute(select(SeasonalRule).where(SeasonalRule.id == rule_id))).scalar_one_or_none()

    async def list_active(self) -> list[SeasonalRule]:
        rows = (
            (
                await self._s.execute(
                    select(SeasonalRule).where(SeasonalRule.is_active.is_(True)).order_by(SeasonalRule.start_date)
                )
            )
            .scalars()
            .all()
        )
        return list(rows)

    async def list_active_covering(self, d: date) -> list[SeasonalRule]:
        """Return rules that are active and whose date range covers the given date."""
        rows = (
            (
                await self._s.execute(
                    select(SeasonalRule).where(
                        SeasonalRule.is_active.is_(True),
                        SeasonalRule.start_date <= d,
                        SeasonalRule.end_date >= d,
                    )
                )
            )
            .scalars()
            .all()
        )
        return list(rows)

    async def list_all(self, page: int, page_size: int) -> tuple[list[SeasonalRule], int]:
        from sqlalchemy import func

        total = (await self._s.execute(select(func.count()).select_from(select(SeasonalRule).subquery()))).scalar_one()
        rows = (
            (
                await self._s.execute(
                    select(SeasonalRule)
                    .order_by(SeasonalRule.start_date)
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )
        return list(rows), total

    async def create(self, **kwargs) -> SeasonalRule:
        rule = SeasonalRule(**kwargs)
        self._s.add(rule)
        await self._s.flush()
        await self._s.refresh(rule)
        return rule

    async def update(self, rule: SeasonalRule, **kwargs) -> SeasonalRule:
        for k, v in kwargs.items():
            setattr(rule, k, v)
        await self._s.flush()
        await self._s.refresh(rule)
        return rule

    async def delete(self, rule: SeasonalRule) -> None:
        await self._s.delete(rule)
        await self._s.flush()
