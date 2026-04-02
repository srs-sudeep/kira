"""KIRA crypto utilities — field-level encryption for PII storage."""
from __future__ import annotations

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def derive_fernet_key(secret: str, salt: bytes | None = None) -> tuple[Fernet, bytes]:
    """
    Derive a Fernet key from an arbitrary secret string using PBKDF2.
    Returns (Fernet instance, salt) so the salt can be persisted alongside
    the ciphertext for later decryption.
    """
    if salt is None:
        salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
    return Fernet(key), salt


def encrypt(plaintext: str, secret: str) -> str:
    """
    Encrypt a string.  Returns a ``<b64-salt>:<b64-ciphertext>`` token that
    is safe to store in the database.
    """
    fernet, salt = derive_fernet_key(secret)
    token = fernet.encrypt(plaintext.encode())
    return f"{base64.urlsafe_b64encode(salt).decode()}:{base64.urlsafe_b64encode(token).decode()}"


def decrypt(token: str, secret: str) -> str:
    """Reverse of :func:`encrypt`."""
    salt_b64, ciphertext_b64 = token.split(":", 1)
    salt = base64.urlsafe_b64decode(salt_b64)
    ciphertext = base64.urlsafe_b64decode(ciphertext_b64)
    fernet, _ = derive_fernet_key(secret, salt)
    return fernet.decrypt(ciphertext).decode()
