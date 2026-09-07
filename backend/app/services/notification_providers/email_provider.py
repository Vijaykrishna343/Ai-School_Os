"""
Email Notification Provider Adapter — Phase 8
Supports SMTP / SendGrid production configuration with fallback to mock.
"""
from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.common.logger.logger import get_logger
from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.services.notification_providers.base_provider import BaseNotificationProvider

logger = get_logger(__name__)


class EmailNotificationProvider(BaseNotificationProvider):
    def __init__(self) -> None:
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.sender_email = os.getenv("SMTP_SENDER_EMAIL", "noreply@aischoolos.com")

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.EMAIL

    @property
    def provider_name(self) -> str:
        return "smtp" if self.is_configured() else "mock_email"

    def is_configured(self) -> bool:
        return bool(self.smtp_server and self.smtp_username and self.smtp_password)

    def send(self, notification: Notification) -> tuple[NotificationStatus, str | None]:
        if not self.is_configured():
            logger.info(
                "[MOCK EMAIL PROVIDER] (SMTP Not Configured) recipient=%s <%s> | subject='%s'",
                notification.recipient_name,
                notification.recipient_contact,
                notification.title,
            )
            return NotificationStatus.SENT, None

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = notification.title
            msg["From"] = self.sender_email
            msg["To"] = notification.recipient_contact

            text_body = notification.body
            html_body = f"""
            <html>
              <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
                  <h2 style="color: #4f46e5; margin-top: 0;">{notification.title}</h2>
                  <p>{notification.body}</p>
                  <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;" />
                  <p style="font-size: 11px; color: #777;">This is an automated notification from AI School OS. Please do not reply directly to this email.</p>
                </div>
              </body>
            </html>
            """

            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.sender_email, [notification.recipient_contact], msg.as_string())

            logger.info("Email successfully dispatched via SMTP to %s", notification.recipient_contact)
            return NotificationStatus.SENT, None
        except Exception as exc:
            logger.error("SMTP Email dispatch failed to %s: %s", notification.recipient_contact, exc)
            return NotificationStatus.FAILED, f"SMTP Error: {exc}"
