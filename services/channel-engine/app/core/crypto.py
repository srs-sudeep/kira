"""AES-256-GCM encryption for OTA credentials stored in channels.credentials_ref.

Wire format: nonce (12 bytes) || GCM ciphertext+tag — identical to reservation-service PII crypto.
"""

import json
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings


def _get_key() -> bytes:
    raw = settings.encryption_key
    if len(raw) == 64:
        return bytes.fromhex(raw)
    return raw.encode()[:32].ljust(32, b"\x00")


def encrypt_credentials(credentials: dict[str, Any]) -> bytes:
    """JSON-encode the credentials dict then encrypt to BYTEA."""
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    plaintext = json.dumps(credentials, ensure_ascii=False).encode("utf-8")
    ct = aesgcm.encrypt(nonce, plaintext, None)
    return nonce + ct


def decrypt_credentials(ciphertext: bytes) -> dict[str, Any]:
    """Decrypt BYTEA back to the original credentials dict."""
    if len(ciphertext) < 28:
        raise ValueError("Ciphertext too short.")
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = ciphertext[:12]
    ct = ciphertext[12:]
    return json.loads(aesgcm.decrypt(nonce, ct, None).decode("utf-8"))
