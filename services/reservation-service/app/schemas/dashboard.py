"""Dashboard API response models (aligned with web-app dashboard-service.ts)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class KpiSummaryResponse(BaseModel):
    total_reservations: int
    reservations_change_pct: float
    total_revenue: float
    revenue_change_pct: float
    occupancy_rate: float
    occupancy_change_pct: float
    cancellation_rate: float
    cancellation_change_pct: float
    period_label: str


class TodaySnapshotResponse(BaseModel):
    arrivals: int
    departures: int
    stay_overs: int
    no_shows: int
    total_occupied: int
    total_rooms: int
    occupancy_pct: float


class OccupancyDataPoint(BaseModel):
    date: str
    occupancy_pct: float
    occupied_rooms: int
    available_rooms: int


class BookingSourceRow(BaseModel):
    channel: str
    display_name: str
    count: int
    percentage: float
    revenue: float


SyncStatusUi = Literal["synced", "pending", "failed", "partial"]


class ChannelHealthRow(BaseModel):
    channel_id: str
    ota: str
    display_name: str
    sync_status: SyncStatusUi
    last_synced_at: datetime | None
    pending_changes: int = 0
    error_count_24h: int = 0
