"""ARI calendar, bulk updates, stop-sell, seasonal rules, blackout dates."""

import math
import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.producer import ARIUpdatedEvent, kafka_producer
from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.inventory_history import InventoryHistory
from app.repositories.ari_repo import ARIRepository
from app.repositories.blackout_date_repo import BlackoutDateRepository
from app.repositories.inventory_history_repo import InventoryHistoryRepository
from app.repositories.rate_plan_repo import RatePlanRepository
from app.repositories.room_type_repo import RoomTypeRepository
from app.repositories.seasonal_rule_repo import SeasonalRuleRepository
from app.schemas.ari import (
    ARICalendarPutRequest,
    ARICalendarResponse,
    ARICell,
    ARIRatePlanRow,
    ARIRoomTypeRow,
    BulkUpdateRequest,
    BulkUpdateResponse,
    StopSellRequest,
)
from app.schemas.blackout_date import (
    BlackoutDateCreate,
    BlackoutDateListResponse,
    BlackoutDateResponse,
)
from app.schemas.inventory_history import (
    InventoryHistoryListResponse,
    InventoryHistoryQuery,
    InventoryHistoryResponse,
)
from app.schemas.seasonal_rule import (
    SeasonalRuleCreate,
    SeasonalRuleListResponse,
    SeasonalRuleResponse,
    SeasonalRuleUpdate,
)

logger = structlog.get_logger(__name__)


def _date_range(start: date, end: date) -> list[date]:
    days = (end - start).days + 1
    return [start + timedelta(days=i) for i in range(days)]


