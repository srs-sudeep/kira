"""AES-GCM + SHA-256 helpers for seed scripts (matches reservation + channel-engine wire format)."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _get_key(raw: str) -> bytes:
    if len(raw) == 64:
        return bytes.fromhex(raw)
    return raw.encode()[:32].ljust(32, b"\x00")


def encrypt_pii(plaintext: str, encryption_key_hex: str) -> bytes:
    key = _get_key(encryption_key_hex)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ct


def hash_email(email: str) -> str:
    normalised = email.strip().lower()
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def encrypt_credentials(credentials: dict[str, Any], encryption_key_hex: str) -> bytes:
    key = _get_key(encryption_key_hex)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    plaintext = json.dumps(credentials, ensure_ascii=False).encode("utf-8")
    ct = aesgcm.encrypt(nonce, plaintext, None)
    return nonce + ct
