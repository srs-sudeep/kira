"""Tests for ARI calendar, bulk update, stop-sell, seasonal rules, blackout dates."""
import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.ari_snapshot import ARISnapshot
from app.schemas.ari import (
    ARICalendarPutRequest,
    ARICellUpdate,
    BulkUpdateRequest,
    StopSellRequest,
)
from app.schemas.blackout_date import BlackoutDateCreate
from app.schemas.seasonal_rule import SeasonalRuleCreate, SeasonalRuleUpdate
from app.services.ari_service import ARIService
from tests.conftest import FAKE_TENANT_ID, FAKE_USER_ID, make_rate_plan, make_room_type

TODAY = date.today()


async def seed_ari(session: AsyncSession, room_type_id: uuid.UUID, rate_plan_id: uuid.UUID, d: date, **kwargs):
    snap = ARISnapshot(
        room_type_id=room_type_id,
        rate_plan_id=rate_plan_id,
        date=d,
        available_rooms=kwargs.get("available_rooms", 5),
        rate_amount=kwargs.get("rate_amount", Decimal("5000.00")),
        is_closed=kwargs.get("is_closed", False),
        cta_closed=False,
        ctd_closed=False,
        min_los=1,
        max_los=365,
        overbooking_buffer=0,
    )
    session.add(snap)
    await session.flush()
    return snap


class TestARICalendar:
    async def test_get_calendar_returns_grid(self, db: AsyncSession):
        rt = await make_room_type(db)
        rp = await make_rate_plan(db, rt.id)
        await seed_ari(db, rt.id, rp.id, TODAY)
        svc = ARIService(db)
        resp = await svc.get_calendar(rt.id, TODAY, TODAY)
        assert resp.start_date == TODAY
        assert len(resp.room_types) == 1
        rt_row = resp.room_types[0]
        assert rt_row.room_type_id == rt.id
        assert len(rt_row.rate_plans) == 1
        assert TODAY.isoformat() in rt_row.rate_plans[0].cells

    async def test_get_calendar_missing_cells_not_included(self, db: AsyncSession):
        rt = await make_room_type(db)
        rp = await make_rate_plan(db, rt.id)
        # Seed only one of three dates
        await seed_ari(db, rt.id, rp.id, TODAY)
        svc = ARIService(db)
        resp = await svc.get_calendar(rt.id, TODAY, TODAY + timedelta(days=2))
        cells = resp.room_types[0].rate_plans[0].cells
        assert TODAY.isoformat() in cells
        assert (TODAY + timedelta(days=1)).isoformat() not in cells

    async def test_get_calendar_exceeds_365_days_raises(self, db: AsyncSession):
        rt = await make_room_type(db)
        svc = ARIService(db)
        with pytest.raises(ValidationError):
            await svc.get_calendar(rt.id, TODAY, TODAY + timedelta(days=366))

    async def test_update_calendar_upserts_cells(self, db: AsyncSession):
        rt = await make_room_type(db)
        rp = await make_rate_plan(db, rt.id)
        req = ARICalendarPutRequest(
            cells=[
                ARICellUpdate(
                    room_type_id=rt.id,
                    rate_plan_id=rp.id,
                    date=TODAY,
                    available_rooms=8,
                    rate_amount=Decimal("6000"),
                )
            ]
        )
        svc = ARIService(db)
        count = await svc.update_calendar(req, FAKE_USER_ID, FAKE_TENANT_ID)
        assert count == 1
        # Verify the cell was written
        resp = await svc.get_calendar(rt.id, TODAY, TODAY)
        cell = resp.room_types[0].rate_plans[0].cells.get(TODAY.isoformat())
        assert cell is not None
        assert cell.available_rooms == 8
        assert cell.rate_amount == Decimal("6000.00")


class TestBulkUpdate:
    async def test_bulk_update_modifies_existing_snapshots(self, db: AsyncSession):
        rt = await make_room_type(db)
        rp = await make_rate_plan(db, rt.id)
        await seed_ari(db, rt.id, rp.id, TODAY)
        await seed_ari(db, rt.id, rp.id, TODAY + timedelta(days=1))

        svc = ARIService(db)
        req = BulkUpdateRequest(
            room_type_ids=[rt.id],
            rate_plan_ids=[rp.id],
            start_date=TODAY,
            end_date=TODAY + timedelta(days=1),
            available_rooms=3,
        )
        result = await svc.bulk_update(req, FAKE_USER_ID, FAKE_TENANT_ID)
        assert result.updated_cells == 2

    async def test_bulk_update_empty_range_returns_zero(self, db: AsyncSession):
        rt = await make_room_type(db)
        rp = await make_rate_plan(db, rt.id)
        svc = ARIService(db)
        req = BulkUpdateRequest(
            room_type_ids=[rt.id],
            rate_plan_ids=[rp.id],
            start_date=TODAY + timedelta(days=100),
            end_date=TODAY + timedelta(days=101),
            available_rooms=5,
        )
        result = await svc.bulk_update(req, FAKE_USER_ID, FAKE_TENANT_ID)
        assert result.updated_cells == 0


