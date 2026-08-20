"""
Notification Service — Phase 9.5/9.6
Provider abstraction + MockNotificationProvider.
"""
from __future__ import annotations

import abc
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.common.logger.logger import get_logger
from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationRecipientType,
    NotificationStatus,
)

logger = get_logger(__name__)


# ── Templates ──────────────────────────────────────────────────────────────────

NOTIFICATION_TEMPLATES: dict[str, dict[str, str]] = {
    "student_absent_alert": {
        "title": "Absence Alert",
        "body": "Dear Parent, your child {student_name} was marked ABSENT on {date}. Please contact the school for any queries.",
    },
    "student_late_arrival": {
        "title": "Late Arrival Alert",
        "body": "Dear Parent, your child {student_name} arrived LATE to school on {date}.",
    },
    "fee_due_reminder": {
        "title": "Fee Payment Reminder",
        "body": "Dear Parent, fee payment of ₹{amount} for {student_name} is due by {due_date}. Please pay at the earliest.",
    },
    "fee_payment_received": {
        "title": "Fee Payment Confirmed",
        "body": "Fee payment of ₹{amount} received for {student_name} on {date}. Receipt: {receipt_number}. Thank you.",
    },
    "exam_results_published": {
        "title": "Exam Results Published",
        "body": "Results for {exam_name} have been published for {student_name}. Please log in to view the report card.",
    },
    "parent_meeting_announcement": {
        "title": "Parent-Teacher Meeting",
        "body": "Dear Parent, a Parent-Teacher Meeting is scheduled on {date} at {time}. Please attend.",
    },
    "general_announcement": {
        "title": "{title}",
        "body": "{message}",
    },
}


def render_template(template_key: str, variables: dict[str, str]) -> tuple[str, str]:
    """Render a notification template with variables. Returns (title, body)."""
    tpl = NOTIFICATION_TEMPLATES.get(template_key)
    if not tpl:
        return "Notification", variables.get("message", "")
    title = tpl["title"].format(**variables)
    body = tpl["body"].format(**variables)
    return title, body


# ── Provider Abstraction ───────────────────────────────────────────────────────

class BaseNotificationProvider(abc.ABC):
    @abc.abstractmethod
    def send(self, notification: Notification) -> tuple[NotificationStatus, str | None]:
        """Send notification. Returns (status, error_message)."""
        ...


class MockNotificationProvider(BaseNotificationProvider):
    """
    Development mock provider — logs the notification but does NOT
    send real SMS, WhatsApp, or Email messages.
    """
    def send(self, notification: Notification) -> tuple[NotificationStatus, str | None]:
        logger.info(
            "[MOCK NOTIFICATION] channel=%s | recipient=%s | contact=%s | template=%s | title=%s",
            notification.channel,
            notification.recipient_name,
            notification.recipient_contact,
            notification.template_key,
            notification.title,
        )
        return NotificationStatus.SENT, None


# ── Service ────────────────────────────────────────────────────────────────────

class NotificationService:
    """
    Creates and dispatches notifications via the configured provider.
    The active provider is determined by environment configuration.
    """

    def __init__(self) -> None:
        self._provider: BaseNotificationProvider = MockNotificationProvider()

    def _get_provider(self, channel: NotificationChannel) -> BaseNotificationProvider:
        """
        Returns the appropriate provider for the given channel.
        In development, always returns MockNotificationProvider.
        Production providers can be plugged in here via environment variables:
          - NOTIFICATION_SMS_PROVIDER=fast2sms|twilio
          - NOTIFICATION_WHATSAPP_PROVIDER=meta|gupshup
          - NOTIFICATION_EMAIL_PROVIDER=smtp|sendgrid
        """
        import os
        if channel == NotificationChannel.SMS:
            provider_name = os.getenv("NOTIFICATION_SMS_PROVIDER", "mock")
        elif channel == NotificationChannel.WHATSAPP:
            provider_name = os.getenv("NOTIFICATION_WHATSAPP_PROVIDER", "mock")
        elif channel == NotificationChannel.EMAIL:
            provider_name = os.getenv("NOTIFICATION_EMAIL_PROVIDER", "mock")
        else:
            provider_name = "mock"

        if provider_name == "mock":
            return MockNotificationProvider()

        # Future: return real providers by name
        logger.warning("Unknown provider '%s' — falling back to mock", provider_name)
        return MockNotificationProvider()

    def create_and_send(
        self,
        db: Session,
        school_id: UUID,
        recipient_type: NotificationRecipientType,
        recipient_name: str,
        recipient_contact: str,
        channel: NotificationChannel,
        template_key: str,
        template_variables: dict[str, str],
        recipient_id: UUID | None = None,
    ) -> Notification:
        """
        Create a notification record and dispatch it immediately via the mock provider.
        """
        title, body = render_template(template_key, template_variables)

        notification = Notification(
            school_id=school_id,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            recipient_name=recipient_name,
            recipient_contact=recipient_contact,
            channel=channel,
            template_key=template_key,
            title=title,
            body=body,
            status=NotificationStatus.PENDING,
        )
        db.add(notification)
        db.flush()

        provider = self._get_provider(channel)
        try:
            status, error = provider.send(notification)
            notification.status = status
            notification.error_message = error
            if status == NotificationStatus.SENT:
                notification.sent_at = datetime.now(timezone.utc)
        except Exception as exc:
            logger.exception("Notification dispatch error: %s", exc)
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(exc)

        db.flush()
        return notification

    def send_absence_alert(
        self,
        db: Session,
        school_id: UUID,
        student_name: str,
        parent_name: str,
        parent_contact: str,
        date_str: str,
        parent_id: UUID | None = None,
    ) -> Notification:
        return self.create_and_send(
            db=db,
            school_id=school_id,
            recipient_type=NotificationRecipientType.PARENT,
            recipient_name=parent_name,
            recipient_contact=parent_contact,
            channel=NotificationChannel.SMS,
            template_key="student_absent_alert",
            template_variables={"student_name": student_name, "date": date_str},
            recipient_id=parent_id,
        )

    def send_fee_receipt(
        self,
        db: Session,
        school_id: UUID,
        student_name: str,
        parent_name: str,
        parent_contact: str,
        amount: str,
        date_str: str,
        receipt_number: str,
        parent_id: UUID | None = None,
    ) -> Notification:
        return self.create_and_send(
            db=db,
            school_id=school_id,
            recipient_type=NotificationRecipientType.PARENT,
            recipient_name=parent_name,
            recipient_contact=parent_contact,
            channel=NotificationChannel.SMS,
            template_key="fee_payment_received",
            template_variables={
                "amount": amount,
                "student_name": student_name,
                "date": date_str,
                "receipt_number": receipt_number,
            },
            recipient_id=parent_id,
        )

    def send_announcement(
        self,
        db: Session,
        school_id: UUID,
        title: str,
        message: str,
        recipient_name: str,
        recipient_contact: str,
        channel: NotificationChannel = NotificationChannel.IN_APP,
    ) -> Notification:
        return self.create_and_send(
            db=db,
            school_id=school_id,
            recipient_type=NotificationRecipientType.STAFF,
            recipient_name=recipient_name,
            recipient_contact=recipient_contact,
            channel=channel,
            template_key="general_announcement",
            template_variables={"title": title, "message": message},
        )


notification_service = NotificationService()
