"""
Base Notification Provider Interface — Phase 8
"""
from __future__ import annotations

import abc
from app.models.notification import Notification, NotificationStatus, NotificationChannel


class BaseNotificationProvider(abc.ABC):
    """
    Abstract interface for provider adapters (Email, SMS, WhatsApp, In-App, Mock).
    """

    @property
    @abc.abstractmethod
    def channel(self) -> NotificationChannel:
        """Returns the channel handled by this provider."""
        ...

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Returns provider adapter name (e.g. 'smtp', 'twilio_sms', 'twilio_whatsapp', 'mock')."""
        ...

    @abc.abstractmethod
    def send(self, notification: Notification, db: Session | None = None) -> tuple[NotificationStatus, str | None]:
        """
        Dispatches notification payload to target external provider or internal persistence.
        Returns tuple of (NotificationStatus, optional error_message).
        """
        ...

    def is_configured(self) -> bool:
        """Returns True if production credentials for this provider are configured."""
        return True
