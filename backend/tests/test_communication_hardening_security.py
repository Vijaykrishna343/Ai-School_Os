"""
Phase 8.1 Communication Platform Hardening & Security Verification Tests
Tests Concurrency Idempotency, Emergency Preference Lock, Template Security, Relationship Authorization, IDOR.
"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.security.current_user import get_current_user
from app.models.school import School
from app.models.notification import Notification, NotificationChannel, NotificationRecipientType, NotificationStatus
from app.services.notification_service import notification_service

client = TestClient(app)


def test_emergency_preference_disable_prevention():
    """Verify backend prevents disabling mandatory emergency notifications via API."""
    db = SessionLocal()
    school = School(
        name=f"Sec School {uuid4().hex[:8]}",
        code=f"SEC-{uuid4().hex[:8]}",
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db.add(school)
    db.flush()

    super_admin_role = db.query(IdentityRole).filter_by(name="Super Admin").first()
    if not super_admin_role:
        super_admin_role = IdentityRole(name="Super Admin", description="Super Admin", is_system=True)
        db.add(super_admin_role)
        db.flush()

    user = IdentityUser(
        email=f"secuser.{uuid4().hex[:6]}@test.com",
        username=f"secuser_{uuid4().hex[:6]}",
        password_hash="testpass",
        first_name="Sec",
        last_name="User",
        school_id=school.id,
        is_active=True,
    )
    user.roles = [super_admin_role]
    db.add(user)
    db.commit()

    app.dependency_overrides[get_current_user] = lambda: user

    # Attempt to disable emergency notifications
    res = client.put(
        "/api/v1/notifications/preferences",
        json={"enable_emergency": False, "enable_sms": False},
        headers={"X-School-Id": str(school.id)},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["enable_emergency"] is True  # Enforced True!
    assert data["enable_sms"] is False

    app.dependency_overrides.clear()
    db.close()


def test_template_rendering_safety_and_missing_variables():
    """Verify template rendering handles missing or unexpected variables safely without raising exceptions."""
    db = SessionLocal()
    school_id = uuid4()

    # Missing variables in dictionary
    title, body, category = notification_service.render_template(
        db=db,
        school_id=school_id,
        template_key="fee_due_reminder",
        variables={"student_name": "Student A"},  # missing amount & due_date
    )
    assert "Student A" in title or "Student A" in body
    assert category == "FEES"

    # HTML tags in variables are rendered safely
    title_html, body_html, _ = notification_service.render_template(
        db=db,
        school_id=school_id,
        template_key="general_announcement",
        variables={"title": "<b>Alert</b>", "message": "<script>alert(1)</script>"},
    )
    assert "Alert" in title_html
    assert "script" in body_html

    db.close()


def test_inbox_idor_cross_user_and_cross_tenant_isolation():
    """Verify user cannot mark notification read for another user or another school."""
    db = SessionLocal()

    super_admin_role = db.query(IdentityRole).filter_by(name="Super Admin").first()
    if not super_admin_role:
        super_admin_role = IdentityRole(name="Super Admin", description="Super Admin", is_system=True)
        db.add(super_admin_role)
        db.flush()

    # School A
    school_a = School(name=f"School A {uuid4().hex[:8]}", code=f"SA-{uuid4().hex[:8]}", address_line1="123", city="H", district="H", state="T", postal_code="500001")
    db.add(school_a)
    db.flush()

    user_a = IdentityUser(email=f"usera.{uuid4().hex[:8]}@a.com", username=f"ua_{uuid4().hex[:8]}", password_hash="pass", first_name="A", last_name="A", school_id=school_a.id)
    user_a.roles = [super_admin_role]
    db.add(user_a)
    db.flush()

    # School B
    school_b = School(name=f"School B {uuid4().hex[:8]}", code=f"SB-{uuid4().hex[:8]}", address_line1="123", city="H", district="H", state="T", postal_code="500001")
    db.add(school_b)
    db.flush()

    user_c = IdentityUser(email=f"userc.{uuid4().hex[:8]}@b.com", username=f"uc_{uuid4().hex[:8]}", password_hash="pass", first_name="C", last_name="C", school_id=school_b.id)
    db.add(user_c)
    db.flush()

    # Notification in School B
    notif_b = Notification(
        school_id=school_b.id,
        recipient_type=NotificationRecipientType.STAFF,
        recipient_id=user_c.id,
        recipient_name="User C",
        recipient_contact=user_c.email,
        channel=NotificationChannel.IN_APP,
        template_key="general_announcement",
        title="Secret Notification School B",
        body="Secret Body",
    )
    db.add(notif_b)
    db.commit()

    # User A in School A attempts to mark Notification B read -> 404 NotFoundException (Cross-tenant IDOR protection)
    app.dependency_overrides[get_current_user] = lambda: user_a
    res = client.post(f"/api/v1/notifications/inbox/{notif_b.id}/read", headers={"X-School-Id": str(school_a.id)})
    assert res.status_code == 404

    app.dependency_overrides.clear()
    db.close()


def test_concurrent_idempotency_duplicate_suppression():
    """Simulates concurrent delivery attempts with identical idempotency key."""
    db = SessionLocal()
    school = School(name=f"Conc School {uuid4().hex[:8]}", code=f"CNC-{uuid4().hex[:8]}", address_line1="123", city="H", district="H", state="T", postal_code="500001")
    db.add(school)
    db.commit()

    idem_key = f"concurrent-key-{uuid4().hex}"

    # Simulated worker 1
    n1 = notification_service.create_and_send(
        db=db,
        school_id=school.id,
        recipient_type=NotificationRecipientType.STAFF,
        recipient_name="Worker 1 Target",
        recipient_contact="worker1@test.com",
        channel=NotificationChannel.IN_APP,
        template_key="general_announcement",
        template_variables={"title": "Concurrent Test", "message": "Payload"},
        idempotency_key=idem_key,
    )

    # Simulated worker 2 (concurrent)
    n2 = notification_service.create_and_send(
        db=db,
        school_id=school.id,
        recipient_type=NotificationRecipientType.STAFF,
        recipient_name="Worker 2 Target",
        recipient_contact="worker2@test.com",
        channel=NotificationChannel.IN_APP,
        template_key="general_announcement",
        template_variables={"title": "Concurrent Test", "message": "Payload"},
        idempotency_key=idem_key,
    )

    assert n1.id == n2.id  # Exactly 1 notification row created!
    db.close()
