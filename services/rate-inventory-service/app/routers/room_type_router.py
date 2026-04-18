"""Room type and rate plan endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.tenant import TenantDB, require_roles
from app.schemas.rate_plan import RatePlanCreate, RatePlanListResponse, RatePlanResponse, RatePlanUpdate
from app.schemas.room_type import RoomTypeCreate, RoomTypeListResponse, RoomTypeResponse, RoomTypeUpdate
from app.services.rate_plan_service import RatePlanService
from app.services.room_type_service import RoomTypeService

router = APIRouter(prefix="/rooms", tags=["Room Types & Rate Plans"])

_writers = Depends(require_roles("super_admin", "property_owner", "revenue_manager"))


# ── Room types ────────────────────────────────────────────────────────────────


@router.get("/types", response_model=RoomTypeListResponse)
async def list_room_types(
    db: TenantDB,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> RoomTypeListResponse:
    return await RoomTypeService(db).list(page, page_size)


@router.get("/types/{room_type_id}", response_model=RoomTypeResponse)
async def get_room_type(room_type_id: uuid.UUID, db: TenantDB) -> RoomTypeResponse:
    return await RoomTypeService(db).get(room_type_id)


@router.post("/types", response_model=RoomTypeResponse, status_code=201)
async def create_room_type(
    req: RoomTypeCreate,
    db: TenantDB,
    _: Annotated[str, _writers],
) -> RoomTypeResponse:
    return await RoomTypeService(db).create(req)


@router.patch("/types/{room_type_id}", response_model=RoomTypeResponse)
async def update_room_type(
    room_type_id: uuid.UUID,
    req: RoomTypeUpdate,
    db: TenantDB,
    _: Annotated[str, _writers],
) -> RoomTypeResponse:
    return await RoomTypeService(db).update(room_type_id, req)


@router.delete("/types/{room_type_id}", status_code=204)
async def delete_room_type(
    room_type_id: uuid.UUID,
    db: TenantDB,
    _: Annotated[str, _writers],
) -> None:
    await RoomTypeService(db).delete(room_type_id)


# ── Rate plans ────────────────────────────────────────────────────────────────


@router.get("/types/{room_type_id}/rate-plans", response_model=RatePlanListResponse)
async def list_rate_plans(room_type_id: uuid.UUID, db: TenantDB) -> RatePlanListResponse:
    return await RatePlanService(db).list(room_type_id)


@router.get("/types/{room_type_id}/rate-plans/{rate_plan_id}", response_model=RatePlanResponse)
async def get_rate_plan(room_type_id: uuid.UUID, rate_plan_id: uuid.UUID, db: TenantDB) -> RatePlanResponse:
    return await RatePlanService(db).get(rate_plan_id)


@router.post("/types/{room_type_id}/rate-plans", response_model=RatePlanResponse, status_code=201)
async def create_rate_plan(
    room_type_id: uuid.UUID,
    req: RatePlanCreate,
    db: TenantDB,
    _: Annotated[str, _writers],
) -> RatePlanResponse:
    return await RatePlanService(db).create(room_type_id, req)


@router.patch("/types/{room_type_id}/rate-plans/{rate_plan_id}", response_model=RatePlanResponse)
async def update_rate_plan(
    room_type_id: uuid.UUID,
    rate_plan_id: uuid.UUID,
    req: RatePlanUpdate,
    db: TenantDB,
    _: Annotated[str, _writers],
) -> RatePlanResponse:
    return await RatePlanService(db).update(rate_plan_id, req)


@router.delete("/types/{room_type_id}/rate-plans/{rate_plan_id}", status_code=204)
async def delete_rate_plan(
    room_type_id: uuid.UUID,
    rate_plan_id: uuid.UUID,
    db: TenantDB,
    _: Annotated[str, _writers],
) -> None:
    await RatePlanService(db).delete(rate_plan_id)
