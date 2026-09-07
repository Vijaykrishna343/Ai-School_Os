"""
Phase 8 Communication Provider Abstraction, Retry & Preference Suppression Tests
"""
import pytest
from uuid import uuid4
from app.database.session import SessionLocal
from app.models.school import School
from app.models.notification import NotificationChannel, NotificationRecipientType, NotificationStatus
from app.services.notification_service import notification_service


def test_provider_resolution_and_mock_fallback():
    db = SessionLocal()
    school = School(name=f"Provider Test School {uuid4().hex[:4]}", code=f"PTS-{uuid4().hex[:4]}", address_line1="123 Main St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001")
    db.add(school)
    db.commit()

    # 1. Create and Send Email Notification (uses provider adapter)
    notif = notification_service.create_and_send(
        db=db,
        school_id=school.id,
        recipient_type=NotificationRecipientType.STAFF,
        recipient_name="Teacher One",
        recipient_contact="teacher1@school.com",
        channel=NotificationChannel.EMAIL,
        template_key="general_announcement",
        template_variables={"title": "Email Test", "message": "Email body content"},
    )

    assert notif.status == NotificationStatus.SENT
    assert notif.sent_at is not None

    db.close()


def test_idempotency_duplicate_suppression():
    db = SessionLocal()
    school = School(name=f"Idem School {uuid4().hex[:4]}", code=f"IDM-{uuid4().hex[:4]}", address_line1="123 Main St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001")
    db.add(school)
    db.commit()

    key = f"idem-key-{uuid4().hex[:8]}"

    # Send first time
    n1 = notification_service.create_and_send(
        db=db,
        school_id=school.id,
        recipient_type=NotificationRecipientType.STAFF,
        recipient_name="Teacher One",
        recipient_contact="teacher1@school.com",
        channel=NotificationChannel.IN_APP,
        template_key="general_announcement",
        template_variables={"title": "Idem Test", "message": "Message"},
        idempotency_key=key,
    )

    # Send second time with same key
    n2 = notification_service.create_and_send(
        db=db,
        school_id=school.id,
        recipient_type=NotificationRecipientType.STAFF,
        recipient_name="Teacher One",
        recipient_contact="teacher1@school.com",
        channel=NotificationChannel.IN_APP,
        template_key="general_announcement",
        template_variables={"title": "Idem Test", "message": "Message"},
        idempotency_key=key,
    )

    assert n1.id == n2.id  # Same notification returned!
    db.close()


def test_user_preference_cancellation_and_emergency_override():
    db = SessionLocal()
    school = School(name=f"Pref Test School {uuid4().hex[:8]}", code=f"PFS-{uuid4().hex[:8]}", address_line1="123 Main St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001")
    db.add(school)
    db.commit()

    from app.identity.models.user import IdentityUser
    user = IdentityUser(
        email=f"prefuser.{uuid4().hex[:6]}@test.com",
        username=f"prefuser_{uuid4().hex[:6]}",
        password_hash="testpass",
        first_name="Pref",
        last_name="User",
        school_id=school.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    user_id = user.id

    # Disable SMS preference
    notification_service.update_user_preferences(
        db=db,
        school_id=school.id,
        user_id=user_id,
        updates={"enable_sms": False, "enable_fees": False},
    )

    # 1. Send Fee SMS (should be CANCELLED)
    cancelled_n = notification_service.create_and_send(
        db=db,
        school_id=school.id,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_name="Parent One",
        recipient_contact="9876543210",
        channel=NotificationChannel.SMS,
        template_key="fee_due_reminder",
        template_variables={"student_name": "Student A", "amount": "5000", "due_date": "2026-09-01"},
        recipient_id=user_id,
    )
    assert cancelled_n.status == NotificationStatus.CANCELLED
    assert "Cancelled by user communication preference" in cancelled_n.error_message

    # 2. Send Emergency Alert (Emergency overrides user preferences)
    emergency_n = notification_service.create_and_send(
        db=db,
        school_id=school.id,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_name="Parent One",
        recipient_contact="9876543210",
        channel=NotificationChannel.SMS,
        template_key="emergency_alert",
        template_variables={"title": "School Closure", "message": "Severe weather alert."},
        recipient_id=user_id,
    )
    assert emergency_n.status == NotificationStatus.SENT

    db.close()
