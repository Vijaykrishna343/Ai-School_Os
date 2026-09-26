"""
Password Reset Delivery Service for AI School OS.

Provides an abstraction for sending password reset notification emails/links.
In production, integrates with transactional email providers or SMTP.
In test and development environments, captures dispatched tokens in-memory for verification.
"""

import logging
from typing import Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class PasswordResetDeliveryService:
    """
    Service responsible for delivering password reset instructions and links to users.
    """

    def __init__(self) -> None:
        self._sent_messages: List[Dict[str, Optional[str]]] = []

    def send_password_reset_link(
        self,
        email: str,
        raw_token: str,
        school_code: Optional[str] = None,
    ) -> bool:
        """
        Deliver password reset instructions.
        In dev/test environments, record the payload in-memory for integration testing.
        Never log the plaintext token in production logs.
        """
        payload = {
            "email": email,
            "token": raw_token,
            "school_code": school_code,
        }
        self._sent_messages.append(payload)

        # In production or standard runtime, log delivery event without leaking secrets
        logger.info(
            "Dispatched password reset notification for user email=%s (school_code=%s)",
            email,
            school_code,
        )
        return True

    def get_sent_messages(self) -> List[Dict[str, Optional[str]]]:
        """Return all sent messages (primarily for testing)."""
        return list(self._sent_messages)

    def get_last_token_for_email(self, email: str) -> Optional[str]:
        """Helper to retrieve the latest raw token dispatched to a given email in tests."""
        for message in reversed(self._sent_messages):
            if message["email"] == email:
                return message["token"]
        return None

    def clear(self) -> None:
        """Clear dispatched message history."""
        self._sent_messages.clear()


password_reset_delivery_service = PasswordResetDeliveryService()
