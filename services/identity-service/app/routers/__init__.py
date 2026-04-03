from app.routers.audit_router import router as audit_router
from app.routers.auth_router import router as auth_router
from app.routers.permission_router import router as permission_router
from app.routers.user_router import router as user_router

__all__ = ["auth_router", "user_router", "audit_router", "permission_router"]
