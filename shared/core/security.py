"""KIRA security helpers — JWT creation/verification and password hashing."""
from __future__ import annotations

from datetime import timedelta

from jose import JWTError, jwt
from pwdlib import PasswordHash

from shared.utils.datetime_utils import utcnow

pwd_hash = PasswordHash.recommended()

ALGORITHM = "HS256"


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    return pwd_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_hash.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(
    subject: str,
    tenant_id: str,
    roles: list[str],
    secret_key: str,
    expires_minutes: int = 60,
) -> str:
    expire = utcnow() + timedelta(minutes=expires_minutes)
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "roles": roles,
        "exp": expire,
        "iat": utcnow(),
        "type": "access",
    }
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def create_refresh_token(
    subject: str,
    tenant_id: str,
    secret_key: str,
    expires_days: int = 7,
) -> str:
    expire = utcnow() + timedelta(days=expires_days)
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "exp": expire,
        "iat": utcnow(),
        "type": "refresh",
    }
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def decode_token(token: str, secret_key: str) -> dict:
    """
    Decode and verify a JWT.  Raises :class:`JWTError` if the token is
    invalid, expired, or tampered with.
    """
    return jwt.decode(token, secret_key, algorithms=[ALGORITHM])


def is_token_valid(token: str, secret_key: str) -> bool:
    try:
        decode_token(token, secret_key)
        return True
    except JWTError:
        return False
