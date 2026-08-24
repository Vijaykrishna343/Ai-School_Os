"""
Relationship Security Tests for Attendance API Endpoints (SEC-003B).
Tests HTTP route authorization for:
- GET /api/v1/attendance
- GET /api/v1/attendance/{attendance_id}
- GET /api/v1/export/attendance
"""
import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient

from app.common.enums import AttendanceStatus, Gender, StudentStatus
from app.identity.models import IdentityPermission, IdentityRole, IdentityRolePermission, IdentityUser, IdentityUserRole
from app.identity.security.jwt_manager import jwt_manager
from app.models.attendance.attendance import Attendance
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.student.student import Student
from app.models.academic_year.academic_year import AcademicYear
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.main import app

client = TestClient(app)


def create_role_with_permissions(db, school_id, role_name, permission_names):
    role = IdentityRole(
        id=uuid.uuid4(),
        school_id=school_id,
        name=role_name,
        description=f"{role_name} test role",
        is_system=True,
    )
    db.add(role)
    db.commit()

    for perm_name in permission_names:
        from app.identity.repositories import permission_repository
        perm = permission_repository.get_by_name(db, perm_name)
        if perm:
            rp = IdentityRolePermission(role_id=role.id, permission_id=perm.id)
            db.add(rp)
    db.commit()
    return role


def create_user_and_auth_headers(db, school_id, email, role, username=None, phone=None):
    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_id,
        email=email,
        username=username,
        phone=phone,
        password_hash="hash123",
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    db.add(user)
    db.commit()

    ur = IdentityUserRole(user_id=user.id, role_id=role.id)
    db.add(ur)
    db.commit()

    token = jwt_manager.create_access_token(user.id, school_id)
    return user, {"Authorization": f"Bearer {token}"}


