"""Tests for authentication flows: register, login, MFA, refresh, logout."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_totp
from app.exceptions import ConflictError, UnauthorizedError, ValidationError
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    LoginRequest,
    MfaVerifyRequest,
    RefreshRequest,
    RegisterRequest,
)
from app.services.auth_service import LOCK_AFTER_FAILURES, AuthService
from tests.conftest import make_user


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_service(session: AsyncSession) -> AuthService:
    return AuthService(session)


# ── Register ──────────────────────────────────────────────────────────────────

class TestRegister:
    async def test_register_new_user(self, db_session: AsyncSession):
        svc = _make_service(db_session)
        req = RegisterRequest(
            email="new@example.com",
            password="Str0ng!Pass",
            first_name="Alice",
            last_name="Smith",
        )
        user = await svc.register_user(req)
        assert user.email == "new@example.com"
        assert user.first_name == "Alice"
        assert user.role == "property_owner"

    async def test_register_duplicate_email_raises(self, db_session: AsyncSession):
        svc = _make_service(db_session)
        req = RegisterRequest(
            email="dup@example.com",
            password="Str0ng!Pass",
            first_name="Bob",
            last_name="Jones",
        )
        await svc.register_user(req)
        with pytest.raises(ConflictError):
            await svc.register_user(req)

    async def test_register_email_lowercased(self, db_session: AsyncSession):
        svc = _make_service(db_session)
        req = RegisterRequest(
            email="UPPER@Example.COM",
            password="Str0ng!Pass",
            first_name="Carol",
            last_name="White",
        )
        user = await svc.register_user(req)
        assert user.email == "upper@example.com"


# ── Login ─────────────────────────────────────────────────────────────────────

class TestAuthenticate:
    async def test_login_success(self, db_session: AsyncSession, tenant_id: uuid.UUID):
        await make_user(db_session, email="login@example.com", password="Pass123!", tenant_id=tenant_id)
        svc = _make_service(db_session)
        resp = await svc.authenticate(LoginRequest(email="login@example.com", password="Pass123!"))
        assert resp.access_token
        assert resp.refresh_token
        assert resp.mfa_required is False

    async def test_login_wrong_password(self, db_session: AsyncSession, tenant_id: uuid.UUID):
        await make_user(db_session, email="bad@example.com", password="CorrectPass1!", tenant_id=tenant_id)
        svc = _make_service(db_session)
        with pytest.raises(UnauthorizedError):
            await svc.authenticate(LoginRequest(email="bad@example.com", password="WrongPass!"))

    async def test_login_nonexistent_user(self, db_session: AsyncSession):
        svc = _make_service(db_session)
        with pytest.raises(UnauthorizedError):
            await svc.authenticate(LoginRequest(email="ghost@example.com", password="AnyPass1!"))

    async def test_brute_force_locks_after_five_failures(
        self, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        user = await make_user(
            db_session, email="brute@example.com", password="RealPass1!", tenant_id=tenant_id
        )
        svc = _make_service(db_session)
        for _ in range(LOCK_AFTER_FAILURES):
            with pytest.raises(UnauthorizedError):
                await svc.authenticate(LoginRequest(email="brute@example.com", password="Wrong!"))

        # On the 5th failure the account is locked; subsequent attempts should raise
        with pytest.raises(UnauthorizedError, match="locked"):
            await svc.authenticate(LoginRequest(email="brute@example.com", password="RealPass1!"))

    async def test_inactive_user_cannot_login(self, db_session: AsyncSession):
        await make_user(
            db_session, email="inactive@example.com", password="Pass123!", is_active=False
        )
        svc = _make_service(db_session)
        with pytest.raises(UnauthorizedError):
            await svc.authenticate(LoginRequest(email="inactive@example.com", password="Pass123!"))

    async def test_mfa_enabled_returns_pending(
        self, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        import pyotp
        secret = pyotp.random_base32()
        user = await make_user(
            db_session,
            email="mfa@example.com",
            password="Pass123!",
            tenant_id=tenant_id,
            mfa_enabled=True,
        )
        user.mfa_secret = secret
        await db_session.flush()

        svc = _make_service(db_session)
        resp = await svc.authenticate(LoginRequest(email="mfa@example.com", password="Pass123!"))
        assert resp.mfa_required is True
        assert resp.refresh_token == ""


# ── MFA setup / enable ────────────────────────────────────────────────────────

class TestMfa:
    async def test_setup_mfa_returns_secret(
        self, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        user = await make_user(db_session, tenant_id=tenant_id)
        svc = _make_service(db_session)
        resp = await svc.setup_mfa(user)
        assert len(resp.secret) > 0
        assert "otpauth://" in resp.provisioning_uri

    async def test_enable_mfa_with_valid_code(
        self, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        import pyotp
        user = await make_user(db_session, tenant_id=tenant_id)
        svc = _make_service(db_session)
        setup = await svc.setup_mfa(user)

        code = pyotp.TOTP(setup.secret).now()
        await svc.enable_mfa(user, MfaVerifyRequest(totp_code=code))
        assert user.mfa_enabled is True

    async def test_enable_mfa_with_invalid_code_raises(
        self, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        user = await make_user(db_session, tenant_id=tenant_id)
        svc = _make_service(db_session)
        await svc.setup_mfa(user)

        with pytest.raises(UnauthorizedError):
            await svc.enable_mfa(user, MfaVerifyRequest(totp_code="000000"))

    async def test_enable_mfa_without_setup_raises(
        self, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        user = await make_user(db_session, tenant_id=tenant_id)
        svc = _make_service(db_session)
        with pytest.raises(ValidationError):
            await svc.enable_mfa(user, MfaVerifyRequest(totp_code="123456"))


# ── Refresh / Logout ──────────────────────────────────────────────────────────

class TestTokenRotation:
    async def test_refresh_issues_new_token(
        self, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        await make_user(db_session, email="rt@example.com", password="Pass123!", tenant_id=tenant_id)
        svc = _make_service(db_session)
        login = await svc.authenticate(LoginRequest(email="rt@example.com", password="Pass123!"))

        resp = await svc.refresh_token(RefreshRequest(refresh_token=login.refresh_token))
        assert resp.access_token != login.access_token

    async def test_refresh_token_rotation_revokes_old(
        self, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        await make_user(db_session, email="rotate@example.com", password="Pass123!", tenant_id=tenant_id)
        svc = _make_service(db_session)
        login = await svc.authenticate(LoginRequest(email="rotate@example.com", password="Pass123!"))

        await svc.refresh_token(RefreshRequest(refresh_token=login.refresh_token))
        # Reusing the old token should fail
        with pytest.raises(UnauthorizedError):
            await svc.refresh_token(RefreshRequest(refresh_token=login.refresh_token))

    async def test_logout_revokes_refresh_token(
        self, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        user = await make_user(db_session, email="out@example.com", password="Pass123!", tenant_id=tenant_id)
        svc = _make_service(db_session)
        login = await svc.authenticate(LoginRequest(email="out@example.com", password="Pass123!"))

        await svc.logout(login.refresh_token, user)
        # Token should now be revoked
        with pytest.raises(UnauthorizedError):
            await svc.refresh_token(RefreshRequest(refresh_token=login.refresh_token))


# ── HTTP integration tests ────────────────────────────────────────────────────

class TestAuthRoutes:
    async def test_register_endpoint(self, client):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "http@example.com",
                "password": "HttpPass1!",
                "first_name": "Http",
                "last_name": "User",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "http@example.com"

    async def test_login_endpoint(self, client, regular_user: User):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": regular_user.email, "password": "TestPass123!"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body.get("user") is not None
        assert body["user"]["full_name"] == f"{regular_user.first_name} {regular_user.last_name}".strip()

    async def test_login_accepts_local_dev_email(self, client, db_session, tenant_id):
        """Emails like admin@kira.local must not fail EmailStr DNS checks (local dev)."""
        await make_user(
            db_session,
            email="admin@kira.local",
            password="LocalPass123!",
            tenant_id=tenant_id,
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@kira.local", "password": "LocalPass123!"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json().get("user") is not None

    async def test_me_endpoint_requires_auth(self, client):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_me_endpoint_returns_profile(self, client, regular_user: User):
        from tests.conftest import auth_headers
        resp = await client.get("/api/v1/auth/me", headers=auth_headers(regular_user))
        assert resp.status_code == 200
        assert resp.json()["id"] == str(regular_user.id)
