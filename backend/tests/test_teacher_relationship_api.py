import uuid
from decimal import Decimal
from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.database.models  # noqa: F401
from app.common.enums import TeacherStatus, Gender
from app.main import app
from app.models.school.school import School
from app.models.teacher.teacher import Teacher
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.permission import IdentityPermission
from app.identity.models.user_role import IdentityUserRole
from app.identity.models.role_permission import IdentityRolePermission
from app.identity.security.password import hash_password
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity


@pytest.fixture
def setup_teacher_security_data(db_session: Session):
    seed_identity(db_session)
    s = uuid.uuid4().hex[:6]

    # Schools A & B
    school_a = School(
        name=f"Teacher School A {s}", code=f"TSA_{s}",
        address_line1="123 Main St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    school_b = School(
        name=f"Teacher School B {s}", code=f"TSB_{s}",
        address_line1="456 Other St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    db_session.add_all([school_a, school_b])
    db_session.commit()

    # Teacher Entities in School A
    t1 = Teacher(
        school_id=school_a.id, employee_id=f"EMP_T1_{s}", first_name="T1_FirstName", last_name="T1_LastName",
        gender=Gender.FEMALE, phone=f"9000{s[:6]}", email=f"teacher1_{s}@school.com",
        date_of_birth=date(1985, 5, 15), joining_date=date(2015, 6, 1), qualification="M.Sc Physics",
        address_line1="123 Teacher St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001",
        salary=Decimal("75000.00"), remarks="Senior Physics Faculty", status=TeacherStatus.ACTIVE
    )
    t2 = Teacher(
        school_id=school_a.id, employee_id=f"EMP_T2_{s}", first_name="T2_FirstName", last_name="T2_LastName",
        gender=Gender.MALE, phone=f"9001{s[:6]}", email=f"teacher2_{s}@school.com",
        date_of_birth=date(1990, 8, 20), joining_date=date(2018, 6, 1), qualification="M.Sc Chemistry",
        address_line1="456 Teacher St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001",
        salary=Decimal("65000.00"), remarks="Chemistry Faculty", status=TeacherStatus.ACTIVE
    )
    t_b = Teacher(
        school_id=school_b.id, employee_id=f"EMP_TB_{s}", first_name="TB_FirstName", last_name="TB_LastName",
        gender=Gender.MALE, phone=f"9002{s[:6]}", email=f"teacher_b_{s}@school.com",
        date_of_birth=date(1988, 3, 10), joining_date=date(2016, 6, 1), qualification="M.A English",
        address_line1="789 School B St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001",
        salary=Decimal("70000.00"), status=TeacherStatus.ACTIVE
    )
    db_session.add_all([t1, t2, t_b])
    db_session.commit()

    # Roles
    r_admin = db_session.query(IdentityRole).filter_by(name="School Admin").first()
    r_principal = db_session.query(IdentityRole).filter_by(name="Principal").first()
    r_vp = db_session.query(IdentityRole).filter_by(name="Vice Principal").first()
    r_teacher = db_session.query(IdentityRole).filter_by(name="Teacher").first()
    r_parent = db_session.query(IdentityRole).filter_by(name="Parent").first()
    r_student = db_session.query(IdentityRole).filter_by(name="Student").first()
    r_super = db_session.query(IdentityRole).filter_by(name="Super Admin").first()

    p_teacher_view = db_session.query(IdentityPermission).filter_by(name="teacher.view").first()

    pwd = hash_password("Password@123")

    u_admin = IdentityUser(email=f"admin_ts_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Admin", last_name="A")
    u_principal = IdentityUser(email=f"principal_ts_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Principal", last_name="P")
    u_vp = IdentityUser(email=f"vp_ts_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Vice", last_name="Principal")
    u_teacher1 = IdentityUser(email=t1.email, password_hash=pwd, school_id=school_a.id, first_name="T1", last_name="User")
    u_teacher2 = IdentityUser(email=t2.email, password_hash=pwd, school_id=school_a.id, first_name="T2", last_name="User")
    u_parent = IdentityUser(email=f"parent_ts_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Parent", last_name="User")
    u_student = IdentityUser(email=f"student_ts_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Student", last_name="User")
    u_super = IdentityUser(email=f"super_ts_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Super", last_name="Admin")
    u_admin_b = IdentityUser(email=f"admin_b_ts_{s}@school.com", password_hash=pwd, school_id=school_b.id, first_name="Admin", last_name="B")

    db_session.add_all([u_admin, u_principal, u_vp, u_teacher1, u_teacher2, u_parent, u_student, u_super, u_admin_b])
    db_session.commit()

    db_session.add_all([
        IdentityUserRole(user_id=u_admin.id, role_id=r_admin.id),
        IdentityUserRole(user_id=u_principal.id, role_id=r_principal.id),
        IdentityUserRole(user_id=u_vp.id, role_id=r_vp.id),
        IdentityUserRole(user_id=u_teacher1.id, role_id=r_teacher.id),
        IdentityUserRole(user_id=u_teacher2.id, role_id=r_teacher.id),
        IdentityUserRole(user_id=u_parent.id, role_id=r_parent.id),
        IdentityUserRole(user_id=u_student.id, role_id=r_student.id),
        IdentityUserRole(user_id=u_super.id, role_id=r_super.id),
        IdentityUserRole(user_id=u_admin_b.id, role_id=r_admin.id),
    ])
    # Grant teacher.view to teacher role for testing peer viewing
    if p_teacher_view:
        db_session.add(IdentityRolePermission(role_id=r_teacher.id, permission_id=p_teacher_view.id))
    db_session.commit()

    tok_admin = jwt_manager.create_access_token(user_id=u_admin.id, school_id=school_a.id)
    tok_principal = jwt_manager.create_access_token(user_id=u_principal.id, school_id=school_a.id)
    tok_vp = jwt_manager.create_access_token(user_id=u_vp.id, school_id=school_a.id)
    tok_teacher1 = jwt_manager.create_access_token(user_id=u_teacher1.id, school_id=school_a.id)
    tok_teacher2 = jwt_manager.create_access_token(user_id=u_teacher2.id, school_id=school_a.id)
    tok_parent = jwt_manager.create_access_token(user_id=u_parent.id, school_id=school_a.id)
    tok_student = jwt_manager.create_access_token(user_id=u_student.id, school_id=school_a.id)
    tok_super = jwt_manager.create_access_token(user_id=u_super.id, school_id=school_a.id)
    tok_admin_b = jwt_manager.create_access_token(user_id=u_admin_b.id, school_id=school_b.id)

    return {
        "school_a": school_a, "school_b": school_b,
        "t1": t1, "t2": t2, "t_b": t_b,
        "tok_admin": tok_admin, "tok_principal": tok_principal, "tok_vp": tok_vp,
        "tok_teacher1": tok_teacher1, "tok_teacher2": tok_teacher2,
        "tok_parent": tok_parent, "tok_student": tok_student,
        "tok_super": tok_super, "tok_admin_b": tok_admin_b,
    }


def test_01_admin_views_full_teacher_profile_with_salary(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get(f"/api/v1/teachers/{d['t1'].id}", headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert float(data["salary"]) == 75000.0
    assert data["address_line1"] == "123 Teacher St"


def test_02_principal_views_full_teacher_profile_with_salary(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get(f"/api/v1/teachers/{d['t1'].id}", headers={"Authorization": f"Bearer {d['tok_principal']}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert float(data["salary"]) == 75000.0


def test_03_vice_principal_views_full_teacher_profile_with_salary(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get(f"/api/v1/teachers/{d['t1'].id}", headers={"Authorization": f"Bearer {d['tok_vp']}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert float(data["salary"]) == 75000.0


def test_04_teacher_views_own_profile_with_salary_via_id(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get(f"/api/v1/teachers/{d['t1'].id}", headers={"Authorization": f"Bearer {d['tok_teacher1']}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert float(data["salary"]) == 75000.0


def test_05_teacher_views_own_profile_via_me(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get("/api/v1/teachers/me", headers={"Authorization": f"Bearer {d['tok_teacher1']}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert float(data["salary"]) == 75000.0
    assert data["email"] == d["t1"].email


def test_06_peer_teacher_viewing_teacher_profile_has_salary_redacted(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get(f"/api/v1/teachers/{d['t2'].id}", headers={"Authorization": f"Bearer {d['tok_teacher1']}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["salary"] is None


def test_07_peer_teacher_viewing_teacher_profile_has_phone_masked(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get(f"/api/v1/teachers/{d['t2'].id}", headers={"Authorization": f"Bearer {d['tok_teacher1']}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["emergency_contact"] is None
    assert data["address_line1"] is None
    assert data["phone"].startswith("XXXXX")


def test_08_peer_teacher_viewing_teacher_list_has_salary_redacted(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get("/api/v1/teachers", headers={"Authorization": f"Bearer {d['tok_teacher1']}"})
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    for item in items:
        if item["email"] != d["t1"].email:
            assert item["salary"] is None


def test_09_parent_cannot_view_teacher_profiles_denied(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get("/api/v1/teachers", headers={"Authorization": f"Bearer {d['tok_parent']}"})
    assert res.status_code == 403


def test_10_student_cannot_view_teacher_profiles_denied(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get("/api/v1/teachers", headers={"Authorization": f"Bearer {d['tok_student']}"})
    assert res.status_code == 403


def test_11_cross_tenant_teacher_lookup_returns_404(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get(f"/api/v1/teachers/{d['t1'].id}", headers={"Authorization": f"Bearer {d['tok_admin_b']}"})
    assert res.status_code == 404


def test_12_teacher_self_checkin_checkout(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res_in = client.post("/api/v1/teachers/attendance/check-in", headers={"Authorization": f"Bearer {d['tok_teacher1']}"})
    assert res_in.status_code == 200
    assert res_in.json()["data"]["status"] == "PRESENT"

    res_out = client.post("/api/v1/teachers/attendance/check-out", headers={"Authorization": f"Bearer {d['tok_teacher1']}"})
    assert res_out.status_code == 200


def test_13_parent_cannot_access_teacher_attendance_denied(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get("/api/v1/teachers/attendance", headers={"Authorization": f"Bearer {d['tok_parent']}"})
    assert res.status_code == 403


def test_14_student_cannot_access_teacher_attendance_denied(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get("/api/v1/teachers/attendance", headers={"Authorization": f"Bearer {d['tok_student']}"})
    assert res.status_code == 403


def test_15_teacher_export_requires_export_permission(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get("/api/v1/export/teachers", headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")


def test_16_non_admin_teacher_cannot_export_teachers(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get("/api/v1/export/teachers", headers={"Authorization": f"Bearer {d['tok_teacher1']}"})
    assert res.status_code == 403


def test_17_admin_can_update_teacher_profile(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    payload = {"qualification": "Ph.D Physics"}
    res = client.put(f"/api/v1/teachers/{d['t1'].id}", json=payload, headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 200
    assert res.json()["data"]["qualification"] == "Ph.D Physics"


def test_18_non_admin_teacher_cannot_update_peer_profile(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    payload = {"qualification": "Hacked"}
    res = client.put(f"/api/v1/teachers/{d['t2'].id}", json=payload, headers={"Authorization": f"Bearer {d['tok_teacher1']}"})
    assert res.status_code == 403


def test_19_non_admin_teacher_cannot_delete_peer_profile(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.delete(f"/api/v1/teachers/{d['t2'].id}", headers={"Authorization": f"Bearer {d['tok_teacher1']}"})
    assert res.status_code == 403


def test_20_direct_id_salary_leak_attempt_redacted(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get(f"/api/v1/teachers/{d['t2'].id}", headers={"Authorization": f"Bearer {d['tok_teacher1']}"})
    assert res.status_code == 200
    assert res.json()["data"]["salary"] is None


def test_21_status_query_param_cannot_bypass_salary_redaction(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get("/api/v1/teachers?status=ACTIVE", headers={"Authorization": f"Bearer {d['tok_teacher1']}"})
    assert res.status_code == 200
    for item in res.json()["data"]["items"]:
        if item["email"] != d["t1"].email:
            assert item["salary"] is None


def test_22_gender_query_param_cannot_bypass_salary_redaction(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get("/api/v1/teachers?gender=MALE", headers={"Authorization": f"Bearer {d['tok_teacher1']}"})
    assert res.status_code == 200
    for item in res.json()["data"]["items"]:
        if item["email"] != d["t1"].email:
            assert item["salary"] is None


def test_23_page_size_query_param_cannot_bypass_salary_redaction(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get("/api/v1/teachers?page_size=50", headers={"Authorization": f"Bearer {d['tok_teacher1']}"})
    assert res.status_code == 200
    for item in res.json()["data"]["items"]:
        if item["email"] != d["t1"].email:
            assert item["salary"] is None


def test_24_unlinked_user_calling_me_returns_404(client: TestClient, setup_teacher_security_data, db_session: Session):
    d = setup_teacher_security_data
    u_unlinked = IdentityUser(email=f"unlinked_{uuid.uuid4().hex[:6]}@school.com", password_hash=hash_password("Pass123!"), school_id=d["school_a"].id, first_name="Unlinked", last_name="User")
    db_session.add(u_unlinked)
    db_session.commit()
    tok = jwt_manager.create_access_token(user_id=u_unlinked.id, school_id=d["school_a"].id)

    res = client.get("/api/v1/teachers/me", headers={"Authorization": f"Bearer {tok}"})
    assert res.status_code == 404


def test_25_unauthenticated_me_returns_401(client: TestClient):
    res = client.get("/api/v1/teachers/me")
    assert res.status_code == 401


def test_26_unauthenticated_teachers_list_returns_401(client: TestClient):
    res = client.get("/api/v1/teachers")
    assert res.status_code == 401


def test_27_super_admin_bypass_allows_full_teacher_profile(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get(f"/api/v1/teachers/{d['t1'].id}", headers={"Authorization": f"Bearer {d['tok_super']}"})
    assert res.status_code == 200
    assert float(res.json()["data"]["salary"]) == 75000.0


def test_28_deleted_teacher_profile_excluded_from_me(client: TestClient, setup_teacher_security_data, db_session: Session):
    d = setup_teacher_security_data
    d["t1"].is_deleted = True
    db_session.commit()

    res = client.get("/api/v1/teachers/me", headers={"Authorization": f"Bearer {d['tok_teacher1']}"})
    assert res.status_code == 404


def test_29_vice_principal_can_manage_teacher_substitutions(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    res = client.get("/api/v1/teacher-substitutions", headers={"Authorization": f"Bearer {d['tok_vp']}"})
    assert res.status_code == 200


def test_30_parent_attempt_bulk_mark_teacher_attendance_denied(client: TestClient, setup_teacher_security_data):
    d = setup_teacher_security_data
    payload = {"attendance_date": date.today().isoformat(), "items": []}
    res = client.post("/api/v1/teachers/attendance/bulk", json=payload, headers={"Authorization": f"Bearer {d['tok_parent']}"})
    assert res.status_code == 403
