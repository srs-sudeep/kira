"""ARI calendar, bulk update, stop-sell, seasonal rules, blackout dates, history."""
import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.tenant import CurrentUserID, TenantDB, require_roles
from app.schemas.ari import (
    ARICalendarPutRequest,
    ARICalendarResponse,
    BulkUpdateRequest,
    BulkUpdateResponse,
    StopSellRequest,
)
from app.schemas.blackout_date import BlackoutDateCreate, BlackoutDateListResponse, BlackoutDateResponse
from app.schemas.inventory_history import (
    InventoryHistoryListResponse,
    InventoryHistoryQuery,
)
from app.schemas.seasonal_rule import (
    SeasonalRuleCreate,
    SeasonalRuleListResponse,
    SeasonalRuleResponse,
    SeasonalRuleUpdate,
)
from app.services.ari_service import ARIService

router = APIRouter(prefix="/inventory", tags=["Inventory & ARI"])

_writers = Depends(require_roles("super_admin", "property_owner", "revenue_manager"))


def _ari(db: TenantDB, user_id: CurrentUserID) -> tuple:
    """Return (service, user_id) — thin helper to avoid repeating Depends."""
    return db, user_id


# ── ARI calendar ──────────────────────────────────────────────────────────────

@router.get("/calendar", response_model=ARICalendarResponse)
async def get_calendar(
    db: TenantDB,
    room_type_id: uuid.UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
) -> ARICalendarResponse:
    # tenant_id not available yet inside service without request context; pass None
    return await ARIService(db).get_calendar(room_type_id, start_date, end_date)


@router.put("/calendar", response_model=dict)
async def update_calendar(
    req: ARICalendarPutRequest,
    db: TenantDB,
    user_id: CurrentUserID,
    tenant_id: uuid.UUID = Query(..., description="Caller's tenant UUID"),
    _: Annotated[str, _writers] = None,
) -> dict:
    count = await ARIService(db).update_calendar(req, user_id, tenant_id)
    return {"updated_cells": count}


# ── Bulk operations ───────────────────────────────────────────────────────────

@router.post("/bulk-update", response_model=BulkUpdateResponse)
async def bulk_update(
    req: BulkUpdateRequest,
    db: TenantDB,
    user_id: CurrentUserID,
    tenant_id: uuid.UUID = Query(...),
    _: Annotated[str, _writers] = None,
) -> BulkUpdateResponse:
    return await ARIService(db).bulk_update(req, user_id, tenant_id)


@router.post("/stop-sell", response_model=BulkUpdateResponse)
async def stop_sell(
    req: StopSellRequest,
    db: TenantDB,
    user_id: CurrentUserID,
    tenant_id: uuid.UUID = Query(...),
    _: Annotated[str, _writers] = None,
) -> BulkUpdateResponse:
    return await ARIService(db).stop_sell(req, user_id, tenant_id)


# ── Seasonal rules ────────────────────────────────────────────────────────────

@router.get("/seasonal-rules", response_model=SeasonalRuleListResponse)
async def list_seasonal_rules(
    db: TenantDB,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> SeasonalRuleListResponse:
    return await ARIService(db).list_seasonal_rules(page, page_size)


@router.post("/seasonal-rules", response_model=SeasonalRuleResponse, status_code=201)
async def create_seasonal_rule(
    req: SeasonalRuleCreate,
    db: TenantDB,
    _: Annotated[str, _writers],
) -> SeasonalRuleResponse:
    return await ARIService(db).create_seasonal_rule(req)


@router.patch("/seasonal-rules/{rule_id}", response_model=SeasonalRuleResponse)
async def update_seasonal_rule(
    rule_id: uuid.UUID,
    req: SeasonalRuleUpdate,
    db: TenantDB,
    _: Annotated[str, _writers],
) -> SeasonalRuleResponse:
    return await ARIService(db).update_seasonal_rule(rule_id, req)


@router.delete("/seasonal-rules/{rule_id}", status_code=204)
async def delete_seasonal_rule(
    rule_id: uuid.UUID,
    db: TenantDB,
    _: Annotated[str, _writers],
) -> None:
    await ARIService(db).delete_seasonal_rule(rule_id)


# ── Blackout dates ────────────────────────────────────────────────────────────

@router.get("/blackout-dates", response_model=BlackoutDateListResponse)
async def list_blackout_dates(
    db: TenantDB,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> BlackoutDateListResponse:
    return await ARIService(db).list_blackout_dates(page, page_size)


@router.post("/blackout-dates", response_model=BlackoutDateResponse, status_code=201)
async def create_blackout_date(
    req: BlackoutDateCreate,
    db: TenantDB,
    user_id: CurrentUserID,
    tenant_id: uuid.UUID = Query(...),
    _: Annotated[str, _writers] = None,
) -> BlackoutDateResponse:
    return await ARIService(db).create_blackout_date(req, user_id, tenant_id)


@router.delete("/blackout-dates/{bd_id}", status_code=204)
async def delete_blackout_date(
    bd_id: uuid.UUID,
    db: TenantDB,
    tenant_id: uuid.UUID = Query(...),
    _: Annotated[str, _writers] = None,
) -> None:
    await ARIService(db).delete_blackout_date(bd_id, tenant_id)


# ── Inventory history ─────────────────────────────────────────────────────────

@router.get("/history", response_model=InventoryHistoryListResponse)
async def get_history(
    db: TenantDB,
    room_type_id: uuid.UUID | None = Query(None),
    rate_plan_id: uuid.UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    changed_by: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> InventoryHistoryListResponse:
    q = InventoryHistoryQuery(
        room_type_id=room_type_id,
        rate_plan_id=rate_plan_id,
        date_from=date_from,
        date_to=date_to,
        changed_by=changed_by,
        page=page,
        page_size=page_size,
    )
    return await ARIService(db).get_history(q)
