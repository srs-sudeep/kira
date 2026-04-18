"""Shared FastAPI dependencies for channel-engine.

Re-exports the type aliases from core.tenant for router convenience.
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
