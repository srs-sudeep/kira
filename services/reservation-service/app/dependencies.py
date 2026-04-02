"""Shared FastAPI dependencies for reservation-service.

Re-exports the type aliases defined in core.tenant so routers can import from
a single, consistent location.
"""
from app.core.tenant import (  # noqa: F401
    CurrentTenantID,
    CurrentUserID,
    RawToken,
    TenantDB,
    get_current_user_id,
    get_tenant_db,
    get_tenant_id_from_token,
    require_roles,
)
