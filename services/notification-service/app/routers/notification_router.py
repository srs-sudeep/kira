"""Notification endpoints — list, unread count, mark read, preferences."""

import uuid

from fastapi import APIRouter, Query

from app.core.tenant import CurrentUserID, TenantDB
from app.schemas.notification import (
    MarkAllReadResponse,
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.schemas.preference import PreferencesListResponse, PreferencesUpdateRequest
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ── Notification list ─────────────────────────────────────────────────────────


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    db: TenantDB,
    current_user: CurrentUserID,
    type: list[str] | None = Query(default=None),
    is_read: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    svc = NotificationService(db)
    return await svc.list_notifications(
        current_user,
        type_filter=type,
        is_read=is_read,
        page=page,
        page_size=page_size,
    )


# ── Unread count ──────────────────────────────────────────────────────────────


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(db: TenantDB, current_user: CurrentUserID):
    svc = NotificationService(db)
    return await svc.get_unread_count(current_user)


# ── Mark all read ─────────────────────────────────────────────────────────────


@router.post("/mark-all-read", response_model=MarkAllReadResponse)
async def mark_all_read(db: TenantDB, current_user: CurrentUserID):
    svc = NotificationService(db)
    return await svc.mark_all_read(current_user)


# ── Mark single read ──────────────────────────────────────────────────────────


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: uuid.UUID,
    db: TenantDB,
    current_user: CurrentUserID,
):
    svc = NotificationService(db)
    return await svc.mark_read(notification_id, current_user)


# ── Preferences ───────────────────────────────────────────────────────────────


@router.get("/preferences", response_model=PreferencesListResponse)
async def get_preferences(db: TenantDB, current_user: CurrentUserID):
    svc = NotificationService(db)
    return await svc.get_preferences(current_user)


@router.patch("/preferences", response_model=PreferencesListResponse)
async def update_preferences(
    req: PreferencesUpdateRequest,
    db: TenantDB,
    current_user: CurrentUserID,
):
    svc = NotificationService(db)
    return await svc.update_preferences(current_user, req)