@pytest.fixture
def attendance_api_fixture(db_session):
    """
    Sets up School A & School B, Parent A (with Child A1 & Child A2), Parent B (with Child B1),
    Parent C (no children), Student A1, Student B1, Teacher, SuperAdmin, cross-tenant entities,
    and attendance records for each student.
    """
    db = db_session

    from app.identity.seeders import seed_identity
    seed_identity(db)

    # 1. School A & School B
    school_a = School(
        id=uuid.uuid4(),
        name="School Alpha",
        code=f"SCHA_{uuid.uuid4().hex[:4]}",
        address_line1="100 Alpha St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    school_b = School(
        id=uuid.uuid4(),
        name="School Beta",
        code=f"SCHB_{uuid.uuid4().hex[:4]}",
        address_line1="200 Beta St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110002",
    )
    db.add_all([school_a, school_b])
    db.commit()

    # 2. Roles with attendance.view & attendance.export permissions
    perms = ["attendance.view", "attendance.export", "student.view"]
    parent_role = create_role_with_permissions(db, school_a.id, "Parent", perms)
    student_role = create_role_with_permissions(db, school_a.id, "Student", perms)
    teacher_role = create_role_with_permissions(db, school_a.id, "Teacher", perms)
    superadmin_role = create_role_with_permissions(db, school_a.id, "Super Admin", perms)

    # 3. Parents
    parent_a = Parent(
        id=uuid.uuid4(),
        school_id=school_a.id,
        father_name="Father Alpha",
        primary_phone="+919876543230",
        email="parenta_att@schoola.com",
        address_line1="123 Main St",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110001",
    )
    parent_b = Parent(
        id=uuid.uuid4(),
        school_id=school_a.id,
        father_name="Father Beta",
        primary_phone="+919876543231",
        email="parentb_att@schoola.com",
        address_line1="456 Park Ave",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110001",
    )
    parent_no_children = Parent(
        id=uuid.uuid4(),
        school_id=school_a.id,
        father_name="Father Childless",
        primary_phone="+919876543232",
        email="parent_no_child_att@schoola.com",
        address_line1="789 Lonely Rd",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110001",
    )
    parent_b_school = Parent(
        id=uuid.uuid4(),
        school_id=school_b.id,
        father_name="Father School B",
        primary_phone="+919876543239",
        email="parent_b_school_att@schoolb.com",
        address_line1="100 Beta Rd",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110002",
    )
    db.add_all([parent_a, parent_b, parent_no_children, parent_b_school])
    db.commit()

    # 4. Academic Year, Class, Section
    ay_a = AcademicYear(id=uuid.uuid4(), school_id=school_a.id, name="2025-2026", start_date=date(2025, 4, 1), end_date=date(2026, 3, 31))
    sc_a = SchoolClass(id=uuid.uuid4(), school_id=school_a.id, name="Class 10", display_order=1)
    db.add_all([ay_a, sc_a])
    db.commit()
    sec_a = Section(id=uuid.uuid4(), school_class_id=sc_a.id, name="Section A")
    db.add(sec_a)
    db.commit()

    # Students for Parent A (2 children)
    child_a1 = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        parent_id=parent_a.id,
        academic_year_id=ay_a.id,
        school_class_id=sc_a.id,
        section_id=sec_a.id,
        admission_number="ADM-ATT-A1",
        roll_number="01",
        first_name="ChildA1",
        last_name="Alpha",
        gender=Gender.MALE,
        date_of_birth=date(2010, 1, 1),
        admission_date=date(2025, 4, 1),
        email="child_a1_att@schoola.com",
        address_line1="123 Main St",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110001",
        status=StudentStatus.ACTIVE,
    )
    child_a2 = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        parent_id=parent_a.id,
        academic_year_id=ay_a.id,
        school_class_id=sc_a.id,
        section_id=sec_a.id,
        admission_number="ADM-ATT-A2",
        roll_number="02",
        first_name="ChildA2",
        last_name="Alpha",
        gender=Gender.FEMALE,
        date_of_birth=date(2012, 2, 2),
        admission_date=date(2025, 4, 1),
        email="child_a2_att@schoola.com",
        address_line1="123 Main St",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110001",
        status=StudentStatus.ACTIVE,
    )
    # Student for Parent B (1 child)
    child_b1 = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        parent_id=parent_b.id,
        academic_year_id=ay_a.id,
        school_class_id=sc_a.id,
        section_id=sec_a.id,
        admission_number="ADM-ATT-B1",
        roll_number="03",
        first_name="ChildB1",
        last_name="Beta",
        gender=Gender.MALE,
        date_of_birth=date(2011, 3, 3),
        admission_date=date(2025, 4, 1),
        email="child_b1_att@schoola.com",
        address_line1="456 Park Ave",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110001",
        status=StudentStatus.ACTIVE,
    )

    # Student in School B
    ay_b = AcademicYear(id=uuid.uuid4(), school_id=school_b.id, name="2025-2026", start_date=date(2025, 4, 1), end_date=date(2026, 3, 31))
    sc_b = SchoolClass(id=uuid.uuid4(), school_id=school_b.id, name="Class 10", display_order=1)
    db.add_all([ay_b, sc_b])
    db.commit()
    sec_b = Section(id=uuid.uuid4(), school_class_id=sc_b.id, name="Section B")
    db.add(sec_b)
    db.commit()

    student_school_b = Student(
        id=uuid.uuid4(),
        school_id=school_b.id,
        parent_id=parent_b_school.id,
        academic_year_id=ay_b.id,
        school_class_id=sc_b.id,
        section_id=sec_b.id,
        admission_number="ADM-ATT-SCHB",
        roll_number="01",
        first_name="ChildB",
        last_name="SchoolB",
        gender=Gender.FEMALE,
        date_of_birth=date(2010, 5, 5),
        admission_date=date(2025, 4, 1),
        email="student_b_att@schoolb.com",
        address_line1="100 Beta Rd",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110002",
        status=StudentStatus.ACTIVE,
    )
    db.add_all([child_a1, child_a2, child_b1, student_school_b])
    db.commit()

    # 5. Attendance Records
    att_a1 = Attendance(
        id=uuid.uuid4(),
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        school_class_id=sc_a.id,
        section_id=sec_a.id,
        student_id=child_a1.id,
        attendance_date=date(2026, 8, 10),
        status=AttendanceStatus.PRESENT,
        remarks="Present child A1",
    )
    att_a2 = Attendance(
        id=uuid.uuid4(),
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        school_class_id=sc_a.id,
        section_id=sec_a.id,
        student_id=child_a2.id,
        attendance_date=date(2026, 8, 10),
        status=AttendanceStatus.PRESENT,
        remarks="Present child A2",
    )
    att_b1 = Attendance(
        id=uuid.uuid4(),
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        school_class_id=sc_a.id,
        section_id=sec_a.id,
        student_id=child_b1.id,
        attendance_date=date(2026, 8, 10),
        status=AttendanceStatus.ABSENT,
        remarks="Absent child B1",
    )
    att_sch_b = Attendance(
        id=uuid.uuid4(),
        school_id=school_b.id,
        academic_year_id=ay_b.id,
        school_class_id=sc_b.id,
        section_id=sec_b.id,
        student_id=student_school_b.id,
        attendance_date=date(2026, 8, 10),
        status=AttendanceStatus.PRESENT,
        remarks="Present school B",
    )
    db.add_all([att_a1, att_a2, att_b1, att_sch_b])
    db.commit()

    # 6. Identity Users & Auth Headers
    user_parent_a, headers_parent_a = create_user_and_auth_headers(
        db, school_a.id, "parenta_att@schoola.com", parent_role, phone="+919876543230"
    )
    user_parent_b, headers_parent_b = create_user_and_auth_headers(
        db, school_a.id, "parentb_att@schoola.com", parent_role, phone="+919876543231"
    )
    user_parent_no_child, headers_parent_no_child = create_user_and_auth_headers(
        db, school_a.id, "parent_no_child_att@schoola.com", parent_role, phone="+919876543232"
    )
    user_student_a1, headers_student_a1 = create_user_and_auth_headers(
        db, school_a.id, "child_a1_att@schoola.com", student_role, username="ADM-ATT-A1"
    )
    user_student_b1, headers_student_b1 = create_user_and_auth_headers(
        db, school_a.id, "child_b1_att@schoola.com", student_role, username="ADM-ATT-B1"
    )
    user_teacher, headers_teacher = create_user_and_auth_headers(
        db, school_a.id, "teacher_att@schoola.com", teacher_role
    )
    user_superadmin, headers_superadmin = create_user_and_auth_headers(
        db, school_a.id, "superadmin_att@schoola.com", superadmin_role
    )

    return {
        "school_a": school_a,
        "school_b": school_b,
        "parent_a": parent_a,
        "child_a1": child_a1,
        "child_a2": child_a2,
        "child_b1": child_b1,
        "student_school_b": student_school_b,
        "att_a1": att_a1,
        "att_a2": att_a2,
        "att_b1": att_b1,
        "att_sch_b": att_sch_b,
        "headers_parent_a": headers_parent_a,
        "headers_parent_b": headers_parent_b,
        "headers_parent_no_child": headers_parent_no_child,
        "headers_student_a1": headers_student_a1,
        "headers_student_b1": headers_student_b1,
        "headers_teacher": headers_teacher,
        "headers_superadmin": headers_superadmin,
    }


