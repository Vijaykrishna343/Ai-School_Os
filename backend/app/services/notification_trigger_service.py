"""
Notification Trigger Service — Phase 27.4.1 Foundation
Provides transaction-safe, post-commit event notification staging and background dispatch.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import UUID
from typing import Any
from sqlalchemy import select, event as sqla_event
from sqlalchemy.orm import Session

from app.common.exceptions import BadRequestException, NotFoundException, ValidationException
from app.common.logger.logger import get_logger
from app.database.session import SessionLocal
from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationRecipientType,
    NotificationStatus,
)
from app.schemas.notification_trigger import NotificationTriggerEvent
from app.services.notification_service import notification_service

logger = get_logger(__name__)


class NotificationTriggerService:
    """
    Event-driven notification foundation service.
    Handles provider-neutral event staging, transaction-safe post-commit dispatch,
    idempotency protection, and tenant isolation.
    """

    def __init__(self, max_workers: int = 5) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="notif_trigger_worker")

    def stage_notification_event(
        self,
        db: Session,
        event: NotificationTriggerEvent,
        auto_dispatch_on_commit: bool = True,
    ) -> Notification:
        """
        Stages a notification event within an ongoing database transaction.
        Checks idempotency, evaluates user communication preferences, renders templates,
        and attaches a post-commit listener to dispatch background notification after commit.
        """
        if not event.school_id:
            raise ValidationException("Mandatory tenant school_id is missing from notification event.")

        # 1. Idempotency Protection
        if event.idempotency_key:
            existing = db.scalar(
                select(Notification).where(
                    Notification.school_id == event.school_id,
                    Notification.idempotency_key == event.idempotency_key,
                    Notification.is_deleted.is_(False),
                )
            )
            if existing:
                logger.info(
                    "Idempotency key '%s' matched existing notification %s for event '%s'",
                    event.idempotency_key,
                    existing.id,
                    event.event_type,
                )
                return existing

        # 2. Render Template
        title, body, category = notification_service.render_template(
            db=db,
            school_id=event.school_id,
            template_key=event.template_key,
            variables=event.template_variables,
        )

        # 3. Preference Evaluation
        if not notification_service.should_deliver(
            db=db,
            school_id=event.school_id,
            user_id=event.recipient_id,
            channel=event.channel,
            category=category,
        ):
            logger.info(
                "Notification for event '%s' cancelled by user preference (school=%s, user=%s, channel=%s)",
                event.event_type,
                event.school_id,
                event.recipient_id,
                event.channel,
            )
            notification = Notification(
                school_id=event.school_id,
                recipient_type=event.recipient_type,
                recipient_id=event.recipient_id,
                recipient_name=event.recipient_name,
                recipient_contact=event.recipient_contact,
                channel=event.channel,
                template_key=event.template_key,
                title=title,
                body=body,
                status=NotificationStatus.CANCELLED,
                error_message="Cancelled by user communication preference",
                idempotency_key=event.idempotency_key,
            )
            # Use a savepoint so a DB constraint error here does not poison the
            # main business transaction.  If the flush fails the savepoint is
            # automatically rolled back and the caller's try/except handles it.
            with db.begin_nested():
                db.add(notification)
                db.flush()
            return notification

        # 4. Create PENDING Notification Entity
        notification = Notification(
            school_id=event.school_id,
            recipient_type=event.recipient_type,
            recipient_id=event.recipient_id,
            recipient_name=event.recipient_name,
            recipient_contact=event.recipient_contact,
            channel=event.channel,
            template_key=event.template_key,
            title=title,
            body=body,
            status=NotificationStatus.PENDING,
            idempotency_key=event.idempotency_key,
            retry_count=0,
            max_retries=3,
        )
        # Savepoint: isolates the staging flush from the main business transaction.
        # On constraint/DB error, only the savepoint is rolled back — the session
        # remains healthy and the business commit (attendance, homework) can proceed.
        with db.begin_nested():
            db.add(notification)
            db.flush()

        # 5. Register Post-Commit Dispatch Hook (only after a successful savepoint)
        if auto_dispatch_on_commit:
            school_id = event.school_id
            notification_id = notification.id

            def _post_commit_callback(session: Session) -> None:
                logger.info(
                    "Post-commit listener triggered for notification %s (event: %s)",
                    notification_id,
                    event.event_type,
                )
                try:
                    self.dispatch_pending_notification(
                        school_id,
                        notification_id,
                        db_override=session,
                    )
                except Exception as err:
                    logger.exception("Error in post-commit notification dispatch %s: %s", notification_id, err)

            sqla_event.listen(db, "after_commit", _post_commit_callback)

        return notification

    def dispatch_pending_notification(
        self,
        school_id: UUID,
        notification_id: UUID,
        db_override: Session | None = None,
    ) -> Notification | None:
        """
        Dispatches a staged PENDING notification through the provider infrastructure.
        Executes in an isolated database transaction to guarantee provider failure isolation.
        """
        should_close = True
        if db_override is not None:
            db = Session(bind=db_override.get_bind())
        else:
            db = SessionLocal()

        try:
            notification = db.scalar(
                select(Notification).where(
                    Notification.id == notification_id,
                    Notification.school_id == school_id,
                    Notification.is_deleted.is_(False),
                )
            )
            if not notification:
                logger.warning("Pending notification %s not found for school %s", notification_id, school_id)
                return None

            if notification.status != NotificationStatus.PENDING:
                logger.info("Notification %s status is %s (not PENDING), skipping dispatch", notification_id, notification.status)
                return notification

            # Dispatch via Provider Abstraction
            provider = notification_service._get_provider(notification.channel)
            try:
                disp_status, error_msg = provider.send(notification, db=db)
                notification.status = disp_status
                notification.error_message = error_msg
                if disp_status == NotificationStatus.SENT:
                    notification.sent_at = datetime.now(timezone.utc)
                    logger.info("Successfully dispatched notification %s via %s", notification_id, notification.channel)
                else:
                    logger.warning("Notification %s dispatch result: status=%s, error=%s", notification_id, disp_status, error_msg)
            except Exception as exc:
                logger.exception("Provider dispatch error for notification %s: %s", notification_id, exc)
                notification.status = NotificationStatus.FAILED
                notification.error_message = str(exc)

            db.commit()
            db.refresh(notification)
            return notification
        except Exception as exc:
            logger.exception("Unhandled error during background notification dispatch %s: %s", notification_id, exc)
            db.rollback()
            return None
        finally:
            if should_close:
                db.close()


notification_trigger_service = NotificationTriggerService()