class ARIService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID | None = None) -> None:
        self._s = session
        self._tenant_id = tenant_id
        self._ari = ARIRepository(session)
        self._rt = RoomTypeRepository(session)
        self._rp = RatePlanRepository(session)
        self._hist = InventoryHistoryRepository(session)
        self._rules = SeasonalRuleRepository(session)
        self._bd = BlackoutDateRepository(session)

    # ── Calendar read ─────────────────────────────────────────────────────────

    async def get_calendar(
        self,
        room_type_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> ARICalendarResponse:
        if end_date < start_date:
            raise ValidationError("end_date must be >= start_date.")
        if (end_date - start_date).days > 365:
            raise ValidationError("Calendar query range cannot exceed 365 days.")

        rt = await self._rt.get_by_id(room_type_id)
        if rt is None or not rt.is_active:
            raise NotFoundError("RoomType", str(room_type_id))

        rate_plans = await self._rp.list_by_room_type(room_type_id)
        rp_ids = [rp.id for rp in rate_plans]
        snapshots = await self._ari.get_range([room_type_id], rp_ids, start_date, end_date)

        # Index snapshots by (rate_plan_id, date)
        snap_index: dict[tuple[uuid.UUID, date], Any] = {(s.rate_plan_id, s.date): s for s in snapshots}
        dates = _date_range(start_date, end_date)
        date_strs = [d.isoformat() for d in dates]

        rp_rows = []
        for rp in rate_plans:
            cells: dict[str, ARICell] = {}
            for d in dates:
                snap = snap_index.get((rp.id, d))
                if snap:
                    cells[d.isoformat()] = ARICell.model_validate(snap)
            rp_rows.append(
                ARIRatePlanRow(
                    rate_plan_id=rp.id,
                    rate_plan_name=rp.name,
                    plan_type=rp.plan_type,
                    base_amount=rp.base_amount,
                    cells=cells,
                )
            )

        return ARICalendarResponse(
            start_date=start_date,
            end_date=end_date,
            dates=date_strs,
            room_types=[
                ARIRoomTypeRow(
                    room_type_id=rt.id,
                    room_type_name=rt.name,
                    physical_inventory=rt.physical_inventory,
                    rate_plans=rp_rows,
                )
            ],
        )

    # ── Calendar write (individual cells) ────────────────────────────────────

    async def update_calendar(
        self,
        req: ARICalendarPutRequest,
        changed_by: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> int:
        updated = 0
        for cell_req in req.cells:
            existing = await self._ari.get(cell_req.room_type_id, cell_req.rate_plan_id, cell_req.date)
            updates = cell_req.model_dump(exclude={"room_type_id", "rate_plan_id", "date"}, exclude_none=True)
            await self._ari.upsert(cell_req.room_type_id, cell_req.rate_plan_id, cell_req.date, updates)
            # History entries for each changed field
            history_rows = [
                InventoryHistory(
                    room_type_id=cell_req.room_type_id,
                    rate_plan_id=cell_req.rate_plan_id,
                    date=cell_req.date,
                    field_changed=field,
                    old_value=str(getattr(existing, field)) if existing else None,
                    new_value=str(value),
                    changed_by=changed_by,
                )
                for field, value in updates.items()
            ]
            if history_rows:
                await self._hist.bulk_record(history_rows)

            await kafka_producer.publish_ari_updated(
                ARIUpdatedEvent(
                    tenant_id=tenant_id,
                    room_type_id=cell_req.room_type_id,
                    rate_plan_id=cell_req.rate_plan_id,
                    start_date=cell_req.date,
                    end_date=cell_req.date,
                    changed_fields=list(updates.keys()),
                    source="manual",
                )
            )
            updated += 1
        return updated

    # ── Bulk update ───────────────────────────────────────────────────────────

    async def bulk_update(
        self,
        req: BulkUpdateRequest,
        changed_by: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> BulkUpdateResponse:
        updates: dict[str, Any] = {
            k: v
            for k, v in req.model_dump(exclude={"room_type_ids", "rate_plan_ids", "start_date", "end_date"}).items()
            if v is not None
        }
        count = await self._ari.bulk_update_fields(
            req.room_type_ids, req.rate_plan_ids, req.start_date, req.end_date, updates
        )
        # Log a summary history entry per (rt, rp) pair
        history_rows = [
            InventoryHistory(
                room_type_id=rt_id,
                rate_plan_id=rp_id,
                date=req.start_date,
                field_changed=f"bulk:{','.join(updates.keys())}",
                old_value=None,
                new_value=f"range:{req.start_date}/{req.end_date}",
                changed_by=changed_by,
            )
            for rt_id in req.room_type_ids
            for rp_id in req.rate_plan_ids
        ]
        await self._hist.bulk_record(history_rows)

        for rt_id in req.room_type_ids:
            for rp_id in req.rate_plan_ids:
                await kafka_producer.publish_ari_updated(
                    ARIUpdatedEvent(
                        tenant_id=tenant_id,
                        room_type_id=rt_id,
                        rate_plan_id=rp_id,
                        start_date=req.start_date,
                        end_date=req.end_date,
                        changed_fields=list(updates.keys()),
                        source="manual",
                    )
                )
        logger.info(
            "bulk_ari_update",
            room_types=len(req.room_type_ids),
            date_range=f"{req.start_date}/{req.end_date}",
            rows_updated=count,
        )
        return BulkUpdateResponse(updated_cells=count, start_date=req.start_date, end_date=req.end_date)

    # ── Stop-sell ─────────────────────────────────────────────────────────────

    async def stop_sell(
        self,
        req: StopSellRequest,
        changed_by: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> BulkUpdateResponse:
        count = await self._ari.apply_stop_sell(
            req.room_type_ids,
            req.rate_plan_ids,
            req.start_date,
            req.end_date,
            cta_closed=req.cta_closed,
            ctd_closed=req.ctd_closed,
        )
        history_rows = [
            InventoryHistory(
                room_type_id=rt_id,
                rate_plan_id=rp_id,
                date=req.start_date,
                field_changed="is_closed",
                old_value="false",
                new_value="true",
                changed_by=changed_by,
            )
            for rt_id in req.room_type_ids
            for rp_id in (req.rate_plan_ids or [uuid.uuid4()])  # placeholder when all plans
        ]
        await self._hist.bulk_record(history_rows)

        for rt_id in req.room_type_ids:
            for rp_id in req.rate_plan_ids or [rt_id]:
                await kafka_producer.publish_ari_updated(
                    ARIUpdatedEvent(
                        tenant_id=tenant_id,
                        room_type_id=rt_id,
                        rate_plan_id=rp_id,
                        start_date=req.start_date,
                        end_date=req.end_date,
                        changed_fields=["is_closed", "cta_closed", "ctd_closed"],
                        source="stop_sell",
                    )
                )
        logger.info("stop_sell_applied", rows=count, date_range=f"{req.start_date}/{req.end_date}")
        return BulkUpdateResponse(updated_cells=count, start_date=req.start_date, end_date=req.end_date)

    # ── Seasonal rules ────────────────────────────────────────────────────────

    async def list_seasonal_rules(self, page: int = 1, page_size: int = 50) -> SeasonalRuleListResponse:
        items, total = await self._rules.list_all(page, page_size)
        return SeasonalRuleListResponse(
            items=[SeasonalRuleResponse.model_validate(r) for r in items],
            total=total,
        )

    async def create_seasonal_rule(self, req: SeasonalRuleCreate) -> SeasonalRuleResponse:
        rule = await self._rules.create(**req.model_dump())
        logger.info("seasonal_rule_created", id=str(rule.id))
        return SeasonalRuleResponse.model_validate(rule)

    async def update_seasonal_rule(self, rule_id: uuid.UUID, req: SeasonalRuleUpdate) -> SeasonalRuleResponse:
        rule = await self._rules.get_by_id(rule_id)
        if rule is None:
            raise NotFoundError("SeasonalRule", str(rule_id))
        updates = req.model_dump(exclude_none=True)
        if updates:
            rule = await self._rules.update(rule, **updates)
        return SeasonalRuleResponse.model_validate(rule)

    async def delete_seasonal_rule(self, rule_id: uuid.UUID) -> None:
        rule = await self._rules.get_by_id(rule_id)
        if rule is None:
            raise NotFoundError("SeasonalRule", str(rule_id))
        await self._rules.delete(rule)

    async def apply_seasonal_rules(
        self,
        tenant_id: uuid.UUID,
        changed_by: uuid.UUID,
        look_ahead_days: int = 365,
    ) -> int:
        """Apply all active seasonal rules to the next N days. Called by Celery beat."""
        today = date.today()
        horizon = today + timedelta(days=look_ahead_days)
        active_rules = await self._rules.list_active()
        total_updated = 0

        for rule in active_rules:
            # Clamp rule range to [today, horizon]
            rule_start = max(rule.start_date, today)
            rule_end = min(rule.end_date, horizon)
            if rule_start > rule_end:
                continue

            # Fetch affected room types
            if rule.room_type_id:
                rt_ids = [rule.room_type_id]
            else:
                rts, _ = await self._rt.list_active(1, 500)
                rt_ids = [rt.id for rt in rts]

            for rt_id in rt_ids:
                rps = await self._rp.list_by_room_type(rt_id)
                target_rp_ids = [rule.rate_plan_id] if rule.rate_plan_id else [rp.id for rp in rps]

                for rp_id in target_rp_ids:
                    rp = next((rp for rp in rps if rp.id == rp_id), None)
                    if rp is None:
                        continue
                    new_amount = _apply_adjustment(rp.base_amount, rule.adjustment_type, rule.adjustment_value)
                    count = await self._ari.bulk_update_fields(
                        [rt_id], [rp_id], rule_start, rule_end, {"rate_amount": new_amount}
                    )
                    total_updated += count
                    await kafka_producer.publish_ari_updated(
                        ARIUpdatedEvent(
                            tenant_id=tenant_id,
                            room_type_id=rt_id,
                            rate_plan_id=rp_id,
                            start_date=rule_start,
                            end_date=rule_end,
                            changed_fields=["rate_amount"],
                            source="seasonal_rule",
                        )
                    )

        logger.info("seasonal_rules_applied", rules=len(active_rules), cells_updated=total_updated)
        return total_updated

    # ── Blackout dates ────────────────────────────────────────────────────────

    async def list_blackout_dates(self, page: int = 1, page_size: int = 50) -> BlackoutDateListResponse:
        items, total = await self._bd.list_all(page, page_size)
        return BlackoutDateListResponse(
            items=[BlackoutDateResponse.model_validate(b) for b in items],
            total=total,
        )

    async def create_blackout_date(
        self,
        req: BlackoutDateCreate,
        changed_by: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> BlackoutDateResponse:
        existing = await self._bd.get_by_date(req.date)
        if existing:
            raise ConflictError(f"Blackout date {req.date} already exists.")
        bd = await self._bd.create(req.date, req.reason)
        closed = await self._ari.close_for_date(req.date)
        # Record history for the closure (single summary entry per date)
        logger.info("blackout_date_created", date=str(req.date), cells_closed=closed)
        return BlackoutDateResponse.model_validate(bd)

    async def delete_blackout_date(
        self,
        bd_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> None:
        bd = await self._bd.get_by_id(bd_id)
        if bd is None:
            raise NotFoundError("BlackoutDate", str(bd_id))
        await self._bd.delete(bd)
        await self._ari.reopen_for_date(bd.date)
        logger.info("blackout_date_removed", date=str(bd.date))

    # ── Inventory history ─────────────────────────────────────────────────────

    async def get_history(self, q: InventoryHistoryQuery) -> InventoryHistoryListResponse:
        items, total = await self._hist.list_filtered(q)
        return InventoryHistoryListResponse(
            items=[InventoryHistoryResponse.model_validate(h) for h in items],
            total=total,
            page=q.page,
            page_size=q.page_size,
            pages=max(1, math.ceil(total / q.page_size)),
        )


# ── Module-level helpers ──────────────────────────────────────────────────────


def _apply_adjustment(base: Decimal, adj_type: str, adj_value: Decimal) -> Decimal:
    if adj_type == "percentage":
        return (base * (Decimal("100") + adj_value) / Decimal("100")).quantize(Decimal("0.01"))
    return (base + adj_value).quantize(Decimal("0.01"))
