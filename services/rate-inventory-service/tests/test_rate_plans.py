"""Tests for rate plan CRUD and derived-rate cascade."""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.schemas.rate_plan import RatePlanCreate, RatePlanUpdate
from app.services.rate_plan_service import RatePlanService, _compute_derived_amount
from tests.conftest import make_rate_plan, make_room_type


class TestDerivedAmountCalculation:
    def test_percentage_increase(self):
        result = _compute_derived_amount(Decimal("5000"), "percentage", Decimal("10"))
        assert result == Decimal("5500.00")

    def test_percentage_decrease(self):
        result = _compute_derived_amount(Decimal("5000"), "percentage", Decimal("-10"))
        assert result == Decimal("4500.00")

    def test_fixed_increase(self):
        result = _compute_derived_amount(Decimal("5000"), "fixed", Decimal("500"))
        assert result == Decimal("5500.00")

    def test_fixed_decrease(self):
        result = _compute_derived_amount(Decimal("5000"), "fixed", Decimal("-500"))
        assert result == Decimal("4500.00")

    def test_rounds_to_two_decimal_places(self):
        result = _compute_derived_amount(Decimal("1000"), "percentage", Decimal("3"))
        assert result == Decimal("1030.00")


class TestRatePlanService:
    async def test_create_rate_plan(self, db: AsyncSession):
        rt = await make_room_type(db)
        svc = RatePlanService(db)
        req = RatePlanCreate(name="BAR", plan_type="bar", base_amount=Decimal("5000"))
        rp = await svc.create(rt.id, req)
        assert rp.name == "BAR"
        assert rp.room_type_id == rt.id
        assert rp.base_amount == Decimal("5000.00")

    async def test_create_derived_plan(self, db: AsyncSession):
        rt = await make_room_type(db)
        parent = await make_rate_plan(db, rt.id, base_amount=Decimal("5000"))
        svc = RatePlanService(db)
        req = RatePlanCreate(
            name="Non-Refundable",
            plan_type="non_refundable",
            base_amount=Decimal("1"),  # will be overridden
            derived_from_id=parent.id,
            derived_type="percentage",
            derived_value=Decimal("-10"),
        )
        child = await svc.create(rt.id, req)
        assert child.base_amount == Decimal("4500.00")
        assert child.derived_from_id == parent.id

    async def test_create_derived_plan_wrong_room_type_raises(self, db: AsyncSession):
        rt1 = await make_room_type(db, name="RT1")
        rt2 = await make_room_type(db, name="RT2")
        parent = await make_rate_plan(db, rt1.id)
        svc = RatePlanService(db)
        req = RatePlanCreate(
            name="Child",
            plan_type="non_refundable",
            base_amount=Decimal("4500"),
            derived_from_id=parent.id,
            derived_type="fixed",
            derived_value=Decimal("-500"),
        )
        with pytest.raises(ValidationError):
            await svc.create(rt2.id, req)

    async def test_update_cascades_to_children(self, db: AsyncSession):
        rt = await make_room_type(db)
        parent = await make_rate_plan(db, rt.id, base_amount=Decimal("5000"))
        child = await make_rate_plan(
            db,
            rt.id,
            name="Child",
            base_amount=Decimal("4500"),
            derived_from_id=parent.id,
            derived_type="fixed",
            derived_value=Decimal("-500"),
        )
        svc = RatePlanService(db)
        await svc.update(parent.id, RatePlanUpdate(base_amount=Decimal("6000")))
        # Child should now be 6000 - 500 = 5500
        updated_child = await svc.get(child.id)
        assert updated_child.base_amount == Decimal("5500.00")

    async def test_delete_with_active_children_raises(self, db: AsyncSession):
        rt = await make_room_type(db)
        parent = await make_rate_plan(db, rt.id)
        await make_rate_plan(
            db,
            rt.id,
            name="Child",
            base_amount=Decimal("4500"),
            derived_from_id=parent.id,
            derived_type="fixed",
            derived_value=Decimal("-500"),
        )
        svc = RatePlanService(db)
        with pytest.raises(ConflictError):
            await svc.delete(parent.id)

    async def test_delete_leaf_plan(self, db: AsyncSession):
        rt = await make_room_type(db)
        rp = await make_rate_plan(db, rt.id)
        svc = RatePlanService(db)
        await svc.delete(rp.id)
        with pytest.raises(NotFoundError):
            await svc.get(rp.id)

    async def test_list_by_room_type(self, db: AsyncSession):
        rt = await make_room_type(db)
        await make_rate_plan(db, rt.id, name="BAR")
        await make_rate_plan(db, rt.id, name="NR", plan_type="non_refundable")
        svc = RatePlanService(db)
        result = await svc.list(rt.id)
        assert result.total == 2
        names = {rp.name for rp in result.items}
        assert {"BAR", "NR"} == names

    async def test_get_nonexistent_raises(self, db: AsyncSession):
        svc = RatePlanService(db)
        with pytest.raises(NotFoundError):
            await svc.get(uuid.uuid4())


class TestRatePlanRoutes:
    async def test_list_rate_plans(self, client, db: AsyncSession):
        rt = await make_room_type(db)
        await make_rate_plan(db, rt.id)
        resp = await client.get(f"/api/v1/rooms/types/{rt.id}/rate-plans")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    async def test_create_rate_plan(self, client, db: AsyncSession):
        rt = await make_room_type(db)
        resp = await client.post(
            f"/api/v1/rooms/types/{rt.id}/rate-plans",
            json={"name": "BAR", "plan_type": "bar", "base_amount": "4999.00"},
        )
        assert resp.status_code == 201
        assert resp.json()["base_amount"] == "4999.00"

    async def test_patch_rate_plan(self, client, db: AsyncSession):
        rt = await make_room_type(db)
        rp = await make_rate_plan(db, rt.id)
        resp = await client.patch(
            f"/api/v1/rooms/types/{rt.id}/rate-plans/{rp.id}",
            json={"base_amount": "5500.00"},
        )
        assert resp.status_code == 200
        assert resp.json()["base_amount"] == "5500.00"
