"""
Credential Encryption Utility — Phase 27.1
Provides authenticated symmetric encryption (Fernet) for storing provider credentials at rest.
Derives 32-byte key securely from app SECRET_KEY.
"""
from __future__ import annotations

import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet
from app.core.config import settings
from app.common.logger.logger import get_logger

logger = get_logger(__name__)


def _get_fernet_key() -> bytes:
    """
    Derives a valid 32-byte url-safe base64 Fernet key from settings.SECRET_KEY.
    """
    secret = settings.SECRET_KEY
    if not secret:
        raise ValueError("SECRET_KEY is not configured in application settings.")
    
    # Hash secret to 32 bytes using SHA-256 and base64-encode for Fernet key compliance
    key_bytes = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_credential(plaintext: Optional[str]) -> Optional[str]:
    """
    Encrypts a plaintext secret string using Fernet authenticated encryption.
    Returns base64-encoded encrypted token string, or None if input is empty.
    """
    if not plaintext or not plaintext.strip():
        return None

    try:
        fernet = Fernet(_get_fernet_key())
        encrypted_bytes = fernet.encrypt(plaintext.strip().encode("utf-8"))
        return encrypted_bytes.decode("utf-8")
    except Exception as exc:
        logger.error("Credential encryption operation failed.")
        raise ValueError("Credential encryption failed.") from exc


def decrypt_credential(ciphertext: Optional[str]) -> Optional[str]:
    """
    Decrypts an encrypted credential token string using Fernet authenticated encryption.
    Returns decrypted plaintext string, or None if ciphertext is empty or invalid.
    """
    if not ciphertext or not ciphertext.strip():
        return None

    try:
        fernet = Fernet(_get_fernet_key())
        decrypted_bytes = fernet.decrypt(ciphertext.strip().encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except Exception:
        logger.error("Failed to decrypt credential (key mismatch or corrupted token).")
        return None


def mask_credential(val: Optional[str], length: int = 8) -> Optional[str]:
    """
    Returns a safe masked string indicator (e.g. '••••••••') if secret exists, or None.
    NEVER exposes the actual secret string.
    """
    if not val or not val.strip():
        return None
    return "•" * length
