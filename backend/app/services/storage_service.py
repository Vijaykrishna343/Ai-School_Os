"""
Storage Service — Private file system storage provider with security validation (Phase 24).
"""
from __future__ import annotations

import hashlib
import os
import re
import uuid
from pathlib import Path
from typing import BinaryIO, Tuple

from app.common.exceptions import BadRequestException, ValidationException
from app.core.config import settings

# Allowed MIME types & corresponding file signatures (magic bytes)
ALLOWED_MIME_TYPES = {
    "application/pdf": b"%PDF-",
    "image/jpeg": b"\xff\xd8\xff",
    "image/jpg": b"\xff\xd8\xff",
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/webp": b"RIFF",
}

# Explicitly forbidden dangerous file extensions
FORBIDDEN_EXTENSIONS = {
    ".exe", ".dll", ".bat", ".cmd", ".sh", ".php", ".js", ".html", ".htm",
    ".svg", ".zip", ".tar", ".gz", ".7z", ".rar", ".py", ".vbs", ".ps1",
    ".jar", ".scr", ".pif", ".cpl", ".msi", ".com"
}

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}


class StorageService:
    def __init__(self, storage_root: str | None = None):
        self.storage_root = Path(storage_root or settings.DOCUMENT_STORAGE_PATH)

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and shell injection.
        Strips directory components and non-printable characters.
        """
        basename = Path(filename).name
        # Remove path separators and null bytes
        clean_name = re.sub(r"[^\w\s\.\-]", "_", basename).strip()
        return clean_name or "document"

    def validate_file_security(
        self,
        filename: str,
        content_type: str,
        file_bytes: bytes,
    ) -> Tuple[str, str]:
        """
        Validates extension, file size, forbidden patterns, and magic bytes.
        Returns (clean_filename, validated_mime_type).
        """
        max_bytes = settings.DOCUMENT_MAX_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise BadRequestException(
                f"File size ({len(file_bytes) / (1024*1024):.2f} MB) exceeds maximum allowed limit of {settings.DOCUMENT_MAX_SIZE_MB} MB."
            )

        if len(file_bytes) == 0:
            raise BadRequestException("Cannot upload empty (0-byte) file.")

        # Check extension
        ext = Path(filename).suffix.lower()
        if ext in FORBIDDEN_EXTENSIONS or ext not in ALLOWED_EXTENSIONS:
            raise BadRequestException(
                f"File extension '{ext}' is not permitted. Allowed extensions: PDF, JPG, PNG, WEBP."
            )

        # Check MIME type and magic bytes
        normalized_mime = content_type.lower() if content_type else "application/octet-stream"
        
        # Verify magic bytes signature
        is_valid_magic = False
        if file_bytes.startswith(b"%PDF-"):
            normalized_mime = "application/pdf"
            is_valid_magic = True
        elif file_bytes.startswith(b"\xff\xd8\xff"):
            normalized_mime = "image/jpeg"
            is_valid_magic = True
        elif file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            normalized_mime = "image/png"
            is_valid_magic = True
        elif file_bytes.startswith(b"RIFF") and b"WEBP" in file_bytes[:16]:
            normalized_mime = "image/webp"
            is_valid_magic = True

        if not is_valid_magic:
            raise ValidationException(
                "File content does not match allowed signatures (PDF, JPEG, PNG, WEBP). File may be corrupted or spoofed."
            )

        clean_filename = self.sanitize_filename(filename)
        return clean_filename, normalized_mime

    def calculate_checksum(self, file_bytes: bytes) -> str:
        """Calculate SHA-256 checksum of file contents."""
        return hashlib.sha256(file_bytes).hexdigest()

    def store_file(
        self,
        school_id: uuid.UUID,
        owner_type: str,
        owner_id: uuid.UUID,
        file_bytes: bytes,
        original_filename: str,
    ) -> Tuple[str, str]:
        """
        Saves file bytes to private local storage directory.
        Returns (storage_key, checksum).
        """
        doc_uuid = uuid.uuid4().hex
        ext = Path(original_filename).suffix.lower() or ".bin"
        
        # Construct non-guessable storage key relative path
        rel_key = f"school_{school_id.hex}/{owner_type.lower()}_{owner_id.hex}/{doc_uuid}{ext}"
        abs_path = self.storage_root / rel_key

        # Create parent directories
        abs_path.parent.mkdir(parents=True, exist_ok=True)

        # Write bytes
        with open(abs_path, "wb") as f:
            f.write(file_bytes)

        checksum = self.calculate_checksum(file_bytes)
        return rel_key, checksum

    def read_file(self, storage_key: str) -> bytes:
        """
        Reads file bytes from private storage root. Prevent path traversal.
        """
        # Ensure target path remains inside storage root
        abs_path = (self.storage_root / storage_key).resolve()
        if not str(abs_path).startswith(str(self.storage_root.resolve())):
            raise BadRequestException("Invalid or path-traversal storage key.")

        if not abs_path.exists() or not abs_path.is_file():
            raise BadRequestException("Storage file not found.")

        with open(abs_path, "rb") as f:
            return f.read()

    def delete_file(self, storage_key: str) -> bool:
        """Safely removes physical file from private storage."""
        try:
            abs_path = (self.storage_root / storage_key).resolve()
            if str(abs_path).startswith(str(self.storage_root.resolve())) and abs_path.exists():
                abs_path.unlink()
                return True
        except Exception:
            pass
        return False


storage_service = StorageService()