class TestStopSell:
    async def test_stop_sell_closes_snapshots(self, db: AsyncSession):
        rt = await make_room_type(db)
        rp = await make_rate_plan(db, rt.id)
        await seed_ari(db, rt.id, rp.id, TODAY, is_closed=False)
        await seed_ari(db, rt.id, rp.id, TODAY + timedelta(days=1), is_closed=False)

        svc = ARIService(db)
        req = StopSellRequest(
            room_type_ids=[rt.id],
            rate_plan_ids=[rp.id],
            start_date=TODAY,
            end_date=TODAY + timedelta(days=1),
        )
        result = await svc.stop_sell(req, FAKE_USER_ID, FAKE_TENANT_ID)
        assert result.updated_cells == 2

        resp = await svc.get_calendar(rt.id, TODAY, TODAY)
        assert resp.room_types[0].rate_plans[0].cells[TODAY.isoformat()].is_closed is True


class TestSeasonalRules:
    async def test_create_rule(self, db: AsyncSession):
        svc = ARIService(db)
        req = SeasonalRuleCreate(
            name="Summer Peak",
            start_date=TODAY,
            end_date=TODAY + timedelta(days=30),
            adjustment_type="percentage",
            adjustment_value=Decimal("20"),
        )
        rule = await svc.create_seasonal_rule(req)
        assert rule.name == "Summer Peak"
        assert rule.is_active is True

    async def test_update_rule(self, db: AsyncSession):
        svc = ARIService(db)
        req = SeasonalRuleCreate(
            name="Original",
            start_date=TODAY,
            end_date=TODAY + timedelta(days=7),
            adjustment_type="fixed",
            adjustment_value=Decimal("200"),
        )
        rule = await svc.create_seasonal_rule(req)
        updated = await svc.update_seasonal_rule(rule.id, SeasonalRuleUpdate(name="Updated"))
        assert updated.name == "Updated"

    async def test_delete_rule(self, db: AsyncSession):
        svc = ARIService(db)
        req = SeasonalRuleCreate(
            name="Temp Rule",
            start_date=TODAY,
            end_date=TODAY + timedelta(days=3),
            adjustment_type="percentage",
            adjustment_value=Decimal("5"),
        )
        rule = await svc.create_seasonal_rule(req)
        await svc.delete_seasonal_rule(rule.id)
        with pytest.raises(NotFoundError):
            await svc.update_seasonal_rule(rule.id, SeasonalRuleUpdate(is_active=False))

    async def test_apply_seasonal_rules_updates_ari(self, db: AsyncSession):
        rt = await make_room_type(db)
        rp = await make_rate_plan(db, rt.id, base_amount=Decimal("5000"))
        await seed_ari(db, rt.id, rp.id, TODAY, rate_amount=Decimal("5000"))

        svc = ARIService(db)
        # Rule: +10% for today only
        req = SeasonalRuleCreate(
            name="Test Rule",
            room_type_id=rt.id,
            rate_plan_id=rp.id,
            start_date=TODAY,
            end_date=TODAY,
            adjustment_type="percentage",
            adjustment_value=Decimal("10"),
        )
        await svc.create_seasonal_rule(req)
        count = await svc.apply_seasonal_rules(FAKE_TENANT_ID, FAKE_USER_ID, look_ahead_days=1)
        assert count >= 1
        resp = await svc.get_calendar(rt.id, TODAY, TODAY)
        cell = resp.room_types[0].rate_plans[0].cells.get(TODAY.isoformat())
        assert cell is not None
        assert cell.rate_amount == Decimal("5500.00")


class TestBlackoutDates:
    async def test_create_blackout_closes_ari(self, db: AsyncSession):
        rt = await make_room_type(db)
        rp = await make_rate_plan(db, rt.id)
        await seed_ari(db, rt.id, rp.id, TODAY, is_closed=False)

        svc = ARIService(db)
        bd = await svc.create_blackout_date(
            BlackoutDateCreate(date=TODAY, reason="Maintenance"),
            FAKE_USER_ID,
            FAKE_TENANT_ID,
        )
        assert bd.date == TODAY

        resp = await svc.get_calendar(rt.id, TODAY, TODAY)
        assert resp.room_types[0].rate_plans[0].cells[TODAY.isoformat()].is_closed is True

    async def test_duplicate_blackout_raises(self, db: AsyncSession):
        svc = ARIService(db)
        await svc.create_blackout_date(
            BlackoutDateCreate(date=TODAY), FAKE_USER_ID, FAKE_TENANT_ID
        )
        with pytest.raises(ConflictError):
            await svc.create_blackout_date(
                BlackoutDateCreate(date=TODAY), FAKE_USER_ID, FAKE_TENANT_ID
            )

    async def test_delete_blackout_reopens_ari(self, db: AsyncSession):
        rt = await make_room_type(db)
        rp = await make_rate_plan(db, rt.id)
        await seed_ari(db, rt.id, rp.id, TODAY, is_closed=False)

        svc = ARIService(db)
        bd = await svc.create_blackout_date(
            BlackoutDateCreate(date=TODAY), FAKE_USER_ID, FAKE_TENANT_ID
        )
        await svc.delete_blackout_date(bd.id, FAKE_TENANT_ID)

        resp = await svc.get_calendar(rt.id, TODAY, TODAY)
        assert resp.room_types[0].rate_plans[0].cells[TODAY.isoformat()].is_closed is False
