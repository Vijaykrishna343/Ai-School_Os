"""
WhatsApp Notification Provider Adapter — Phase 8
Supports Twilio WhatsApp API / Meta Cloud API production configuration with fallback to mock.
"""
from __future__ import annotations

import os

from app.common.logger.logger import get_logger
from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.services.notification_providers.base_provider import BaseNotificationProvider

logger = get_logger(__name__)


class WhatsAppNotificationProvider(BaseNotificationProvider):
    def __init__(self) -> None:
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.WHATSAPP

    @property
    def provider_name(self) -> str:
        return "twilio_whatsapp" if self.is_configured() else "mock_whatsapp"

    def is_configured(self) -> bool:
        return bool(self.twilio_account_sid and self.twilio_auth_token and self.twilio_whatsapp_number)

    def send(self, notification: Notification) -> tuple[NotificationStatus, str | None]:
        if not self.is_configured():
            logger.info(
                "[MOCK WHATSAPP PROVIDER] (Twilio WhatsApp Not Configured) contact=%s | message='%s'",
                notification.recipient_contact,
                notification.body,
            )
            return NotificationStatus.SENT, None

        try:
            from twilio.rest import Client
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            target_number = notification.recipient_contact
            if not target_number.startswith("whatsapp:"):
                target_number = f"whatsapp:{target_number}"

            message = client.messages.create(
                body=f"*{notification.title}*\n\n{notification.body}",
                from_=self.twilio_whatsapp_number,
                to=target_number,
            )
            logger.info("WhatsApp message sent via Twilio to %s. SID: %s", target_number, message.sid)
            return NotificationStatus.SENT, None
        except Exception as exc:
            logger.error("Twilio WhatsApp dispatch failed to %s: %s", notification.recipient_contact, exc)
            return NotificationStatus.FAILED, f"Twilio WhatsApp Error: {exc}"
