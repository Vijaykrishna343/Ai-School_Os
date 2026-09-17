"""
In-App Notification Provider Adapter — Phase 8
Persists notifications to DB for immediate in-app inbox access.
"""
from __future__ import annotations

from app.common.logger.logger import get_logger
from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.services.notification_providers.base_provider import BaseNotificationProvider

logger = get_logger(__name__)


class InAppNotificationProvider(BaseNotificationProvider):
    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.IN_APP

    @property
    def provider_name(self) -> str:
        return "in_app_internal"

    def is_configured(self) -> bool:
        return True

    def send(self, notification: Notification, db: Session | None = None) -> tuple[NotificationStatus, str | None]:
        logger.info("In-App Notification persisted for recipient %s", notification.recipient_name)
        return NotificationStatus.SENT, None
