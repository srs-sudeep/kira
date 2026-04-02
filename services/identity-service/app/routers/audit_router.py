"""Audit log endpoint — read-only, super_admin and property_owner only."""
import math
from typing import Annotated

from fastapi import APIRouter, Depends, Query
import uuid
from datetime import datetime

from app.dependencies import DBSession, require_roles
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.schemas.audit import AuditEventListResponse, AuditEventResponse, AuditFilterParams

router = APIRouter(prefix="/audit", tags=["Audit"])

_admins = Depends(require_roles("super_admin", "property_owner"))


@router.get("/", response_model=AuditEventListResponse)
async def list_audit_events(
    db: DBSession,
    actor: Annotated[User, _admins],
    tenant_id: uuid.UUID | None = Query(None),
    user_id: uuid.UUID | None = Query(None),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    resource_id: str | None = Query(None),
    from_dt: datetime | None = Query(None),
    to_dt: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> AuditEventListResponse:
    # Non-super-admins are restricted to their own tenant's audit log
    effective_tenant_id = (
        tenant_id if actor.role == "super_admin" else actor.tenant_id
    )

    filters = AuditFilterParams(
        tenant_id=effective_tenant_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        from_dt=from_dt,
        to_dt=to_dt,
        page=page,
        page_size=page_size,
    )
    repo = AuditRepository(db)
    events, total = await repo.list_filtered(filters)
    return AuditEventListResponse(
        items=[AuditEventResponse.model_validate(e) for e in events],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )
