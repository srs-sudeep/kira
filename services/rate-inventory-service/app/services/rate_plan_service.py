"""Rate plan CRUD + derived-rate recalculation."""

import uuid
from decimal import Decimal

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.rate_plan import RatePlan
from app.repositories.rate_plan_repo import RatePlanRepository
from app.repositories.room_type_repo import RoomTypeRepository
from app.schemas.rate_plan import (
    RatePlanCreate,
    RatePlanListResponse,
    RatePlanResponse,
    RatePlanUpdate,
)

logger = structlog.get_logger(__name__)


def _compute_derived_amount(parent_amount: Decimal, derived_type: str, derived_value: Decimal) -> Decimal:
    """Recalculate a child rate plan's base_amount from its parent."""
    if derived_type == "percentage":
        return (parent_amount * (Decimal("100") + derived_value) / Decimal("100")).quantize(Decimal("0.01"))
    # fixed offset
    return (parent_amount + derived_value).quantize(Decimal("0.01"))


class RatePlanService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = RatePlanRepository(session)
        self._rt_repo = RoomTypeRepository(session)

    async def list(self, room_type_id: uuid.UUID) -> RatePlanListResponse:
        rt = await self._rt_repo.get_by_id(room_type_id)
        if rt is None or not rt.is_active:
            raise NotFoundError("RoomType", str(room_type_id))
        items = await self._repo.list_by_room_type(room_type_id)
        return RatePlanListResponse(
            items=[RatePlanResponse.model_validate(rp) for rp in items],
            total=len(items),
        )

    async def get(self, rate_plan_id: uuid.UUID) -> RatePlanResponse:
        rp = await self._repo.get_by_id(rate_plan_id)
        if rp is None or not rp.is_active:
            raise NotFoundError("RatePlan", str(rate_plan_id))
        return RatePlanResponse.model_validate(rp)

    async def create(self, room_type_id: uuid.UUID, req: RatePlanCreate) -> RatePlanResponse:
        rt = await self._rt_repo.get_by_id(room_type_id)
        if rt is None or not rt.is_active:
            raise NotFoundError("RoomType", str(room_type_id))

        data = req.model_dump()
        data["room_type_id"] = room_type_id

        # Validate parent and auto-compute base_amount for derived plan
        if req.derived_from_id:
            parent = await self._repo.get_by_id(req.derived_from_id)
            if parent is None or not parent.is_active:
                raise NotFoundError("RatePlan (parent)", str(req.derived_from_id))
            if parent.room_type_id != room_type_id:
                raise ValidationError("Parent rate plan must belong to the same room type.")
            data["base_amount"] = _compute_derived_amount(parent.base_amount, req.derived_type, req.derived_value)

        rp = await self._repo.create(**data)
        logger.info("rate_plan_created", id=str(rp.id), room_type_id=str(room_type_id))
        return RatePlanResponse.model_validate(rp)

    async def update(self, rate_plan_id: uuid.UUID, req: RatePlanUpdate) -> RatePlanResponse:
        rp = await self._repo.get_by_id(rate_plan_id)
        if rp is None or not rp.is_active:
            raise NotFoundError("RatePlan", str(rate_plan_id))

        updates = req.model_dump(exclude_none=True)
        if not updates:
            return RatePlanResponse.model_validate(rp)

        updated = await self._repo.update(rp, **updates)

        # If base_amount changed, cascade to all child (derived) plans
        if "base_amount" in updates and updated.derived_plans:
            await self._cascade_to_children(updated)

        logger.info("rate_plan_updated", id=str(rate_plan_id))
        return RatePlanResponse.model_validate(updated)

    async def delete(self, rate_plan_id: uuid.UUID) -> None:
        rp = await self._repo.get_by_id(rate_plan_id)
        if rp is None or not rp.is_active:
            raise NotFoundError("RatePlan", str(rate_plan_id))
        # Prevent deletion if children exist
        children = await self._repo.get_children(rate_plan_id)
        active_children = [c for c in children if c.is_active]
        if active_children:
            raise ConflictError(
                f"Cannot delete rate plan with {len(active_children)} active derived plan(s). "
                "Delete or reassign children first."
            )
        await self._repo.soft_delete(rp)
        logger.info("rate_plan_deleted", id=str(rate_plan_id))

    async def _cascade_to_children(self, parent: RatePlan) -> None:
        """Recursively recompute base_amount for all descendants."""
        for child in parent.derived_plans:
            if not child.is_active or not child.derived_type or child.derived_value is None:
                continue
            new_amount = _compute_derived_amount(parent.base_amount, child.derived_type, child.derived_value)
            child = await self._repo.update(child, base_amount=new_amount)
            # Recurse — load grandchildren
            grandchildren = await self._repo.get_children(child.id)
            if grandchildren:
                child_with_children = await self._repo.get_by_id(child.id)
                if child_with_children:
                    await self._cascade_to_children(child_with_children)
            logger.debug(
                "derived_rate_cascaded",
                child_id=str(child.id),
                new_amount=str(new_amount),
            )
