"""
Mock Notification Provider — Phase 8
"""
from __future__ import annotations

from app.common.logger.logger import get_logger
from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.services.notification_providers.base_provider import BaseNotificationProvider

logger = get_logger(__name__)


class MockNotificationProvider(BaseNotificationProvider):
    """
    Development/Mock provider adapter for isolated local testing.
    Logs payload details without external API calls.
    """

    def __init__(self, channel_type: NotificationChannel = NotificationChannel.IN_APP) -> None:
        self._channel = channel_type

    @property
    def channel(self) -> NotificationChannel:
        return self._channel

    @property
    def provider_name(self) -> str:
        return "mock"

    def send(self, notification: Notification, db: Session | None = None) -> tuple[NotificationStatus, str | None]:
        logger.info(
            "[MOCK PROVIDER] channel=%s | recipient=%s (%s) | title='%s' | body='%s'",
            notification.channel,
            notification.recipient_name,
            notification.recipient_contact,
            notification.title,
            notification.body,
        )
        return NotificationStatus.SENT, None
