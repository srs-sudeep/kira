"""Authentication business logic: register, login, MFA, token rotation, logout."""

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    MFA_PENDING_EXPIRE_MINUTES,
    create_access_token,
    create_mfa_pending_token,
    create_refresh_token,
    decode_mfa_pending_token,
    generate_totp_secret,
    get_totp_provisioning_uri,
    hash_password,
    hash_token,
    verify_password,
    verify_totp,
)
from app.exceptions import ConflictError, UnauthorizedError, ValidationError
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MfaSetupResponse,
    MfaVerifyRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
)
from app.schemas.user import UserResponse

logger = structlog.get_logger(__name__)

LOCK_AFTER_FAILURES = 5
LOCK_DURATION_MINUTES = 15


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._user_repo = UserRepository(session)
        self._audit_repo = AuditRepository(session)

    # ── Registration ──────────────────────────────────────────────────────────

    async def register_user(
        self,
        req: RegisterRequest,
        *,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        if await self._user_repo.get_by_email(req.email):
            raise ConflictError(f"Email '{req.email}' is already registered.")

        user = await self._user_repo.create(
            email=req.email,
            hashed_password=hash_password(req.password),
            first_name=req.first_name,
            last_name=req.last_name,
            role="property_owner",
            tenant_id=req.tenant_id,
        )
        await self._audit_repo.create(
            action="user.registered",
            tenant_id=req.tenant_id,
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip,
            user_agent=user_agent,
        )
        logger.info("user_registered", user_id=str(user.id), email=user.email)
        return user

    # ── Login ─────────────────────────────────────────────────────────────────

    async def authenticate(
        self,
        req: LoginRequest,
        *,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> LoginResponse:
        user = await self._user_repo.get_by_email(req.email)

        if user is None or not user.is_active:
            # Constant-time-ish: do a dummy verify to resist timing attacks
            verify_password("dummy", "$2b$12$aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.")
            raise UnauthorizedError("Invalid credentials.")

        # ── Account lock check ────────────────────────────────────────────────
        if user.locked_until and datetime.now(UTC) < user.locked_until.replace(tzinfo=UTC):
            raise UnauthorizedError(
                f"Account locked until {user.locked_until.isoformat()}. Too many failed login attempts."
            )

        if not verify_password(req.password, user.hashed_password):
            await self._user_repo.increment_failed_attempts(user)
            if user.failed_login_attempts >= LOCK_AFTER_FAILURES:
                lock_until = datetime.now(UTC) + timedelta(minutes=LOCK_DURATION_MINUTES)
                await self._user_repo.lock_until(user, lock_until)
                logger.warning(
                    "account_locked",
                    user_id=str(user.id),
                    locked_until=lock_until.isoformat(),
                )
                raise UnauthorizedError(f"Account locked for {LOCK_DURATION_MINUTES} minutes after too many failures.")
            raise UnauthorizedError("Invalid credentials.")

        # Password correct — reset failure counter
        await self._user_repo.reset_failed_attempts(user)
        await self._user_repo.update(user, last_login_at=datetime.now(UTC))

        await self._audit_repo.create(
            action="user.login",
            tenant_id=user.tenant_id,
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip,
            user_agent=user_agent,
        )

        # ── MFA check ─────────────────────────────────────────────────────────
        if user.mfa_enabled:
            mfa_pending = create_mfa_pending_token(user_id=str(user.id), email=user.email)
            return LoginResponse(
                access_token="",
                refresh_token="",
                expires_in=MFA_PENDING_EXPIRE_MINUTES * 60,
                user_id=user.id,
                role=user.role,
                mfa_required=True,
                mfa_token=mfa_pending,
                user=None,
            )

        return await self._issue_full_tokens(user)

    # ── MFA verify (second step) ──────────────────────────────────────────────

    async def verify_mfa(
        self,
        mfa_pending_token: str,
        req: MfaVerifyRequest,
        *,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> LoginResponse:
        payload = decode_mfa_pending_token(mfa_pending_token)
        user = await self._user_repo.get_by_id(uuid.UUID(payload["sub"]))
        if user is None or not user.is_active:
            raise UnauthorizedError("User not found or inactive.")
        if not user.mfa_enabled or not user.mfa_secret:
            raise ValidationError("MFA is not enabled for this account.")
        if not verify_totp(user.mfa_secret, req.totp_code):
            raise UnauthorizedError("Invalid TOTP code.")

        await self._audit_repo.create(
            action="user.mfa_verified",
            tenant_id=user.tenant_id,
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip,
            user_agent=user_agent,
        )
        return await self._issue_full_tokens(user)

    # ── MFA setup / enable ────────────────────────────────────────────────────

    async def setup_mfa(self, user: User) -> MfaSetupResponse:
        """Generate a TOTP secret and persist it. MFA is not active until enable_mfa."""
        secret = generate_totp_secret()
        await self._user_repo.update(user, mfa_secret=secret)
        provisioning_uri = get_totp_provisioning_uri(secret, user.email)
        logger.info("mfa_setup_initiated", user_id=str(user.id))
        # QR rendering is intentionally left to the frontend (use provisioning_uri)
        return MfaSetupResponse(
            secret=secret,
            provisioning_uri=provisioning_uri,
            qr_code_base64="",
        )

    async def enable_mfa(self, user: User, req: MfaVerifyRequest) -> None:
        """Confirm TOTP works before flipping mfa_enabled=True."""
        if not user.mfa_secret:
            raise ValidationError("Call /mfa/setup before /mfa/enable.")
        if not verify_totp(user.mfa_secret, req.totp_code):
            raise UnauthorizedError("Invalid TOTP code.")
        await self._user_repo.update(user, mfa_enabled=True)
        await self._audit_repo.create(
            action="user.mfa_enabled",
            tenant_id=user.tenant_id,
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
        )
        logger.info("mfa_enabled", user_id=str(user.id))

    # ── Token rotation ────────────────────────────────────────────────────────

    async def refresh_token(self, req: RefreshRequest) -> RefreshResponse:
        token_hash = hash_token(req.refresh_token)
        rt = await self._user_repo.get_refresh_token_by_hash(token_hash)

        if rt is None or rt.revoked:
            raise UnauthorizedError("Refresh token is invalid or has been revoked.")
        if rt.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
            raise UnauthorizedError("Refresh token has expired.")

        user = await self._user_repo.get_by_id(rt.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("User not found or inactive.")

        # Rotate: revoke old, issue new
        await self._user_repo.revoke_refresh_token(rt)
        raw_rt, rt_hash = create_refresh_token()
        expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self._user_repo.create_refresh_token(user_id=user.id, token_hash=rt_hash, expires_at=expires_at)

        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            role=user.role,
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
        )
        return RefreshResponse(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ── Logout ────────────────────────────────────────────────────────────────

    async def logout(
        self,
        refresh_token_raw: str,
        user: User,
        *,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        token_hash = hash_token(refresh_token_raw)
        rt = await self._user_repo.get_refresh_token_by_hash(token_hash)
        if rt and not rt.revoked:
            await self._user_repo.revoke_refresh_token(rt)
        await self._audit_repo.create(
            action="user.logout",
            tenant_id=user.tenant_id,
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip,
            user_agent=user_agent,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _issue_full_tokens(self, user: User) -> LoginResponse:
        raw_rt, rt_hash = create_refresh_token()
        expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self._user_repo.create_refresh_token(user_id=user.id, token_hash=rt_hash, expires_at=expires_at)
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            role=user.role,
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
        )
        return LoginResponse(
            access_token=access_token,
            refresh_token=raw_rt,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            role=user.role,
            mfa_required=False,
            user=UserResponse.model_validate(user),
            mfa_token=None,
        )
