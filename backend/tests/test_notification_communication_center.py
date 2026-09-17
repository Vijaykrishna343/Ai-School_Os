"""
Phase 27.5 Communication Center & Notification Analytics Test Suite
Tests history listing, multi-parameter filters, detail inspection, DB-side analytics aggregation,
retry lifecycle constraints, RBAC, PII minimization, and strict multi-tenant isolation.
"""
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import SessionLocal
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.permission import IdentityPermission
from app.identity.security.current_user import get_current_user
from app.models.school import School
from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationRecipientType,
    NotificationStatus,
)
from app.services.notification_service import notification_service

client = TestClient(app)


@pytest.fixture
def comm_center_setup():
    db = SessionLocal()

    # School A
    school_a = School(
        name=f"Comm Center School A {uuid4().hex[:6]}",
        code=f"CCA-{uuid4().hex[:4]}",
        address_line1="123 Alpha St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db.add(school_a)

    # School B
    school_b = School(
        name=f"Comm Center School B {uuid4().hex[:6]}",
        code=f"CCB-{uuid4().hex[:4]}",
        address_line1="456 Beta Ave",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500002",
    )
    db.add(school_b)
    db.flush()

    # Admin Role with all notification permissions
    admin_role = db.query(IdentityRole).filter_by(name="Super Admin").first()
    if not admin_role:
        admin_role = IdentityRole(name="Super Admin", description="Super Admin", is_system=True)
        db.add(admin_role)
        db.flush()

    # Viewer Role with notification.view only
    viewer_role = db.query(IdentityRole).filter_by(name="Notification Viewer Role").first()
    if not viewer_role:
        viewer_role = IdentityRole(name="Notification Viewer Role", description="View Only", is_system=False)
        db.add(viewer_role)
        db.flush()
        # Attach permission
        perm_view = db.query(IdentityPermission).filter_by(name="notification.view").first()
        if perm_view:
            viewer_role.permissions.append(perm_view)

    # User A (Admin in School A)
    user_a = IdentityUser(
        email=f"admin.a.{uuid4().hex[:6]}@schoola.com",
        username=f"admin_a_{uuid4().hex[:6]}",
        password_hash="testpass",
        first_name="Admin",
        last_name="A",
        school_id=school_a.id,
        is_active=True,
    )
    user_a.roles = [admin_role]
    db.add(user_a)

    # User B (Admin in School B)
    user_b = IdentityUser(
        email=f"admin.b.{uuid4().hex[:6]}@schoolb.com",
        username=f"admin_b_{uuid4().hex[:6]}",
        password_hash="testpass",
        first_name="Admin",
        last_name="B",
        school_id=school_b.id,
        is_active=True,
    )
    user_b.roles = [admin_role]
    db.add(user_b)
    db.flush()

    # Populate seeded notifications for School A
    now = datetime.now(timezone.utc)

    n1 = Notification(
        school_id=school_a.id,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_name="Rahul Sharma",
        recipient_contact="+919876543210",
        channel=NotificationChannel.SMS,
        template_key="student_absence",
        title="Student Absence: Aarav Sharma",
        body="Aarav Sharma was marked absent on 2026-09-09.",
        status=NotificationStatus.SENT,
        created_at=now - timedelta(days=2),
        sent_at=now - timedelta(days=2),
    )
    n2 = Notification(
        school_id=school_a.id,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_name="Priya Patel",
        recipient_contact="+919876543211",
        channel=NotificationChannel.WHATSAPP,
        template_key="fee_payment_received",
        title="Fee Payment Receipt: Ananya Patel",
        body="Payment of INR 15,000 received.",
        status=NotificationStatus.SENT,
        created_at=now - timedelta(days=1),
        sent_at=now - timedelta(days=1),
    )
    n3 = Notification(
        school_id=school_a.id,
        recipient_type=NotificationRecipientType.STAFF,
        recipient_name="Teacher Vikram",
        recipient_contact="vikram@schoola.com",
        channel=NotificationChannel.EMAIL,
        template_key="visitor_checkin",
        title="Visitor Arrival: Rajesh Verma",
        body="Visitor Rajesh Verma checked in to meet you.",
        status=NotificationStatus.FAILED,
        error_message="SMTP connection timeout",
        retry_count=1,
        max_retries=3,
        created_at=now - timedelta(hours=6),
    )
    n4 = Notification(
        school_id=school_a.id,
        recipient_type=NotificationRecipientType.STUDENT,
        recipient_name="Kavita Reddy",
        recipient_contact="kavita@schoola.com",
        channel=NotificationChannel.IN_APP,
        template_key="homework_published",
        title="New Homework Assigned: Mathematics",
        body="Chapter 5 Exercises due Monday.",
        status=NotificationStatus.PENDING,
        created_at=now - timedelta(hours=1),
    )
    n5 = Notification(
        school_id=school_a.id,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_name="Suresh Kumar",
        recipient_contact="+919876543219",
        channel=NotificationChannel.SMS,
        template_key="visitor_checkout",
        title="Visitor Departure: Suresh Kumar",
        body="Visitor checkout complete.",
        status=NotificationStatus.SENT,
        created_at=now,
        sent_at=now,
    )

    # Seed Notification for School B (Tenant Isolation Target)
    n_b = Notification(
        school_id=school_b.id,
        recipient_type=NotificationRecipientType.STAFF,
        recipient_name="School B Staff",
        recipient_contact="staff@schoolb.com",
        channel=NotificationChannel.IN_APP,
        template_key="general_announcement",
        title="School B Private Notice",
        body="Confidential School B Payload",
        status=NotificationStatus.SENT,
        created_at=now,
        sent_at=now,
    )

    db.add_all([n1, n2, n3, n4, n5, n_b])
    db.commit()

    yield {
        "school_a": school_a,
        "school_b": school_b,
        "user_a": user_a,
        "user_b": user_b,
        "notifications_a": [n1, n2, n3, n4, n5],
        "notification_b": n_b,
    }

    db.close()


def test_notification_history_listing_and_filters(comm_center_setup):
    """Verify notification listing endpoint with status, channel, event_type, date, and search filters."""
    user_a = comm_center_setup["user_a"]
    school_a = comm_center_setup["school_a"]
    app.dependency_overrides[get_current_user] = lambda: user_a

    # 1. Default listing returns all School A items
    res = client.get("/api/v1/notifications", headers={"X-School-Id": str(school_a.id)})
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["total"] == 5
    assert len(data["items"]) == 5

    # 2. Filter by status = FAILED
    res_failed = client.get("/api/v1/notifications?status=FAILED", headers={"X-School-Id": str(school_a.id)})
    assert res_failed.status_code == 200
    failed_items = res_failed.json()["data"]["items"]
    assert len(failed_items) == 1
    assert failed_items[0]["status"] == "FAILED"
    assert failed_items[0]["template_key"] == "visitor_checkin"

    # 3. Filter by channel = WHATSAPP
    res_wa = client.get("/api/v1/notifications?channel=WHATSAPP", headers={"X-School-Id": str(school_a.id)})
    assert res_wa.status_code == 200
    wa_items = res_wa.json()["data"]["items"]
    assert len(wa_items) == 1
    assert wa_items[0]["channel"] == "WHATSAPP"
    assert wa_items[0]["recipient_name"] == "Priya Patel"

    # 4. Filter by event_type = student_absence
    res_evt = client.get("/api/v1/notifications?event_type=student_absence", headers={"X-School-Id": str(school_a.id)})
    assert res_evt.status_code == 200
    evt_items = res_evt.json()["data"]["items"]
    assert len(evt_items) == 1
    assert evt_items[0]["template_key"] == "student_absence"
    assert "Aarav Sharma" in evt_items[0]["title"]

    # 5. Search keyword filter
    res_search = client.get("/api/v1/notifications?search=Kavita", headers={"X-School-Id": str(school_a.id)})
    assert res_search.status_code == 200
    search_items = res_search.json()["data"]["items"]
    assert len(search_items) == 1
    assert search_items[0]["recipient_name"] == "Kavita Reddy"

    # 6. Pagination check
    res_page = client.get("/api/v1/notifications?page=1&page_size=2", headers={"X-School-Id": str(school_a.id)})
    assert res_page.status_code == 200
    pdata = res_page.json()["data"]
    assert len(pdata["items"]) == 2
    assert pdata["total"] == 5
    assert pdata["page"] == 1
    assert pdata["page_size"] == 2

    app.dependency_overrides.clear()


def test_notification_detail_endpoint_and_pii_safety(comm_center_setup):
    """Verify single notification detail retrieval and ensure no credential/auth secrets leak."""
    user_a = comm_center_setup["user_a"]
    school_a = comm_center_setup["school_a"]
    target_notif = comm_center_setup["notifications_a"][2]  # Failed notification n3
    app.dependency_overrides[get_current_user] = lambda: user_a

    res = client.get(f"/api/v1/notifications/{target_notif.id}", headers={"X-School-Id": str(school_a.id)})
    assert res.status_code == 200, res.text
    detail = res.json()["data"]

    assert detail["id"] == str(target_notif.id)
    assert detail["school_id"] == str(school_a.id)
    assert detail["recipient_name"] == "Teacher Vikram"
    assert detail["recipient_contact"] == "vikram@schoola.com"
    assert detail["channel"] == "EMAIL"
    assert detail["template_key"] == "visitor_checkin"
    assert detail["status"] == "FAILED"
    assert detail["error_message"] == "SMTP connection timeout"
    assert detail["retry_count"] == 1
    assert detail["max_retries"] == 3

    # Ensure no secrets in output
    detail_str = str(detail).lower()
    assert "password" not in detail_str
    assert "secret" not in detail_str
    assert "token" not in detail_str
    assert "api_key" not in detail_str

    app.dependency_overrides.clear()


def test_cross_tenant_detail_isolation_fail_closed(comm_center_setup):
    """Verify School A user cannot view School B notification (fail closed 404)."""
    user_a = comm_center_setup["user_a"]
    school_a = comm_center_setup["school_a"]
    notif_b = comm_center_setup["notification_b"]
    app.dependency_overrides[get_current_user] = lambda: user_a

    res = client.get(f"/api/v1/notifications/{notif_b.id}", headers={"X-School-Id": str(school_a.id)})
    assert res.status_code == 404

    app.dependency_overrides.clear()


def test_notification_analytics_aggregation_and_tenant_isolation(comm_center_setup):
    """Verify database-side aggregated analytics calculation and multi-tenant isolation."""
    user_a = comm_center_setup["user_a"]
    school_a = comm_center_setup["school_a"]
    app.dependency_overrides[get_current_user] = lambda: user_a

    res = client.get("/api/v1/notifications/analytics", headers={"X-School-Id": str(school_a.id)})
    assert res.status_code == 200, res.text
    analytics = res.json()["data"]

    # In School A: 5 notifications total (3 SENT, 1 FAILED, 1 PENDING)
    assert analytics["total_notifications"] == 5
    assert analytics["sent_count"] == 3
    assert analytics["failed_count"] == 1
    assert analytics["pending_count"] == 1
    assert analytics["cancelled_count"] == 0

    # Rates: (3 / 5) * 100 = 60.0% success, (1 / 5) * 100 = 20.0% failure
    assert analytics["success_rate_percent"] == 60.0
    assert analytics["failure_rate_percent"] == 20.0
    assert analytics["pending_rate_percent"] == 20.0

    # Channel counts
    by_channel = analytics["by_channel"]
    assert by_channel["SMS"] == 2
    assert by_channel["WHATSAPP"] == 1
    assert by_channel["EMAIL"] == 1
    assert by_channel["IN_APP"] == 1

    # Event counts
    by_event = analytics["by_event"]
    assert by_event["student_absence"] == 1
    assert by_event["fee_payment_received"] == 1
    assert by_event["visitor_checkin"] == 1
    assert by_event["visitor_checkout"] == 1
    assert by_event["homework_published"] == 1

    # Daily volume timeline
    assert len(analytics["daily_volume"]) >= 1

    # Verify School B is completely isolated
    user_b = comm_center_setup["user_b"]
    school_b = comm_center_setup["school_b"]
    app.dependency_overrides[get_current_user] = lambda: user_b

    res_b = client.get("/api/v1/notifications/analytics", headers={"X-School-Id": str(school_b.id)})
    assert res_b.status_code == 200
    analytics_b = res_b.json()["data"]
    assert analytics_b["total_notifications"] == 1
    assert analytics_b["sent_count"] == 1
    assert analytics_b["failed_count"] == 0

    app.dependency_overrides.clear()


def test_notification_retry_mutation_lifecycle_and_constraints(comm_center_setup):
    """Verify manual retry works on FAILED notifications and rejects invalid states/limits/cross-tenant."""
    user_a = comm_center_setup["user_a"]
    school_a = comm_center_setup["school_a"]
    failed_notif = comm_center_setup["notifications_a"][2]  # n3 (FAILED)
    sent_notif = comm_center_setup["notifications_a"][0]    # n1 (SENT)
    notif_b = comm_center_setup["notification_b"]           # School B
    app.dependency_overrides[get_current_user] = lambda: user_a

    # 1. Retry FAILED notification succeeds
    res_retry = client.post(f"/api/v1/notifications/{failed_notif.id}/retry", headers={"X-School-Id": str(school_a.id)})
    assert res_retry.status_code == 200, res_retry.text
    retry_data = res_retry.json()["data"]
    assert retry_data["id"] == str(failed_notif.id)
    assert retry_data["retry_count"] == 2  # Incremented from 1 to 2

    # 2. Retry already SENT notification is rejected (Validation error 422)
    res_sent_retry = client.post(f"/api/v1/notifications/{sent_notif.id}/retry", headers={"X-School-Id": str(school_a.id)})
    assert res_sent_retry.status_code == 422
    assert "Only FAILED or PENDING notifications can be retried" in res_sent_retry.text

    # 3. Exceeded max retries is rejected
    db = SessionLocal()
    notif_db = db.query(Notification).filter_by(id=failed_notif.id).first()
    notif_db.status = NotificationStatus.FAILED
    notif_db.retry_count = 3
    notif_db.max_retries = 3
    db.commit()
    db.close()

    res_max_retry = client.post(f"/api/v1/notifications/{failed_notif.id}/retry", headers={"X-School-Id": str(school_a.id)})
    assert res_max_retry.status_code == 422
    assert "Maximum retries" in res_max_retry.text

    # 4. Cross-tenant retry rejected (404)
    res_cross = client.post(f"/api/v1/notifications/{notif_b.id}/retry", headers={"X-School-Id": str(school_a.id)})
    assert res_cross.status_code == 404

    app.dependency_overrides.clear()


def test_notification_rbac_unauthorized_denial():
    """Verify users without appropriate permissions are rejected with 403 Forbidden."""
    db = SessionLocal()
    school = School(
        name=f"RBAC School {uuid4().hex[:6]}",
        code=f"RBC-{uuid4().hex[:4]}",
        address_line1="123 Test St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db.add(school)
    db.flush()

    # Unprivileged User (No notification permissions)
    unprivileged_role = IdentityRole(name="Unprivileged Role", description="No Perms", is_system=False)
    db.add(unprivileged_role)
    db.flush()

    unprivileged_user = IdentityUser(
        email=f"noperms.{uuid4().hex[:6]}@school.com",
        username=f"noperms_{uuid4().hex[:6]}",
        password_hash="testpass",
        first_name="No",
        last_name="Perms",
        school_id=school.id,
        is_active=True,
    )
    unprivileged_user.roles = [unprivileged_role]
    db.add(unprivileged_user)
    db.commit()

    app.dependency_overrides[get_current_user] = lambda: unprivileged_user

    # 1. Listing rejected
    res_list = client.get("/api/v1/notifications", headers={"X-School-Id": str(school.id)})
    assert res_list.status_code == 403

    # 2. Analytics rejected
    res_analytics = client.get("/api/v1/notifications/analytics", headers={"X-School-Id": str(school.id)})
    assert res_analytics.status_code == 403

    # 3. Detail rejected
    fake_id = uuid4()
    res_detail = client.get(f"/api/v1/notifications/{fake_id}", headers={"X-School-Id": str(school.id)})
    assert res_detail.status_code == 403

    # 4. Retry rejected
    res_retry = client.post(f"/api/v1/notifications/{fake_id}/retry", headers={"X-School-Id": str(school.id)})
    assert res_retry.status_code == 403

    app.dependency_overrides.clear()
    db.close()
