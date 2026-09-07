from __future__ import annotations

import re
from typing import Any

RESTRICTED_FIELD_PATTERNS = {
    "password",
    "password_hash",
    "hash",
    "jwt",
    "token",
    "secret",
    "api_key",
    "ssn",
    "aadhaar",
    "bank_account",
    "credit_card",
}

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_REGEX = re.compile(r"\b(?:\+91|91)?[6-9]\d{9}\b")


class AIDataMinimizer:
    """
    Strips restricted fields and masks PII before payload processing.
    Produces sanitized content and a summary list of redacted categories.
    """

    @classmethod
    def sanitize_dict(cls, data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        sanitized: dict[str, Any] = {}
        redact_log: set[str] = set()

        for key, val in data.items():
            key_lower = key.lower()
            if any(pattern in key_lower for pattern in RESTRICTED_FIELD_PATTERNS):
                redact_log.add(key)
                continue  # Completely drop restricted keys

            if isinstance(val, str):
                cleaned_val, text_redactions = cls.sanitize_text(val)
                sanitized[key] = cleaned_val
                redact_log.update(text_redactions)
            elif isinstance(val, dict):
                sub_dict, sub_redactions = cls.sanitize_dict(val)
                sanitized[key] = sub_dict
                redact_log.update(sub_redactions)
            else:
                sanitized[key] = val

        return sanitized, sorted(redact_log)

    @classmethod
    def sanitize_text(cls, text: str) -> tuple[str, list[str]]:
        redactions: set[str] = set()

        # Email masking
        if EMAIL_REGEX.search(text):
            text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
            redactions.add("email")

        # Phone masking
        if PHONE_REGEX.search(text):
            text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)
            redactions.add("phone")

        return text, sorted(redactions)
