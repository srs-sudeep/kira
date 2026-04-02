"""Authentication endpoints: register, login, MFA, token management, profile."""
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.dependencies import (
    CurrentUser,
    DBSession,
    get_client_ip,
    get_user_agent,
)
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MfaSetupResponse,
    MfaVerifyRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
)
from app.schemas.user import UpdateUserRequest, UserResponse
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    req: RegisterRequest,
    db: DBSession,
    request: Request,
) -> UserResponse:
    svc = AuthService(db)
    user = await svc.register_user(
        req,
        ip=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    return UserResponse.model_validate(user)


@router.post("/login", response_model=LoginResponse)
async def login(
    req: LoginRequest,
    db: DBSession,
    request: Request,
) -> LoginResponse:
    svc = AuthService(db)
    return await svc.authenticate(
        req,
        ip=get_client_ip(request),
        user_agent=get_user_agent(request),
    )


@router.post("/login/mfa", response_model=LoginResponse)
async def login_mfa(
    req: MfaVerifyRequest,
    db: DBSession,
    request: Request,
) -> LoginResponse:
    """Second step of MFA login.

    Send the mfa_pending token (returned by /login) in the Authorization header
    and the 6-digit TOTP code in the request body.
    """
    from app.exceptions import UnauthorizedError

    auth_header: str | None = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise UnauthorizedError("MFA pending token required in Authorization header.")
    mfa_pending_token = auth_header.removeprefix("Bearer ").strip()

    svc = AuthService(db)
    return await svc.verify_mfa(
        mfa_pending_token,
        req,
        ip=get_client_ip(request),
        user_agent=get_user_agent(request),
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(req: RefreshRequest, db: DBSession) -> RefreshResponse:
    svc = AuthService(db)
    return await svc.refresh_token(req)


@router.post("/logout", status_code=204)
async def logout(
    req: RefreshRequest,
    current_user: CurrentUser,
    db: DBSession,
    request: Request,
) -> None:
    svc = AuthService(db)
    await svc.logout(
        req.refresh_token,
        current_user,
        ip=get_client_ip(request),
        user_agent=get_user_agent(request),
    )


@router.post("/mfa/setup", response_model=MfaSetupResponse)
async def mfa_setup(current_user: CurrentUser, db: DBSession) -> MfaSetupResponse:
    svc = AuthService(db)
    return await svc.setup_mfa(current_user)


@router.post("/mfa/enable", status_code=204)
async def mfa_enable(
    req: MfaVerifyRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> None:
    svc = AuthService(db)
    await svc.enable_mfa(current_user, req)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    req: UpdateUserRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> UserResponse:
    svc = UserService(db)
    updated = await svc.update_user(current_user.id, req, actor=current_user)
    return UserResponse.model_validate(updated)
