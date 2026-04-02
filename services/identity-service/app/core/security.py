"""JWT creation/verification, password hashing, and TOTP utilities."""
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import pyotp
import structlog
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.exceptions import UnauthorizedError

logger = structlog.get_logger(__name__)

ALGORITHM = "HS256"
MFA_PENDING_EXPIRE_MINUTES = 5

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT helpers ───────────────────────────────────────────────────────────────

def create_access_token(
    *,
    user_id: str,
    email: str,
    role: str,
    tenant_id: str | None,
    token_type: str = "access",
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "tenant_id": tenant_id,
        "type": token_type,
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a full access token. Raises UnauthorizedError on failure."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired token.") from exc
    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type.")
    return payload


def create_mfa_pending_token(*, user_id: str, email: str) -> str:
    """Short-lived token issued after password auth when MFA is required."""
    return create_access_token(
        user_id=user_id,
        email=email,
        role="",
        tenant_id=None,
        token_type="mfa_pending",
        expires_delta=timedelta(minutes=MFA_PENDING_EXPIRE_MINUTES),
    )


def decode_mfa_pending_token(token: str) -> dict:
    """Decode a mfa_pending token. Raises UnauthorizedError on failure."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired MFA token.") from exc
    if payload.get("type") != "mfa_pending":
        raise UnauthorizedError("Expected MFA pending token.")
    return payload


# ── Refresh token helpers ─────────────────────────────────────────────────────

def create_refresh_token() -> tuple[str, str]:
    """Return (raw_token, sha256_hash). Only the hash is persisted in the DB."""
    raw = secrets.token_urlsafe(64)
    return raw, hash_token(raw)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


# ── TOTP / MFA helpers ────────────────────────────────────────────────────────

def generate_totp_secret() -> str:
    return pyotp.random_base32()


def get_totp_provisioning_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(
        name=email, issuer_name=settings.MFA_ISSUER
    )


def verify_totp(secret: str, code: str) -> bool:
    """Verify a 6-digit TOTP code. valid_window=1 allows ±30 s clock drift."""
    return pyotp.TOTP(secret).verify(code, valid_window=1)
