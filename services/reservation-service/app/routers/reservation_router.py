"""Reservation endpoints — create, modify, cancel, status, notes, duplicates, inbox."""
import uuid

from fastapi import APIRouter, Query

from app.core.tenant import CurrentTenantID, CurrentUserID, RawToken, TenantDB
from app.schemas.note import NoteCreate, NoteResponse
from app.schemas.reservation import (
    DuplicatesResponse,
    InboxFilters,
    ReservationCancel,
    ReservationCreate,
    ReservationDetail,
    ReservationInboxResponse,
    ReservationModify,
    ReservationStatusUpdate,
)
from app.services.reservation_service import ReservationService

router = APIRouter(prefix="/reservations", tags=["reservations"])


# ── Inbox ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=ReservationInboxResponse)
async def list_reservations(
    db: TenantDB,
    status: list[str] | None = Query(default=None),
    source: list[str] | None = Query(default=None),
    channel_id: uuid.UUID | None = None,
    check_in_from: str | None = None,
    check_in_to: str | None = None,
    check_out_from: str | None = None,
    check_out_to: str | None = None,
    guest_query: str | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    from datetime import date

    def _parse_date(s: str | None):
        return date.fromisoformat(s) if s else None

    filters = InboxFilters(
        status=status,
        source=source,
        channel_id=channel_id,
        check_in_from=_parse_date(check_in_from),
        check_in_to=_parse_date(check_in_to),
        check_out_from=_parse_date(check_out_from),
        check_out_to=_parse_date(check_out_to),
        guest_query=guest_query,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )
    svc = ReservationService(db)
    return await svc.get_inbox(filters)


# ── Detail ────────────────────────────────────────────────────────────────────

@router.get("/{reservation_id}", response_model=ReservationDetail)
async def get_reservation(
    reservation_id: uuid.UUID,
    db: TenantDB,
):
    svc = ReservationService(db)
    return await svc.get_detail(reservation_id)


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("", response_model=ReservationDetail, status_code=201)
async def create_reservation(
    req: ReservationCreate,
    db: TenantDB,
    actor_id: CurrentUserID,
    tenant_id: CurrentTenantID,
    token: RawToken,
):
    svc = ReservationService(db)
    return await svc.create_reservation(
        req, actor_id=actor_id, tenant_id=tenant_id, token=token
    )


# ── Modify ────────────────────────────────────────────────────────────────────

@router.patch("/{reservation_id}", response_model=ReservationDetail)
async def modify_reservation(
    reservation_id: uuid.UUID,
    req: ReservationModify,
    db: TenantDB,
    tenant_id: CurrentTenantID,
    token: RawToken,
):
    svc = ReservationService(db)
    return await svc.modify_reservation(
        reservation_id, req, tenant_id=tenant_id, token=token
    )


# ── Cancel ────────────────────────────────────────────────────────────────────

@router.post("/{reservation_id}/cancel", response_model=ReservationDetail)
async def cancel_reservation(
    reservation_id: uuid.UUID,
    req: ReservationCancel,
    db: TenantDB,
    tenant_id: CurrentTenantID,
    token: RawToken,
):
    svc = ReservationService(db)
    return await svc.cancel_reservation(
        reservation_id, req, tenant_id=tenant_id, token=token
    )


# ── Status transition ─────────────────────────────────────────────────────────

@router.post("/{reservation_id}/status", response_model=ReservationDetail)
async def update_status(
    reservation_id: uuid.UUID,
    req: ReservationStatusUpdate,
    db: TenantDB,
):
    svc = ReservationService(db)
    return await svc.update_status(reservation_id, req)


# ── Notes ─────────────────────────────────────────────────────────────────────

@router.post("/{reservation_id}/notes", response_model=NoteResponse, status_code=201)
async def add_note(
    reservation_id: uuid.UUID,
    req: NoteCreate,
    db: TenantDB,
    actor_id: CurrentUserID,
):
    svc = ReservationService(db)
    return await svc.add_note(reservation_id, req, actor_id)


# ── Duplicate detection ───────────────────────────────────────────────────────

@router.get("/duplicates/scan", response_model=DuplicatesResponse)
async def get_duplicates(db: TenantDB):
    svc = ReservationService(db)
    return await svc.get_duplicates()
