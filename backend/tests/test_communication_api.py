"""
Phase 8 Communication & Notification API Tests
Tests Inbox, Unread Count, Preferences GET/PUT, Delivery Metrics, Templates, Provider Statuses.
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.security.current_user import get_current_user
from app.models.school import School
from app.models.notification import Notification, NotificationChannel, NotificationRecipientType, NotificationStatus

client = TestClient(app)


@pytest.fixture
def comm_db_setup():
    db = SessionLocal()

    school = School(
        name=f"Comm Test School {uuid4().hex[:6]}",
        code=f"CTS-{uuid4().hex[:4]}",
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
        super_admin_role = IdentityRole(
            name="Super Admin",
            description="Super Admin Role",
            is_system=True,
        )
        db.add(super_admin_role)
        db.flush()

    user = IdentityUser(
        email=f"comm.admin.{uuid4().hex[:6]}@test.com",
        username=f"commadmin_{uuid4().hex[:6]}",
        password_hash="hashed_test_password",
        first_name="Comm",
        last_name="Admin",
        school_id=school.id,
        is_active=True,
    )
    user.roles = [super_admin_role]
    db.add(user)
    db.flush()

    # Pre-populate a notification
    notif = Notification(
        school_id=school.id,
        recipient_type=NotificationRecipientType.STAFF,
        recipient_id=user.id,
        recipient_name="Comm Admin",
        recipient_contact=user.email,
        channel=NotificationChannel.IN_APP,
        template_key="general_announcement",
        title="Test Inbox Notification",
        body="Body of test inbox notification",
        status=NotificationStatus.SENT,
    )
    db.add(notif)
    db.commit()

    yield {
        "school": school,
        "user": user,
        "notification": notif,
    }

    db.close()


def test_communication_inbox_and_unread_count(comm_db_setup):
    user = comm_db_setup["user"]
    app.dependency_overrides[get_current_user] = lambda: user

    # 1. Get Inbox
    response = client.get(
        "/api/v1/notifications/inbox",
        headers={"X-School-Id": str(user.school_id)},
    )
    assert response.status_code == 200, response.text
    res_data = response.json()["data"]
    assert res_data["total"] >= 1
    assert res_data["unread_count"] >= 1

    # 2. Get Unread Count
    count_res = client.get(
        "/api/v1/notifications/unread-count",
        headers={"X-School-Id": str(user.school_id)},
    )
    assert count_res.status_code == 200
    assert count_res.json()["data"]["unread_count"] >= 1

    # 3. Mark Read
    notif_id = comm_db_setup["notification"].id
    read_res = client.post(
        f"/api/v1/notifications/inbox/{notif_id}/read",
        headers={"X-School-Id": str(user.school_id)},
    )
    assert read_res.status_code == 200

    app.dependency_overrides.clear()


def test_user_communication_preferences_api(comm_db_setup):
    user = comm_db_setup["user"]
    app.dependency_overrides[get_current_user] = lambda: user

    # 1. Get Preferences
    get_res = client.get(
        "/api/v1/notifications/preferences",
        headers={"X-School-Id": str(user.school_id)},
    )
    assert get_res.status_code == 200
    pref_data = get_res.json()["data"]
    assert pref_data["enable_in_app"] is True
    assert pref_data["enable_emergency"] is True

    # 2. Update Preferences
    update_res = client.put(
        "/api/v1/notifications/preferences",
        json={"enable_sms": False, "enable_fees": False},
        headers={"X-School-Id": str(user.school_id)},
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()["data"]
    assert updated_data["enable_sms"] is False
    assert updated_data["enable_fees"] is False
    assert updated_data["enable_emergency"] is True  # Mandatory safety invariant holds

    app.dependency_overrides.clear()


def test_provider_status_and_template_apis(comm_db_setup):
    user = comm_db_setup["user"]
    app.dependency_overrides[get_current_user] = lambda: user

    # 1. Provider Statuses
    prov_res = client.get(
        "/api/v1/notifications/providers/status",
        headers={"X-School-Id": str(user.school_id)},
    )
    assert prov_res.status_code == 200
    providers = prov_res.json()["data"]
    assert len(providers) >= 4

    # 2. Templates List
    tpl_res = client.get(
        "/api/v1/notifications/templates",
        headers={"X-School-Id": str(user.school_id)},
    )
    assert tpl_res.status_code == 200
    templates = tpl_res.json()["data"]
    assert len(templates) >= 5

    # 3. Create Custom Template
    create_tpl_res = client.post(
        "/api/v1/notifications/templates",
        json={
            "template_key": "custom_exam_alert_v1",
            "name": "Custom Exam Alert",
            "category": "EXAMS",
            "title_template": "Exam Alert for {student_name}",
            "body_template": "Exam starts on {date}.",
        },
        headers={"X-School-Id": str(user.school_id)},
    )
    assert create_tpl_res.status_code == 201
    assert create_tpl_res.json()["data"]["is_custom"] is True

    app.dependency_overrides.clear()
