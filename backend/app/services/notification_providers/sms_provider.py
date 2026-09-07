"""
SMS Notification Provider Adapter — Phase 8
Supports Twilio / Fast2SMS API production configuration with fallback to mock.
"""
from __future__ import annotations

import os

from app.common.logger.logger import get_logger
from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.services.notification_providers.base_provider import BaseNotificationProvider

logger = get_logger(__name__)


class SmsNotificationProvider(BaseNotificationProvider):
    def __init__(self) -> None:
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_from_number = os.getenv("TWILIO_PHONE_NUMBER")

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.SMS

    @property
    def provider_name(self) -> str:
        return "twilio_sms" if self.is_configured() else "mock_sms"

    def is_configured(self) -> bool:
        return bool(self.twilio_account_sid and self.twilio_auth_token and self.twilio_from_number)

    def send(self, notification: Notification) -> tuple[NotificationStatus, str | None]:
        if not self.is_configured():
            logger.info(
                "[MOCK SMS PROVIDER] (Twilio SMS Not Configured) contact=%s | message='%s'",
                notification.recipient_contact,
                notification.body,
            )
            return NotificationStatus.SENT, None

        try:
            # Production Twilio SDK call (guarded)
            from twilio.rest import Client
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            message = client.messages.create(
                body=f"{notification.title}: {notification.body}",
                from_=self.twilio_from_number,
                to=notification.recipient_contact,
            )
            logger.info("SMS sent via Twilio to %s. SID: %s", notification.recipient_contact, message.sid)
            return NotificationStatus.SENT, None
        except Exception as exc:
            logger.error("Twilio SMS dispatch failed to %s: %s", notification.recipient_contact, exc)
            return NotificationStatus.FAILED, f"Twilio SMS Error: {exc}"
