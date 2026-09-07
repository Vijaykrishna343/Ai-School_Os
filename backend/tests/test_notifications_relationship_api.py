import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.database.models  # noqa: F401
from app.common.enums import StudentStatus, Gender, AcademicYearStatus
from app.main import app
from app.models.school.school import School
from app.models.academic_year.academic_year import AcademicYear
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.parent.parent import Parent
from app.models.student.student import Student
from app.models.notification import Notification, NotificationChannel, NotificationRecipientType, NotificationStatus
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.permission import IdentityPermission
from app.identity.models.user_role import IdentityUserRole
from app.identity.models.role_permission import IdentityRolePermission
from app.identity.security.password import hash_password
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity


@pytest.fixture
def setup_notif_security_data(db_session: Session):
    seed_identity(db_session)
    s = uuid.uuid4().hex[:6]

    # Schools A and B
    school_a = School(
        name=f"Notif School A {s}", code=f"NSA_{s}",
        address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    school_b = School(
        name=f"Notif School B {s}", code=f"NSB_{s}",
        address_line1="456 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    db_session.add_all([school_a, school_b])
    db_session.commit()

    ay_a = AcademicYear(school_id=school_a.id, name=f"2026-2027_{s}", start_date=date(2026, 6, 1), end_date=date(2027, 4, 30), status=AcademicYearStatus.ACTIVE)
    db_session.add(ay_a)
    db_session.commit()

    class_10a = SchoolClass(school_id=school_a.id, name=f"10_{s}", display_order=1)
    db_session.add(class_10a)
    db_session.commit()

    sec_10a = Section(school_class_id=class_10a.id, name="A")
    db_session.add(sec_10a)
    db_session.commit()

    # Roles
    r_admin = db_session.query(IdentityRole).filter_by(name="School Admin").first()
    r_teacher = db_session.query(IdentityRole).filter_by(name="Teacher").first()
    r_student = db_session.query(IdentityRole).filter_by(name="Student").first()
    r_parent = db_session.query(IdentityRole).filter_by(name="Parent").first()
    r_super = db_session.query(IdentityRole).filter_by(name="Super Admin").first()

    p_school_view = db_session.query(IdentityPermission).filter_by(name="school.view").first()

    pwd = hash_password("Password@123")

    u_admin = IdentityUser(email=f"admin_notif_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Admin", last_name="A")
    u_student1 = IdentityUser(email=f"student1_notif_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Student", last_name="One")
    u_student2 = IdentityUser(email=f"student2_notif_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Student", last_name="Two")
    u_student3 = IdentityUser(username=f"ADM_NS3_{s}", email=f"student3_notif_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Student", last_name="Three")

    u_parent1 = IdentityUser(email=f"parent1_notif_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Parent", last_name="One")
    u_parent2 = IdentityUser(email=f"parent2_notif_{s}@school.com", phone="9876000001", password_hash=pwd, school_id=school_a.id, first_name="Parent", last_name="Two")
    u_parent3 = IdentityUser(email=f"parent3_notif_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Parent", last_name="Three")

    u_super = IdentityUser(email=f"super_notif_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Super", last_name="Admin")
    u_admin_b = IdentityUser(email=f"admin_notif_b_{s}@school.com", password_hash=pwd, school_id=school_b.id, first_name="Admin", last_name="B")

    db_session.add_all([
        u_admin, u_student1, u_student2, u_student3,
        u_parent1, u_parent2, u_parent3, u_super, u_admin_b
    ])
    db_session.commit()

    db_session.add_all([
        IdentityUserRole(user_id=u_admin.id, role_id=r_admin.id),
        IdentityUserRole(user_id=u_student1.id, role_id=r_student.id),
        IdentityUserRole(user_id=u_student2.id, role_id=r_student.id),
        IdentityUserRole(user_id=u_student3.id, role_id=r_student.id),
        IdentityUserRole(user_id=u_parent1.id, role_id=r_parent.id),
        IdentityUserRole(user_id=u_parent2.id, role_id=r_parent.id),
        IdentityUserRole(user_id=u_parent3.id, role_id=r_parent.id),
        IdentityUserRole(user_id=u_super.id, role_id=r_super.id),
        IdentityUserRole(user_id=u_admin_b.id, role_id=r_admin.id),
    ])
    if p_school_view:
        db_session.add_all([
            IdentityRolePermission(role_id=r_parent.id, permission_id=p_school_view.id),
            IdentityRolePermission(role_id=r_student.id, permission_id=p_school_view.id),
        ])
    db_session.commit()

    p_prof1 = Parent(school_id=school_a.id, father_name="Parent One", email=u_parent1.email, primary_phone="9990001111", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001")
    p_prof2 = Parent(school_id=school_a.id, father_name="Parent Two", primary_phone="9876000001", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001")
    p_prof3 = Parent(school_id=school_a.id, father_name="Parent Three", email=u_parent3.email, primary_phone="9990003333", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001")
    db_session.add_all([p_prof1, p_prof2, p_prof3])
    db_session.commit()

    st_prof1 = Student(
        school_id=school_a.id, academic_year_id=ay_a.id, school_class_id=class_10a.id, section_id=sec_10a.id,
        parent_id=p_prof1.id, admission_number=f"ADM_NS1_{s}", roll_number="1", first_name="Student", last_name="One",
        gender=Gender.MALE, date_of_birth=date(2010, 1, 1), admission_date=date(2026, 6, 1),
        email=u_student1.email, status=StudentStatus.ACTIVE, address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    st_prof2 = Student(
        school_id=school_a.id, academic_year_id=ay_a.id, school_class_id=class_10a.id, section_id=sec_10a.id,
        parent_id=p_prof1.id, admission_number=f"ADM_NS2_{s}", roll_number="2", first_name="Student", last_name="Two",
        gender=Gender.FEMALE, date_of_birth=date(2011, 1, 1), admission_date=date(2026, 6, 1),
        email=u_student2.email, status=StudentStatus.ACTIVE, address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    st_prof3 = Student(
        school_id=school_a.id, academic_year_id=ay_a.id, school_class_id=class_10a.id, section_id=sec_10a.id,
        parent_id=p_prof2.id, admission_number=f"ADM_NS3_{s}", roll_number="3", first_name="Student", last_name="Three",
        gender=Gender.MALE, date_of_birth=date(2010, 1, 1), admission_date=date(2026, 6, 1),
        email=u_student3.email, status=StudentStatus.ACTIVE, address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    db_session.add_all([st_prof1, st_prof2, st_prof3])
    db_session.commit()

    # Notifications
    n_st1_absent = Notification(
        school_id=school_a.id, recipient_type=NotificationRecipientType.PARENT, recipient_id=p_prof1.id,
        recipient_name="Parent One", recipient_contact=u_parent1.email, channel=NotificationChannel.SMS,
        template_key="student_absent_alert", title="Absence Alert", body="Dear Parent, your child Student One was marked ABSENT on 2026-08-20.",
        status=NotificationStatus.SENT
    )
    n_st2_fee = Notification(
        school_id=school_a.id, recipient_type=NotificationRecipientType.PARENT, recipient_id=st_prof2.id,
        recipient_name="Parent One", recipient_contact=u_parent1.email, channel=NotificationChannel.SMS,
        template_key="fee_payment_received", title="Fee Payment Confirmed", body="Fee payment of ₹10,000 received for Student Two.",
        status=NotificationStatus.SENT
    )
    n_st3_absent = Notification(
        school_id=school_a.id, recipient_type=NotificationRecipientType.PARENT, recipient_id=p_prof2.id,
        recipient_name="Parent Two", recipient_contact="9876000001", channel=NotificationChannel.SMS,
        template_key="student_absent_alert", title="Absence Alert", body="Dear Parent, your child Student Three was marked ABSENT on 2026-08-20.",
        status=NotificationStatus.FAILED, error_message="Network Timeout"
    )
    n_general = Notification(
        school_id=school_a.id, recipient_type=NotificationRecipientType.STAFF, recipient_id=None,
        recipient_name="All School", recipient_contact="all@school.com", channel=NotificationChannel.IN_APP,
        template_key="general_announcement", title="Annual Sports Day", body="Annual Sports Day will be held on 2026-09-15.",
        status=NotificationStatus.SENT
    )
    db_session.add_all([n_st1_absent, n_st2_fee, n_st3_absent, n_general])
    db_session.commit()

    tok_admin = jwt_manager.create_access_token(user_id=u_admin.id, school_id=school_a.id)
    tok_parent1 = jwt_manager.create_access_token(user_id=u_parent1.id, school_id=school_a.id)
    tok_parent2 = jwt_manager.create_access_token(user_id=u_parent2.id, school_id=school_a.id)
    tok_parent3 = jwt_manager.create_access_token(user_id=u_parent3.id, school_id=school_a.id)
    tok_student1 = jwt_manager.create_access_token(user_id=u_student1.id, school_id=school_a.id)
    tok_student2 = jwt_manager.create_access_token(user_id=u_student2.id, school_id=school_a.id)
    tok_student3 = jwt_manager.create_access_token(user_id=u_student3.id, school_id=school_a.id)
    tok_super = jwt_manager.create_access_token(user_id=u_super.id, school_id=school_a.id)
    tok_admin_b = jwt_manager.create_access_token(user_id=u_admin_b.id, school_id=school_b.id)

    return {
        "school_a": school_a, "school_b": school_b,
        "st_prof1": st_prof1, "st_prof2": st_prof2, "st_prof3": st_prof3,
        "p_prof1": p_prof1, "p_prof2": p_prof2, "p_prof3": p_prof3,
        "n_st1_absent": n_st1_absent, "n_st2_fee": n_st2_fee, "n_st3_absent": n_st3_absent, "n_general": n_general,
        "tok_admin": tok_admin, "tok_parent1": tok_parent1, "tok_parent2": tok_parent2, "tok_parent3": tok_parent3,
        "tok_student1": tok_student1, "tok_student2": tok_student2, "tok_student3": tok_student3,
        "tok_super": tok_super, "tok_admin_b": tok_admin_b,
    }


def test_01_parent_lists_only_own_and_linked_child_notifications(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    titles = {item["title"] for item in items}
    assert "Absence Alert" in titles
    assert "Fee Payment Confirmed" in titles
    assert "Annual Sports Day" in titles


def test_02_parent_cannot_view_unrelated_family_notifications(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    contacts = [item["recipient_contact"] for item in items]
    assert "9876000001" not in contacts


def test_03_student_lists_only_own_notifications(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    for item in items:
        assert item["title"] in ("Annual Sports Day",) or item["recipient_name"] == "Student One"


def test_04_student_cannot_view_peer_notifications(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    bodies = [item["body"] for item in items]
    assert not any("Student Three" in b for b in bodies)


def test_05_zero_child_parent_gets_empty_notification_list(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_parent3']}"})
    assert res.status_code == 200
    assert res.json()["data"]["total"] == 0
    assert res.json()["data"]["items"] == []


def test_06_cross_tenant_notification_isolation(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_admin_b']}"})
    assert res.status_code == 200
    assert res.json()["data"]["total"] == 0


def test_07_parent_cannot_send_announcements(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    payload = {"title": "Test", "message": "Test", "recipient_name": "All", "recipient_contact": "9999999999"}
    res = client.post("/api/v1/notifications/send", json=payload, headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 403


def test_08_student_cannot_send_announcements(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    payload = {"title": "Test", "message": "Test", "recipient_name": "All", "recipient_contact": "9999999999"}
    res = client.post("/api/v1/notifications/send", json=payload, headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 403


def test_09_staff_admin_can_list_school_notifications(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 200
    assert res.json()["data"]["total"] >= 4


def test_10_staff_admin_can_send_announcements(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    payload = {"title": "Exam Schedule", "message": "Exams start next week.", "recipient_name": "All Parents", "recipient_contact": "parents@school.com"}
    res = client.post("/api/v1/notifications/send", json=payload, headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 201
    assert res.json()["data"]["title"] == "Exam Schedule"


def test_11_parent_phone_identity_resolution(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    # Parent 2 (phone match = 9876000001)
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_parent2']}"})
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    contacts = [item["recipient_contact"] for item in items]
    assert "9876000001" in contacts


def test_12_student_admission_number_identity_resolution(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_student3']}"})
    assert res.status_code == 200


def test_13_school_wide_announcement_visibility_for_parent(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    titles = [item["title"] for item in res.json()["data"]["items"]]
    assert "Annual Sports Day" in titles


def test_14_school_wide_announcement_visibility_for_student(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 200
    titles = [item["title"] for item in res.json()["data"]["items"]]
    assert "Annual Sports Day" in titles


def test_15_targeted_parent_notification_isolation(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    bodies = [item["body"] for item in res.json()["data"]["items"]]
    assert not any("Student Three" in b for b in bodies)


def test_16_targeted_student_notification_isolation(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 200
    bodies = [item["body"] for item in res.json()["data"]["items"]]
    assert not any("Student Three" in b for b in bodies)


def test_17_staff_notification_isolation_from_parent(client: TestClient, setup_notif_security_data, db_session: Session):
    d = setup_notif_security_data
    # Add staff-only private notification
    n_staff_private = Notification(
        school_id=d["school_a"].id, recipient_type=NotificationRecipientType.STAFF, recipient_id=uuid.uuid4(),
        recipient_name="Staff Member", recipient_contact="staff@school.com", channel=NotificationChannel.EMAIL,
        template_key="staff_payroll_notice", title="Payroll Processed", body="Your salary has been credited.",
        status=NotificationStatus.SENT
    )
    db_session.add(n_staff_private)
    db_session.commit()

    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    titles = [item["title"] for item in res.json()["data"]["items"]]
    assert "Payroll Processed" not in titles


def test_18_staff_notification_isolation_from_student(client: TestClient, setup_notif_security_data, db_session: Session):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 200
    titles = [item["title"] for item in res.json()["data"]["items"]]
    assert "Payroll Processed" not in titles


def test_19_delivery_status_metadata_privacy_unrelated_parent(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    for item in items:
        assert item["recipient_contact"] != "9876000001"


def test_20_failed_delivery_metadata_privacy_unrelated_parent(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    # n_st3_absent status is FAILED, parent 1 should not see it
    ids = [item["id"] for item in items]
    assert str(d["n_st3_absent"].id) not in ids


def test_21_status_filter_cannot_bypass_relationship_scope(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications?status=FAILED", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    assert res.json()["data"]["total"] == 0


def test_22_channel_filter_cannot_bypass_relationship_scope(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications?channel=SMS", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    for item in items:
        assert item["recipient_contact"] != "9876000001"


def test_23_pagination_respects_relationship_scoped_total(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications?page=1&page_size=10", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    assert res.json()["data"]["total"] == 3


def test_24_multi_child_parent_sees_all_linked_children(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    assert res.json()["data"]["total"] == 3


def test_25_send_announcement_empty_contact_rejected(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    payload = {"title": "Test", "message": "Test", "recipient_name": "All", "recipient_contact": "   "}
    res = client.post("/api/v1/notifications/send", json=payload, headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 400


def test_26_unauthorized_user_permission_rejection(client: TestClient, setup_notif_security_data, db_session: Session):
    d = setup_notif_security_data
    u_no_perm = IdentityUser(email=f"noperm_{uuid.uuid4().hex[:6]}@school.com", password_hash=hash_password("Pass123!"), school_id=d["school_a"].id, first_name="No", last_name="Perm")
    db_session.add(u_no_perm)
    db_session.commit()
    tok = jwt_manager.create_access_token(user_id=u_no_perm.id, school_id=d["school_a"].id)

    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {tok}"})
    assert res.status_code == 403


def test_27_unauthenticated_request_rejected(client: TestClient):
    res = client.get("/api/v1/notifications")
    assert res.status_code == 401


def test_28_super_admin_bypass_allows_all_notifications(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_super']}"})
    assert res.status_code == 200
    assert res.json()["data"]["total"] >= 4


def test_29_deleted_notifications_excluded(client: TestClient, setup_notif_security_data, db_session: Session):
    d = setup_notif_security_data
    n_del = Notification(
        school_id=d["school_a"].id, recipient_type=NotificationRecipientType.STAFF, recipient_id=None,
        recipient_name="Deleted", recipient_contact="del@school.com", channel=NotificationChannel.IN_APP,
        template_key="general_announcement", title="Deleted Notice", body="Deleted body.",
        status=NotificationStatus.SENT
    )
    n_del.is_deleted = True
    db_session.add(n_del)
    db_session.commit()

    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 200
    titles = [item["title"] for item in res.json()["data"]["items"]]
    assert "Deleted Notice" not in titles


def test_30_notification_templates_endpoint_accessible(client: TestClient, setup_notif_security_data):
    d = setup_notif_security_data
    res = client.get("/api/v1/notifications/templates", headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 200
    template_keys = [t["template_key"] for t in res.json()["data"]]
    assert "student_absent_alert" in template_keys
