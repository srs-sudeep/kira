"""AES-256-GCM encryption/decryption for guest PII and SHA-256 email hashing.

Wire format: nonce (12 bytes) || GCM ciphertext+tag
The 12-byte nonce is generated fresh per encryption so identical plaintexts
produce different ciphertexts — safe to store in BYTEA columns.
"""
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings


def _get_key() -> bytes:
    """Decode the 64-char hex encryption key from settings into 32 raw bytes."""
    raw = settings.encryption_key
    if len(raw) == 64:
        return bytes.fromhex(raw)
    # Assume already bytes or base64 if not hex — pad/truncate to 32 bytes as fallback
    return raw.encode()[:32].ljust(32, b"\x00")


def encrypt_pii(plaintext: str) -> bytes:
    """Encrypt a plaintext string; returns nonce || ciphertext (bytes for BYTEA column)."""
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ct  # 12 + len(plaintext) + 16 (GCM tag) bytes


def decrypt_pii(ciphertext: bytes) -> str:
    """Decrypt bytes produced by encrypt_pii back to a plaintext string."""
    if len(ciphertext) < 28:  # 12 nonce + at least 0 plaintext + 16 tag
        raise ValueError("Ciphertext too short to be valid.")
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = ciphertext[:12]
    ct = ciphertext[12:]
    return aesgcm.decrypt(nonce, ct, None).decode("utf-8")


def hash_email(email: str) -> str:
    """Return the SHA-256 hex digest of the normalised email address."""
    normalised = email.strip().lower()
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()
