"""Tenant management endpoints."""

import uuid

from fastapi import APIRouter, Query

from app.core.tenant import (
    CurrentTenantID,
    DB,
    require_roles,
)
from app.schemas.tenant import (
    TenantAdminUpdate,
    TenantCreate,
    TenantListResponse,
    TenantMeUpdate,
    TenantResponse,
)
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/tenants", tags=["tenants"])

# ── super_admin-only endpoints ────────────────────────────────────────────────

# NOTE: /me must be registered before /{tenant_id} to avoid path conflict.


@router.post(
    "",
    response_model=TenantResponse,
    status_code=201,
    dependencies=[require_roles("super_admin")],
)
async def create_tenant(req: TenantCreate, db: DB):
    svc = TenantService(db)
    return await svc.create_tenant(req)


@router.get(
    "",
    response_model=TenantListResponse,
    dependencies=[require_roles("super_admin")],
)
async def list_tenants(
    db: DB,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    svc = TenantService(db)
    return await svc.list_tenants(page=page, page_size=page_size)


# ── Current-tenant endpoints (property_owner + super_admin) ──────────────────


@router.get("/me", response_model=TenantResponse)
async def get_my_tenant(db: DB, tenant_id: CurrentTenantID):
    svc = TenantService(db)
    return await svc.get_my_tenant(tenant_id)


@router.patch(
    "/me",
    response_model=TenantResponse,
    dependencies=[require_roles("super_admin", "property_owner")],
)
async def update_my_tenant(
    req: TenantMeUpdate,
    db: DB,
    tenant_id: CurrentTenantID,
):
    svc = TenantService(db)
    return await svc.update_my_tenant(tenant_id, req)


# ── Per-tenant super_admin endpoints ─────────────────────────────────────────


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    dependencies=[require_roles("super_admin")],
)
async def get_tenant(tenant_id: uuid.UUID, db: DB):
    svc = TenantService(db)
    return await svc.get_tenant(tenant_id)


@router.patch(
    "/{tenant_id}",
    response_model=TenantResponse,
    dependencies=[require_roles("super_admin")],
)
async def update_tenant(
    tenant_id: uuid.UUID,
    req: TenantAdminUpdate,
    db: DB,
):
    svc = TenantService(db)
    return await svc.update_tenant(tenant_id, req)