# ============================================================================
# PARENT ATTENDANCE TESTS
# ============================================================================

def test_parent_list_attendance_returns_only_linked_children(client, attendance_api_fixture):
    fx = attendance_api_fixture
    response = client.get("/api/v1/attendance", headers=fx["headers_parent_a"])
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 2
    retrieved_student_ids = {item["student_id"] for item in data["items"]}
    assert retrieved_student_ids == {str(fx["child_a1"].id), str(fx["child_a2"].id)}


def test_parent_get_own_child_attendance_detail_success(client, attendance_api_fixture):
    fx = attendance_api_fixture
    url = f"/api/v1/attendance/{fx['att_a1'].id}"
    response = client.get(url, headers=fx["headers_parent_a"])
    assert response.status_code == 200
    assert response.json()["data"]["id"] == str(fx["att_a1"].id)


def test_parent_get_other_parent_child_attendance_detail_denied(client, attendance_api_fixture):
    fx = attendance_api_fixture
    url = f"/api/v1/attendance/{fx['att_b1'].id}"
    response = client.get(url, headers=fx["headers_parent_a"])
    assert response.status_code == 403


def test_parent_cannot_get_unrelated_student_attendance_via_filter(client, attendance_api_fixture):
    fx = attendance_api_fixture
    # Parent A passes student_id of Child B1
    url = f"/api/v1/attendance?student_id={fx['child_b1'].id}"
    response = client.get(url, headers=fx["headers_parent_a"])
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 0
    assert data["items"] == []


def test_parent_cannot_access_cross_tenant_attendance(client, attendance_api_fixture):
    fx = attendance_api_fixture
    url = f"/api/v1/attendance/{fx['att_sch_b'].id}"
    response = client.get(url, headers=fx["headers_parent_a"])
    assert response.status_code in (403, 404)


