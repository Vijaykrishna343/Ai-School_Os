"""
Notification Service — Phase 8 Production-Grade Communication Architecture
Handles provider selection, template resolution, preference checking, idempotency, retry handling, and user inbox management.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from uuid import UUID
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, case

from app.common.exceptions import BadRequestException, NotFoundException, ValidationException
from app.common.logger.logger import get_logger
from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationRecipientType,
    NotificationStatus,
)
from app.models.communication import (
    UserCommunicationPreference,
    NotificationTemplate,
    InAppNotificationRead,
)
from app.models.audit_log import AuditLog
from app.services.notification_providers import (
    BaseNotificationProvider,
    MockNotificationProvider,
    EmailNotificationProvider,
    SmsNotificationProvider,
    WhatsAppNotificationProvider,
    InAppNotificationProvider,
)

logger = get_logger(__name__)

# Fallback default notification templates
DEFAULT_NOTIFICATION_TEMPLATES: dict[str, dict[str, str]] = {
    "student_absent_alert": {
        "title": "Absence Alert: {student_name}",
        "body": "Dear Parent, your child {student_name} was marked ABSENT on {date}. Please contact school if you have any questions.",
        "category": "ATTENDANCE",
    },
    "student_absence": {
        "title": "Absence Alert: {student_name}",
        "body": "Dear Parent, your child {student_name} was marked ABSENT on {date}. Please contact school if you have any questions.",
        "category": "ATTENDANCE",
    },
    "student.absent": {
        "title": "Absence Alert: {student_name}",
        "body": "Dear Parent, your child {student_name} was marked ABSENT on {date}. Please contact school if you have any questions.",
        "category": "ATTENDANCE",
    },
    "homework_published": {
        "title": "New Homework: {title}",
        "body": "New homework published for {subject_name}: {title}. Due date: {due_date}.",
        "category": "ACADEMIC",
    },
    "homework.published": {
        "title": "New Homework: {title}",
        "body": "New homework published for {subject_name}: {title}. Due date: {due_date}.",
        "category": "ACADEMIC",
    },
    "student_late_arrival": {
        "title": "Late Arrival Alert",
        "body": "Dear Parent, your child {student_name} arrived LATE to school on {date}.",
        "category": "ATTENDANCE",
    },
    "fee_due_reminder": {
        "title": "Fee Payment Reminder",
        "body": "Dear Parent, fee payment of ₹{amount} for {student_name} is due by {due_date}. Please pay at your earliest convenience.",
        "category": "FEES",
    },
    "fee_payment_received": {
        "title": "Fee Payment Confirmed",
        "body": "Fee payment of ₹{amount} received for {student_name} on {date}. Receipt No: {receipt_number}. Thank you.",
        "category": "FEES",
    },
    "fee.payment_received": {
        "title": "Fee Payment Confirmed",
        "body": "Fee payment of ₹{amount} received for {student_name} on {date}. Receipt No: {receipt_number}. Thank you.",
        "category": "FEES",
    },
    "exam_results_published": {
        "title": "Exam Results Published",
        "body": "Results for {exam_name} have been published for {student_name}. Please log in to view the report card.",
        "category": "EXAMS",
    },
    "event_created_announcement": {
        "title": "New School Event: {event_title}",
        "body": "Event '{event_title}' is scheduled on {date} at {venue}. Audience: {audience_scope}.",
        "category": "EVENTS",
    },
    "hostel_outpass_status": {
        "title": "Hostel Outpass Update: {status}",
        "body": "Outpass request for {student_name} from {start_date} to {end_date} has been {status}.",
        "category": "HOSTEL",
    },
    "staff_leave_submitted": {
        "title": "Staff Leave Request Submitted",
        "body": "Leave request for {requested_days} day(s) from {start_date} to {end_date} submitted by {staff_name}.",
        "category": "LEAVE",
    },
    "staff_leave_approved": {
        "title": "Staff Leave Request Approved",
        "body": "Your leave request from {start_date} to {end_date} has been APPROVED.",
        "category": "LEAVE",
    },
    "staff_leave_rejected": {
        "title": "Staff Leave Request Rejected",
        "body": "Your leave request from {start_date} to {end_date} was REJECTED. Reason: {rejection_reason}.",
        "category": "LEAVE",
    },
    "general_announcement": {
        "title": "{title}",
        "body": "{message}",
        "category": "ANNOUNCEMENT",
    },
    "emergency_alert": {
        "title": "EMERGENCY: {title}",
        "body": "{message}",
        "category": "EMERGENCY",
    },
    "visitor_checkin": {
        "title": "Visitor Alert: {visitor_name}",
        "body": "Visitor Alert: {visitor_name} has arrived at the reception desk to meet you. Purpose: {purpose}. Gate Pass: {pass_number}.",
        "category": "VISITORS",
    },
    "visitor.checkin": {
        "title": "Visitor Alert: {visitor_name}",
        "body": "Visitor Alert: {visitor_name} has arrived at the reception desk to meet you. Purpose: {purpose}. Gate Pass: {pass_number}.",
        "category": "VISITORS",
    },
    "visitor_checkout": {
        "title": "Visitor Departure: {visitor_name}",
        "body": "Visitor Departure: {visitor_name} has checked out from the reception desk. Gate Pass: {pass_number}.",
        "category": "VISITORS",
    },
    "visitor.checkout": {
        "title": "Visitor Departure: {visitor_name}",
        "body": "Visitor Departure: {visitor_name} has checked out from the reception desk. Gate Pass: {pass_number}.",
        "category": "VISITORS",
    },
}


class NotificationService:
    """
    Core Communication & Notification Service.
    Provider-independent, multi-channel dispatch with preference checking, template rendering, and retry capabilities.
    """

    def __init__(self) -> None:
        self._providers: dict[NotificationChannel, BaseNotificationProvider] = {
            NotificationChannel.EMAIL: EmailNotificationProvider(),
            NotificationChannel.SMS: SmsNotificationProvider(),
            NotificationChannel.WHATSAPP: WhatsAppNotificationProvider(),
            NotificationChannel.IN_APP: InAppNotificationProvider(),
        }

    def _get_provider(self, channel: NotificationChannel) -> BaseNotificationProvider:
        """Returns provider adapter for specified channel."""
        return self._providers.get(channel, MockNotificationProvider(channel))

    def get_provider_statuses(self) -> list[dict[str, str | bool]]:
        """Returns status of all channel provider adapters."""
        statuses = []
        for channel, provider in self._providers.items():
            is_cfg = provider.is_configured()
            statuses.append({
                "channel": channel.value,
                "provider_name": provider.provider_name,
                "is_configured": is_cfg,
                "status": "CONFIGURED" if is_cfg else "MOCK_DEVELOPMENT",
            })
        return statuses

    # ── TEMPLATE RESOLUTION ───────────────────────────────────────────────────

    def render_template(
        self, db: Session | None, school_id: UUID | None, template_key: str, variables: dict[str, str]
    ) -> tuple[str, str, str]:
        """
        Renders template using database DB template or fallback defaults.
        Returns tuple of (title, body, category).
        """
        db_tpl = None
        if db is not None and school_id is not None:
            db_tpl = db.scalar(
                select(NotificationTemplate).where(
                    or_(NotificationTemplate.school_id == school_id, NotificationTemplate.school_id.is_(None)),
                    NotificationTemplate.template_key == template_key,
                    NotificationTemplate.is_active.is_(True),
                    NotificationTemplate.is_deleted.is_(False),
                ).order_by(NotificationTemplate.school_id.desc())
            )

        if db_tpl:
            title_fmt = db_tpl.title_template
            body_fmt = db_tpl.body_template
            category = db_tpl.category
        else:
            fallback = DEFAULT_NOTIFICATION_TEMPLATES.get(template_key, DEFAULT_NOTIFICATION_TEMPLATES["general_announcement"])
            title_fmt = fallback["title"]
            body_fmt = fallback["body"]
            category = fallback.get("category", "ANNOUNCEMENT")

        # Safe String Formatting (replaces missing keys with blank)
        class SafeDict(dict):
            def __missing__(self, key: str) -> str:
                return f"{{{key}}}"

        safe_vars = SafeDict(variables)
        try:
            title = title_fmt.format_map(safe_vars)
            body = body_fmt.format_map(safe_vars)
        except Exception as err:
            logger.warning("Error rendering notification template %s: %s", template_key, err)
            title = variables.get("title", "Notification")
            body = variables.get("message", "")

        return title, body, category

    # ── USER PREFERENCE EVALUATION ─────────────────────────────────────────────

    def should_deliver(
        self, db: Session, school_id: UUID, user_id: UUID | None, channel: NotificationChannel, category: str
    ) -> bool:
        """
        Evaluates user communication preferences.
        Emergency alerts are mandatory and bypass user preferences.
        """
        if category == "EMERGENCY":
            return True

        if not user_id:
            return True

        pref = db.scalar(
            select(UserCommunicationPreference).where(
                UserCommunicationPreference.school_id == school_id,
                UserCommunicationPreference.user_id == user_id,
                UserCommunicationPreference.is_deleted.is_(False),
            )
        )
        if not pref:
            return True  # Defaults to True if no explicit preferences saved

        # Check channel preference
        if channel == NotificationChannel.IN_APP and not pref.enable_in_app:
            return False
        if channel == NotificationChannel.EMAIL and not pref.enable_email:
            return False
        if channel == NotificationChannel.SMS and not pref.enable_sms:
            return False
        if channel == NotificationChannel.WHATSAPP and not pref.enable_whatsapp:
            return False

        # Check category preference
        cat_upper = category.upper()
        if cat_upper == "ATTENDANCE" and not pref.enable_attendance:
            return False
        if cat_upper == "FEES" and not pref.enable_fees:
            return False
        if cat_upper == "EXAMS" and not pref.enable_exams:
            return False
        if cat_upper == "EVENTS" and not pref.enable_events:
            return False
        if cat_upper == "HOSTEL" and not pref.enable_hostel:
            return False
        if cat_upper == "LEAVE" and not pref.enable_leave:
            return False
        if cat_upper in ("ANNOUNCEMENT", "ANNOUNCEMENTS") and not pref.enable_announcements:
            return False

        return True

    # ── DISPATCH & RETRY ENGINE ────────────────────────────────────────────────

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
        idempotency_key: str | None = None,
    ) -> Notification:
        """
        Creates and dispatches a notification through provider abstraction with idempotency check.
        """
        title, body, category = self.render_template(db, school_id, template_key, template_variables)

        # 1. Idempotency Check (prevent duplicate sends)
        if idempotency_key:
            existing = db.scalar(
                select(Notification).where(
                    Notification.school_id == school_id,
                    Notification.idempotency_key == idempotency_key,
                    Notification.is_deleted.is_(False),
                )
            )
            if existing:
                logger.info("Idempotency key '%s' matched existing notification %s", idempotency_key, existing.id)
                return existing

        # 2. Preference Check
        if not self.should_deliver(db, school_id, recipient_id, channel, category):
            logger.info(
                "Notification to user %s cancelled by communication preference (channel=%s, category=%s)",
                recipient_id,
                channel,
                category,
            )
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
                status=NotificationStatus.CANCELLED,
                error_message="Cancelled by user communication preference",
                idempotency_key=idempotency_key,
            )
            db.add(notification)
            db.flush()
            return notification

        # 3. Create Notification entity
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
            idempotency_key=idempotency_key,
            retry_count=0,
            max_retries=3,
        )
        db.add(notification)
        db.flush()

        # 4. Dispatch through channel provider
        provider = self._get_provider(channel)
        try:
            status, error = provider.send(notification, db=db)
            notification.status = status
            notification.error_message = error
            if status == NotificationStatus.SENT:
                notification.sent_at = datetime.now(timezone.utc)
        except Exception as exc:
            logger.exception("Provider exception for notification %s: %s", notification.id, exc)
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(exc)

        db.flush()
        return notification

    def retry_failed_notification(
        self,
        db: Session,
        school_id: UUID,
        notification_id: UUID,
        user_id: UUID | None = None,
        user_email: str | None = None,
    ) -> Notification:
        """
        Retries dispatching a failed or pending notification.
        """
        notification = db.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.school_id == school_id,
                Notification.is_deleted.is_(False),
            )
        )
        if not notification:
            raise NotFoundException("Notification", str(notification_id))

        if notification.status not in (NotificationStatus.FAILED, NotificationStatus.PENDING):
            raise ValidationException(f"Only FAILED or PENDING notifications can be retried. Current status is {notification.status.value}.")

        if notification.retry_count >= notification.max_retries:
            raise ValidationException(f"Maximum retries ({notification.max_retries}) exceeded for notification.")

        notification.retry_count += 1
        provider = self._get_provider(notification.channel)

        try:
            status, error = provider.send(notification, db=db)
            notification.status = status
            notification.error_message = error
            if status == NotificationStatus.SENT:
                notification.sent_at = datetime.now(timezone.utc)
            elif error and ("DLT Error" in error or "missing" in error.lower() or "disabled" in error.lower() or "NONE" in error):
                # Permanent configuration error: do not continue retrying
                notification.max_retries = notification.retry_count
        except Exception as exc:
            logger.exception("Retry provider exception for notification %s: %s", notification.id, exc)
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(exc)

        # Audit Log Entry with sanitized metadata
        try:
            audit = AuditLog(
                school_id=school_id,
                user_id=user_id,
                user_email=user_email or "system@school.internal",
                action="NOTIFICATION_RETRY",
                module="NOTIFICATION",
                entity_type="NOTIFICATION",
                entity_id=str(notification.id),
                details=json.dumps({
                    "notification_id": str(notification.id),
                    "channel": notification.channel.value if hasattr(notification.channel, "value") else str(notification.channel),
                    "template_key": notification.template_key,
                    "retry_count": notification.retry_count,
                    "max_retries": notification.max_retries,
                    "status": notification.status.value if hasattr(notification.status, "value") else str(notification.status),
                }),
            )
            db.add(audit)
        except Exception as audit_exc:
            logger.warning("Failed to record retry audit log: %s", audit_exc)

        db.commit()
        db.refresh(notification)
        return notification

    def get_notification_detail(
        self, db: Session, school_id: UUID, notification_id: UUID
    ) -> Notification:
        """
        Retrieves single notification by ID strictly scoped to school_id.
        """
        notification = db.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.school_id == school_id,
                Notification.is_deleted.is_(False),
            )
        )
        if not notification:
            raise NotFoundException("Notification", str(notification_id))
        return notification

    # ── USER INBOX & READ STATE ───────────────────────────────────────────────

    def get_user_inbox(
        self, db: Session, school_id: UUID, user_id: UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[dict[str, Any]], int, int]:
        """
        Retrieves in-app notification inbox for a user with read/unread tracking.
        Returns (items, total_count, unread_count).
        """
        # User notifications matching recipient_id or in-app channel
        query = select(Notification).where(
            Notification.school_id == school_id,
            or_(Notification.recipient_id == user_id, Notification.channel == NotificationChannel.IN_APP),
            Notification.is_deleted.is_(False),
        )

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

        # Read notifications IDs for this user
        read_ids = set(
            db.scalars(
                select(InAppNotificationRead.notification_id).where(
                    InAppNotificationRead.school_id == school_id,
                    InAppNotificationRead.user_id == user_id,
                    InAppNotificationRead.is_deleted.is_(False),
                )
            ).all()
        )

        offset = (page - 1) * page_size
        notifications = db.scalars(query.order_by(Notification.created_at.desc()).offset(offset).limit(page_size)).all()

        items = []
        unread_count = 0
        for n in notifications:
            is_read = n.id in read_ids
            if not is_read:
                unread_count += 1
            items.append({
                "id": str(n.id),
                "title": n.title,
                "body": n.body,
                "template_key": n.template_key,
                "channel": n.channel.value,
                "status": n.status.value,
                "is_read": is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            })

        # Calculate total unread count across inbox
        total_unread = total - len(read_ids) if total > len(read_ids) else 0

        return items, total, max(0, total_unread)

    def mark_as_read(self, db: Session, school_id: UUID, user_id: UUID, notification_id: UUID) -> bool:
        """Marks single notification read for a user."""
        notif = db.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.school_id == school_id,
                Notification.is_deleted.is_(False),
            )
        )
        if not notif:
            raise NotFoundException("Notification", str(notification_id))

        existing = db.scalar(
            select(InAppNotificationRead).where(
                InAppNotificationRead.school_id == school_id,
                InAppNotificationRead.user_id == user_id,
                InAppNotificationRead.notification_id == notification_id,
                InAppNotificationRead.is_deleted.is_(False),
            )
        )
        if not existing:
            read_record = InAppNotificationRead(
                school_id=school_id,
                user_id=user_id,
                notification_id=notification_id,
            )
            db.add(read_record)
            db.commit()
        return True

    def mark_all_as_read(self, db: Session, school_id: UUID, user_id: UUID) -> int:
        """Marks all in-app notifications read for a user."""
        user_notifs = db.scalars(
            select(Notification.id).where(
                Notification.school_id == school_id,
                or_(Notification.recipient_id == user_id, Notification.channel == NotificationChannel.IN_APP),
                Notification.is_deleted.is_(False),
            )
        ).all()

        read_ids = set(
            db.scalars(
                select(InAppNotificationRead.notification_id).where(
                    InAppNotificationRead.school_id == school_id,
                    InAppNotificationRead.user_id == user_id,
                    InAppNotificationRead.is_deleted.is_(False),
                )
            ).all()
        )

        new_reads = 0
        for nid in user_notifs:
            if nid not in read_ids:
                db.add(InAppNotificationRead(school_id=school_id, user_id=user_id, notification_id=nid))
                new_reads += 1

        db.commit()
        return new_reads

    # ── USER PREFERENCES GET/UPDATE ───────────────────────────────────────────

    def get_user_preferences(self, db: Session, school_id: UUID, user_id: UUID) -> UserCommunicationPreference:
        """Gets user communication preferences or initializes defaults."""
        pref = db.scalar(
            select(UserCommunicationPreference).where(
                UserCommunicationPreference.school_id == school_id,
                UserCommunicationPreference.user_id == user_id,
                UserCommunicationPreference.is_deleted.is_(False),
            )
        )
        if not pref:
            pref = UserCommunicationPreference(
                school_id=school_id,
                user_id=user_id,
                enable_in_app=True,
                enable_email=True,
                enable_sms=True,
                enable_whatsapp=True,
                enable_attendance=True,
                enable_fees=True,
                enable_exams=True,
                enable_events=True,
                enable_hostel=True,
                enable_leave=True,
                enable_emergency=True,
                enable_announcements=True,
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)
        return pref

    def update_user_preferences(
        self, db: Session, school_id: UUID, user_id: UUID, updates: dict[str, bool]
    ) -> UserCommunicationPreference:
        """Updates user communication preferences."""
        pref = self.get_user_preferences(db, school_id, user_id)

        # Allow updating optional preferences; emergency remains True
        for key, val in updates.items():
            if hasattr(pref, key) and key != "enable_emergency":
                setattr(pref, key, bool(val))

        pref.enable_emergency = True  # Mandatory safety invariant
        db.commit()
        db.refresh(pref)
        return pref

    # ── TEMPLATES MANAGEMENT ──────────────────────────────────────────────────

    def get_templates(self, db: Session, school_id: UUID) -> list[dict[str, Any]]:
        """Returns all custom DB templates combined with default templates."""
        db_tpls = db.scalars(
            select(NotificationTemplate).where(
                or_(NotificationTemplate.school_id == school_id, NotificationTemplate.school_id.is_(None)),
                NotificationTemplate.is_deleted.is_(False),
            )
        ).all()

        res = []
        seen_keys = set()
        for t in db_tpls:
            seen_keys.add(t.template_key)
            res.append({
                "id": str(t.id),
                "template_key": t.template_key,
                "name": t.name,
                "category": t.category,
                "title_template": t.title_template,
                "body_template": t.body_template,
                "is_active": t.is_active,
                "is_custom": True,
                "dlt_entity_id": t.dlt_entity_id,
                "dlt_template_id": t.dlt_template_id,
                "whatsapp_template_name": t.whatsapp_template_name,
                "whatsapp_language_code": t.whatsapp_language_code,
            })

        for key, fallback in DEFAULT_NOTIFICATION_TEMPLATES.items():
            if key not in seen_keys:
                res.append({
                    "id": f"default-{key}",
                    "template_key": key,
                    "name": key.replace("_", " ").title(),
                    "category": fallback.get("category", "ANNOUNCEMENT"),
                    "title_template": fallback["title"],
                    "body_template": fallback["body"],
                    "is_active": True,
                    "is_custom": False,
                    "dlt_entity_id": None,
                    "dlt_template_id": None,
                    "whatsapp_template_name": None,
                    "whatsapp_language_code": None,
                })

        return res

    def create_template(
        self,
        db: Session,
        school_id: UUID,
        template_key: str,
        name: str,
        title_template: str,
        body_template: str,
        category: str = "ANNOUNCEMENT",
        dlt_entity_id: str | None = None,
        dlt_template_id: str | None = None,
        whatsapp_template_name: str | None = None,
        whatsapp_language_code: str | None = None,
    ) -> NotificationTemplate:
        """Creates a custom template for a school with DLT/WhatsApp metadata."""
        key_upper = template_key.strip().lower()
        tpl = NotificationTemplate(
            school_id=school_id,
            template_key=key_upper,
            name=name.strip(),
            category=category.upper(),
            title_template=title_template.strip(),
            body_template=body_template.strip(),
            is_active=True,
            dlt_entity_id=dlt_entity_id,
            dlt_template_id=dlt_template_id,
            whatsapp_template_name=whatsapp_template_name,
            whatsapp_language_code=whatsapp_language_code,
        )
        db.add(tpl)
        db.commit()
        db.refresh(tpl)
        return tpl

    # ── METRICS & CONVENIENCE HELPERS ──────────────────────────────────────────

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

    def get_delivery_metrics(self, db: Session, school_id: UUID) -> dict[str, Any]:
        """Returns structured delivery metrics and channel counts."""
        analytics = self.get_notification_analytics(db=db, school_id=school_id)
        return {
            "total_notifications": analytics["total_notifications"],
            "sent_count": analytics["sent_count"] + analytics["delivered_count"],
            "failed_count": analytics["failed_count"],
            "pending_count": analytics["pending_count"],
            "cancelled_count": analytics["cancelled_count"],
            "failure_rate_percent": analytics["failure_rate_percent"],
            "by_channel": analytics["by_channel"],
            "providers": analytics["providers"],
        }

    def get_notification_analytics(
        self,
        db: Session,
        school_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Database-side aggregated delivery metrics, channel/event breakdown, and daily volume.
        All aggregations are computed database-side and strictly tenant-scoped.
        """
        filters = [
            Notification.school_id == school_id,
            Notification.is_deleted.is_(False),
        ]
        if start_date is not None:
            filters.append(Notification.created_at >= start_date)
        if end_date is not None:
            filters.append(Notification.created_at <= end_date)

        base_cond = and_(*filters)

        # 1. Status Aggregation
        status_rows = db.execute(
            select(Notification.status, func.count(Notification.id))
            .where(base_cond)
            .group_by(Notification.status)
        ).all()

        status_counts = {st: 0 for st in NotificationStatus}
        for st, count in status_rows:
            if isinstance(st, NotificationStatus):
                status_counts[st] = count
            elif isinstance(st, str) and st in NotificationStatus.__members__:
                status_counts[NotificationStatus[st]] = count

        sent_count = status_counts.get(NotificationStatus.SENT, 0)
        delivered_count = status_counts.get(NotificationStatus.DELIVERED, 0)
        failed_count = status_counts.get(NotificationStatus.FAILED, 0)
        pending_count = status_counts.get(NotificationStatus.PENDING, 0) + status_counts.get(NotificationStatus.QUEUED, 0)
        cancelled_count = status_counts.get(NotificationStatus.CANCELLED, 0)
        total = sum(status_counts.values())

        # 2. Channel Distribution
        channel_rows = db.execute(
            select(Notification.channel, func.count(Notification.id))
            .where(base_cond)
            .group_by(Notification.channel)
        ).all()
        by_channel = {ch.value: 0 for ch in NotificationChannel}
        for ch, count in channel_rows:
            ch_key = ch.value if hasattr(ch, "value") else str(ch)
            by_channel[ch_key] = count

        # 3. Event Distribution
        event_rows = db.execute(
            select(Notification.template_key, func.count(Notification.id))
            .where(base_cond)
            .group_by(Notification.template_key)
        ).all()
        by_event = {str(evt): count for evt, count in event_rows}

        # 4. Rates
        success_rate = round(((sent_count + delivered_count) / total * 100), 2) if total > 0 else 0.0
        failure_rate = round((failed_count / total * 100), 2) if total > 0 else 0.0
        pending_rate = round((pending_count / total * 100), 2) if total > 0 else 0.0

        # 5. Daily Volume (Database-side date grouping)
        daily_rows = db.execute(
            select(
                func.date(Notification.created_at).label("day"),
                func.count(Notification.id).label("total"),
                func.sum(
                    case(
                        (Notification.status.in_([NotificationStatus.SENT, NotificationStatus.DELIVERED]), 1),
                        else_=0,
                    )
                ).label("sent_delivered"),
                func.sum(
                    case(
                        (Notification.status == NotificationStatus.FAILED, 1),
                        else_=0,
                    )
                ).label("failed_count"),
            )
            .where(base_cond)
            .group_by(func.date(Notification.created_at))
            .order_by(func.date(Notification.created_at).asc())
        ).all()

        daily_volume = [
            {
                "date": str(row.day),
                "count": int(row.total),
                "sent": int(row.sent_delivered or 0),
                "failed": int(row.failed_count or 0),
            }
            for row in daily_rows
        ]

        return {
            "total_notifications": total,
            "sent_count": sent_count,
            "delivered_count": delivered_count,
            "failed_count": failed_count,
            "pending_count": pending_count,
            "cancelled_count": cancelled_count,
            "success_rate_percent": success_rate,
            "failure_rate_percent": failure_rate,
            "pending_rate_percent": pending_rate,
            "by_channel": by_channel,
            "by_event": by_event,
            "daily_volume": daily_volume,
            "providers": self.get_provider_statuses(),
        }


notification_service = NotificationService()


def render_template(template_key: str, variables: dict[str, str]) -> tuple[str, str]:
    """
    Exposed module-level wrapper that delegates template rendering to notification_service.
    """
    title, body, _ = notification_service.render_template(
        db=None,
        school_id=None,
        template_key=template_key,
        variables=variables,
    )
    return title, body
