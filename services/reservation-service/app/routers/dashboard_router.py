"""Dashboard read API — KPIs and charts for the web app."""

from fastapi import APIRouter, Query

from app.core.tenant import TenantDB
from app.schemas.dashboard import (
    BookingSourceRow,
    ChannelHealthRow,
    KpiSummaryResponse,
    OccupancyDataPoint,
    TodaySnapshotResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/kpi-summary", response_model=KpiSummaryResponse)
async def kpi_summary(
    db: TenantDB,
    days: int = Query(30, ge=1, le=365),
):
    svc = DashboardService(db)
    data = await svc.kpi_summary(days)
    return KpiSummaryResponse.model_validate(data)


@router.get("/today-snapshot", response_model=TodaySnapshotResponse)
async def today_snapshot(db: TenantDB):
    svc = DashboardService(db)
    data = await svc.today_snapshot()
    return TodaySnapshotResponse.model_validate(data)


@router.get("/occupancy-trend", response_model=list[OccupancyDataPoint])
async def occupancy_trend(
    db: TenantDB,
    days: int = Query(30, ge=1, le=90),
):
    svc = DashboardService(db)
    raw = await svc.occupancy_trend(days)
    return [OccupancyDataPoint.model_validate(r) for r in raw]


@router.get("/booking-sources", response_model=list[BookingSourceRow])
async def booking_sources(
    db: TenantDB,
    days: int = Query(30, ge=1, le=365),
):
    svc = DashboardService(db)
    raw = await svc.booking_sources(days)
    return [BookingSourceRow.model_validate(r) for r in raw]


@router.get("/channel-health", response_model=list[ChannelHealthRow])
async def channel_health(db: TenantDB):
    svc = DashboardService(db)
    raw = await svc.channel_health()
    return [ChannelHealthRow.model_validate(r) for r in raw]
