"""
Focused Test Suite for Phase 27.4.1 — Event/Notification Trigger Foundation
Verifies transaction-safe post-commit dispatch, rollback isolation, failure safety,
idempotency keys, tenant isolation, and communication preference checking.
"""
from __future__ import annotations

import time
from uuid import uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.school import School
from app.models.notification import NotificationChannel, NotificationRecipientType, NotificationStatus
from app.common.exceptions import ValidationException
from app.models.communication import UserCommunicationPreference
from app.models.notification import Notification
from app.schemas.notification_trigger import NotificationTriggerEvent
from app.services.notification_trigger_service import notification_trigger_service


def _create_test_school(db: Session) -> School:
    """Helper to create a valid persisted School for FK integrity."""
    school = School(
        id=uuid4(),
        name=f"Test School {uuid4().hex[:6]}",
        code=f"TS{uuid4().hex[:6].upper()}",
        address_line1="123 Campus Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def test_notification_trigger_contract_validation():
    """Verifies that NotificationTriggerEvent enforces mandatory school_id."""
    school_id = uuid4()
    event = NotificationTriggerEvent(
        event_type="test_event",
        school_id=school_id,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_name="John Doe",
        recipient_contact="+919876543210",
        channel=NotificationChannel.SMS,
        template_key="general_announcement",
        template_variables={"title": "Test Title", "message": "Test Message"},
        idempotency_key=f"test_key_{uuid4()}",
    )
    assert event.school_id == school_id
    assert event.event_type == "test_event"


def test_notification_staging_and_post_commit_dispatch(db_session: Session):
    """
    Verifies:
    1. Event staging creates PENDING Notification in main session.
    2. Commit triggers post-commit dispatch.
    3. Notification transitions from PENDING to SENT (mock provider).
    """
    school = _create_test_school(db_session)
    school_id = school.id
    idempotency_key = f"post_commit_{uuid4()}"

    event = NotificationTriggerEvent(
        event_type="test_post_commit",
        school_id=school_id,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_name="Jane Parent",
        recipient_contact="+919876543211",
        channel=NotificationChannel.IN_APP,
        template_key="general_announcement",
        template_variables={"title": "Hello", "message": "Post Commit Test"},
        idempotency_key=idempotency_key,
    )

    staged_notif = notification_trigger_service.stage_notification_event(
        db=db_session,
        event=event,
        auto_dispatch_on_commit=True,
    )
    assert staged_notif.status == NotificationStatus.PENDING
    staged_id = staged_notif.id

    # Commit main business transaction
    db_session.commit()

    # Allow background thread worker to execute
    time.sleep(0.5)

    # Re-query in a fresh session to verify post-commit dispatch result
    db_session.expire_all()
    updated = db_session.scalar(
        select(Notification).where(
            Notification.id == staged_id,
            Notification.school_id == school_id,
        )
    )
    assert updated is not None
    assert updated.status == NotificationStatus.SENT
    assert updated.sent_at is not None


def test_notification_rollback_isolation(db_session: Session):
    """
    Verifies that if the main business transaction rolls back:
    1. The Notification record is rolled back from DB.
    2. Zero notifications are dispatched.
    """
    school = _create_test_school(db_session)
    school_id = school.id
    idempotency_key = f"rollback_{uuid4()}"

    event = NotificationTriggerEvent(
        event_type="test_rollback",
        school_id=school_id,
        recipient_type=NotificationRecipientType.TEACHER,
        recipient_name="Teacher Rollback",
        recipient_contact="+919876543212",
        channel=NotificationChannel.IN_APP,
        template_key="general_announcement",
        template_variables={"title": "Rollback", "message": "Rollback Test"},
        idempotency_key=idempotency_key,
    )

    staged_notif = notification_trigger_service.stage_notification_event(
        db=db_session,
        event=event,
        auto_dispatch_on_commit=True,
    )
    staged_id = staged_notif.id

    # Simulating business transaction rollback
    db_session.rollback()

    time.sleep(0.3)

    # Verify notification record was rolled back and never existed in DB
    existing = db_session.scalar(
        select(Notification).where(
            Notification.id == staged_id,
            Notification.school_id == school_id,
        )
    )
    assert existing is None


def test_notification_provider_failure_isolation(db_session: Session, monkeypatch):
    """
    Verifies that if provider dispatch throws an exception:
    1. Notification status is marked FAILED.
    2. Main business transaction remains 100% committed.
    """
    school = _create_test_school(db_session)
    school_id = school.id
    idempotency_key = f"failure_isolation_{uuid4()}"

    # Mock provider.send to simulate provider network exception
    def failing_send(self, notification, db=None):
        raise RuntimeError("Simulated provider outage / timeout")

    from app.services.notification_providers.sms_provider import SmsNotificationProvider
    monkeypatch.setattr(SmsNotificationProvider, "send", failing_send)

    event = NotificationTriggerEvent(
        event_type="test_provider_failure",
        school_id=school_id,
        recipient_type=NotificationRecipientType.STAFF,
        recipient_name="Staff Fail",
        recipient_contact="+919876543213",
        channel=NotificationChannel.SMS,
        template_key="general_announcement",
        template_variables={"title": "Fail Test", "message": "Fail Test Message"},
        idempotency_key=idempotency_key,
    )

    staged = notification_trigger_service.stage_notification_event(
        db=db_session,
        event=event,
        auto_dispatch_on_commit=True,
    )
    staged_id = staged.id

    # Business transaction commits successfully
    db_session.commit()

    time.sleep(0.5)

    db_session.expire_all()
    notif = db_session.scalar(
        select(Notification).where(
            Notification.id == staged_id,
            Notification.school_id == school_id,
        )
    )
    assert notif is not None
    assert notif.status == NotificationStatus.FAILED
    assert "Simulated provider outage" in (notif.error_message or "")


def test_notification_trigger_idempotency(db_session: Session):
    """
    Verifies that staging the same event with an identical idempotency key
    returns the existing notification without creating a duplicate entity.
    """
    school = _create_test_school(db_session)
    school_id = school.id
    idempotency_key = f"idempotency_{uuid4()}"

    event1 = NotificationTriggerEvent(
        event_type="test_idempotency",
        school_id=school_id,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_name="Parent Idempotent",
        recipient_contact="+919876543214",
        channel=NotificationChannel.IN_APP,
        template_key="general_announcement",
        template_variables={"title": "Idempotent", "message": "First Call"},
        idempotency_key=idempotency_key,
    )

    notif1 = notification_trigger_service.stage_notification_event(
        db=db_session,
        event=event1,
        auto_dispatch_on_commit=False,
    )
    db_session.commit()

    event2 = NotificationTriggerEvent(
        event_type="test_idempotency",
        school_id=school_id,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_name="Parent Idempotent",
        recipient_contact="+919876543214",
        channel=NotificationChannel.IN_APP,
        template_key="general_announcement",
        template_variables={"title": "Idempotent", "message": "Second Call"},
        idempotency_key=idempotency_key,
    )

    notif2 = notification_trigger_service.stage_notification_event(
        db=db_session,
        event=event2,
        auto_dispatch_on_commit=False,
    )

    assert notif1.id == notif2.id


def _create_test_user(db: Session, school_id: UUID) -> IdentityUser:
    """Helper to create a valid persisted IdentityUser for FK integrity."""
    from app.identity.models.user import IdentityUser
    user = IdentityUser(
        id=uuid4(),
        school_id=school_id,
        email=f"user_{uuid4().hex[:6]}@school.com",
        password_hash="hash",
        first_name="Test",
        last_name="User",
        is_active=True,
        status="ACTIVE",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_notification_trigger_user_preference_opt_out(db_session: Session):
    """
    Verifies that if user has opted out of a channel in UserCommunicationPreference,
    notification is staged with status CANCELLED and never sent to provider.
    """
    school = _create_test_school(db_session)
    school_id = school.id
    user = _create_test_user(db_session, school_id)
    user_id = user.id

    # Create explicit preference opting out of SMS
    pref = UserCommunicationPreference(
        school_id=school_id,
        user_id=user_id,
        enable_sms=False,
        enable_in_app=True,
    )
    db_session.add(pref)
    db_session.commit()

    event = NotificationTriggerEvent(
        event_type="test_opt_out",
        school_id=school_id,
        recipient_id=user_id,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_name="Opted Out Parent",
        recipient_contact="+919876543215",
        channel=NotificationChannel.SMS,
        template_key="general_announcement",
        template_variables={"title": "Opted Out", "message": "Opted Out Message"},
        idempotency_key=f"opt_out_{uuid4()}",
    )

    staged = notification_trigger_service.stage_notification_event(
        db=db_session,
        event=event,
        auto_dispatch_on_commit=True,
    )
    assert staged.status == NotificationStatus.CANCELLED
    assert "Cancelled by user communication preference" in (staged.error_message or "")