def test_parent_with_no_children_returns_empty_attendance_list(client, attendance_api_fixture):
    fx = attendance_api_fixture
    response = client.get("/api/v1/attendance", headers=fx["headers_parent_no_child"])
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 0
    assert data["items"] == []


# ============================================================================
# STUDENT ATTENDANCE TESTS
# ============================================================================

def test_student_get_own_attendance_detail_success(client, attendance_api_fixture):
    fx = attendance_api_fixture
    url = f"/api/v1/attendance/{fx['att_a1'].id}"
    response = client.get(url, headers=fx["headers_student_a1"])
    assert response.status_code == 200
    assert response.json()["data"]["id"] == str(fx["att_a1"].id)


def test_student_get_other_student_attendance_detail_denied(client, attendance_api_fixture):
    fx = attendance_api_fixture
    url = f"/api/v1/attendance/{fx['att_a2'].id}"
    response = client.get(url, headers=fx["headers_student_a1"])
    assert response.status_code == 403


def test_student_cannot_access_cross_tenant_attendance(client, attendance_api_fixture):
    fx = attendance_api_fixture
    url = f"/api/v1/attendance/{fx['att_sch_b'].id}"
    response = client.get(url, headers=fx["headers_student_a1"])
    assert response.status_code in (403, 404)


def test_student_list_attendance_returns_only_self(client, attendance_api_fixture):
    fx = attendance_api_fixture
    response = client.get("/api/v1/attendance", headers=fx["headers_student_a1"])
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["student_id"] == str(fx["child_a1"].id)


def test_student_query_tampering_cannot_expose_others(client, attendance_api_fixture):
    fx = attendance_api_fixture
    # Student A1 attempts to query with student_id of Child B1
    url = f"/api/v1/attendance?student_id={fx['child_b1'].id}"
    response = client.get(url, headers=fx["headers_student_a1"])
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 0
    assert data["items"] == []


# ============================================================================
# EXPORT ATTENDANCE TESTS
# ============================================================================

def test_parent_attendance_export_contains_only_linked_children(client, attendance_api_fixture):
    fx = attendance_api_fixture
    response = client.get("/api/v1/export/attendance", headers=fx["headers_parent_a"])
    assert response.status_code == 200
    content = response.text
    # Should include ChildA1 and ChildA2, but NOT ChildB1
    assert "ChildA1 Alpha" in content or "ADM-ATT-A1" in content
    assert "ChildB1 Beta" not in content and "ADM-ATT-B1" not in content


def test_student_attendance_export_contains_only_self(client, attendance_api_fixture):
    fx = attendance_api_fixture
    response = client.get("/api/v1/export/attendance", headers=fx["headers_student_a1"])
    assert response.status_code == 200
    content = response.text
    assert "ADM-ATT-A1" in content
    assert "ADM-ATT-A2" not in content
    assert "ADM-ATT-B1" not in content


def test_parent_export_filter_tampering_cannot_expand_scope(client, attendance_api_fixture):
    fx = attendance_api_fixture
    response = client.get(
        f"/api/v1/export/attendance?section_id={fx['child_b1'].section_id}",
        headers=fx["headers_parent_a"],
    )
    assert response.status_code == 200
    content = response.text
    assert "ADM-ATT-B1" not in content


# ============================================================================
# STAFF & SUPER ADMIN TESTS
# ============================================================================

def test_teacher_unrestricted_attendance_list_and_detail_success(client, attendance_api_fixture):
    fx = attendance_api_fixture
    res_list = client.get("/api/v1/attendance", headers=fx["headers_teacher"])
    assert res_list.status_code == 200
    assert res_list.json()["data"]["total"] == 3

    res_detail = client.get(f"/api/v1/attendance/{fx['att_b1'].id}", headers=fx["headers_teacher"])
    assert res_detail.status_code == 200
    assert res_detail.json()["data"]["id"] == str(fx["att_b1"].id)


def test_superadmin_unrestricted_attendance_access_success(client, attendance_api_fixture):
    fx = attendance_api_fixture
    res_list = client.get("/api/v1/attendance", headers=fx["headers_superadmin"])
    assert res_list.status_code == 200

    res_detail = client.get(f"/api/v1/attendance/{fx['att_a1'].id}", headers=fx["headers_superadmin"])
    assert res_detail.status_code == 200
