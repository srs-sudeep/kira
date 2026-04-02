"""Channel endpoints — CRUD, mappings, sync log, health, manual sync."""
import uuid

from fastapi import APIRouter, Query

from app.core.tenant import CurrentTenantID, TenantDB
from app.schemas.channel import (
    ChannelCreate,
    ChannelListResponse,
    ChannelResponse,
    ChannelUpdate,
    HealthDashboardResponse,
    SyncTriggeredResponse,
)
from app.schemas.mapping import (
    MappingCreate,
    MappingListResponse,
    MappingResponse,
    MappingUpdate,
)
from app.schemas.sync_log import SyncLogPageResponse
from app.services.channel_service import ChannelService

router = APIRouter(prefix="/channels", tags=["channels"])


# ── Health dashboard (no channel ID required) ─────────────────────────────────

@router.get("/health", response_model=HealthDashboardResponse)
async def get_health_dashboard(db: TenantDB):
    svc = ChannelService(db)
    return await svc.get_health_dashboard()


# ── Channel CRUD ──────────────────────────────────────────────────────────────

@router.get("", response_model=ChannelListResponse)
async def list_channels(db: TenantDB):
    svc = ChannelService(db)
    return await svc.list_channels()


@router.post("", response_model=ChannelResponse, status_code=201)
async def create_channel(req: ChannelCreate, db: TenantDB):
    svc = ChannelService(db)
    return await svc.create_channel(req)


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(channel_id: uuid.UUID, db: TenantDB):
    svc = ChannelService(db)
    return await svc.get_channel(channel_id)


@router.patch("/{channel_id}", response_model=ChannelResponse)
async def update_channel(channel_id: uuid.UUID, req: ChannelUpdate, db: TenantDB):
    svc = ChannelService(db)
    return await svc.update_channel(channel_id, req)


@router.delete("/{channel_id}", status_code=204)
async def delete_channel(channel_id: uuid.UUID, db: TenantDB):
    svc = ChannelService(db)
    await svc.delete_channel(channel_id)


# ── Manual sync trigger ───────────────────────────────────────────────────────

@router.post("/{channel_id}/sync", response_model=SyncTriggeredResponse)
async def trigger_sync(
    channel_id: uuid.UUID,
    db: TenantDB,
    tenant_id: CurrentTenantID,
):
    from sqlalchemy import text
    svc = ChannelService(db)
    # Resolve schema_name for the task
    result = await db.execute(
        text("SELECT schema_name FROM public.tenants WHERE id = :id"),
        {"id": str(tenant_id)},
    )
    row = result.fetchone()
    schema_name = row[0] if row else "public"
    return await svc.trigger_sync(channel_id, tenant_id=tenant_id, schema_name=schema_name)


# ── Sync log ──────────────────────────────────────────────────────────────────

@router.get("/{channel_id}/sync-log", response_model=SyncLogPageResponse)
async def get_sync_log(
    channel_id: uuid.UUID,
    db: TenantDB,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    svc = ChannelService(db)
    return await svc.get_sync_log(channel_id, page=page, page_size=page_size)


# ── Channel mappings ──────────────────────────────────────────────────────────

@router.get("/{channel_id}/mapping", response_model=MappingListResponse)
async def list_mappings(channel_id: uuid.UUID, db: TenantDB):
    svc = ChannelService(db)
    return await svc.list_mappings(channel_id)


@router.post("/{channel_id}/mapping", response_model=MappingResponse, status_code=201)
async def create_mapping(channel_id: uuid.UUID, req: MappingCreate, db: TenantDB):
    svc = ChannelService(db)
    return await svc.create_mapping(channel_id, req)


@router.patch("/{channel_id}/mapping/{mapping_id}", response_model=MappingResponse)
async def update_mapping(
    channel_id: uuid.UUID,
    mapping_id: uuid.UUID,
    req: MappingUpdate,
    db: TenantDB,
):
    svc = ChannelService(db)
    return await svc.update_mapping(channel_id, mapping_id, req)


@router.delete("/{channel_id}/mapping/{mapping_id}", status_code=204)
async def delete_mapping(channel_id: uuid.UUID, mapping_id: uuid.UUID, db: TenantDB):
    svc = ChannelService(db)
    await svc.delete_mapping(channel_id, mapping_id)
