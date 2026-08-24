"""
Relationship Security Tests for Student API Endpoints (SEC-002B).
Tests HTTP route authorization for GET /students and GET /students/{student_id}.
"""
import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient

from app.common.enums import Gender, StudentStatus
from app.identity.models import IdentityPermission, IdentityRole, IdentityRolePermission, IdentityUser, IdentityUserRole
from app.identity.security.jwt_manager import jwt_manager
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
def student_api_fixture(db_session):
    """
    Sets up School A & School B, Parent A (with 2 children), Parent B (with 1 child),
    Parent C (no children), Student A, Student B, Teacher, SuperAdmin, and cross-tenant entities.
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

    # 2. Roles with student.view permission
    parent_role = create_role_with_permissions(db, school_a.id, "Parent", ["student.view"])
    student_role = create_role_with_permissions(db, school_a.id, "Student", ["student.view"])
    teacher_role = create_role_with_permissions(db, school_a.id, "Teacher", ["student.view"])
    superadmin_role = create_role_with_permissions(db, school_a.id, "Super Admin", ["student.view"])

    # 3. Parents
    parent_a = Parent(
        id=uuid.uuid4(),
        school_id=school_a.id,
        father_name="Father Alpha",
        primary_phone="+919876543210",
        email="parenta@schoola.com",
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
        primary_phone="+919876543211",
        email="parentb@schoola.com",
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
        primary_phone="+919876543212",
        email="parent_no_child@schoola.com",
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
        primary_phone="+919876543219",
        email="parent_b_school@schoolb.com",
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
        admission_number="ADM-PA-001",
        roll_number="01",
        first_name="ChildA1",
        last_name="Alpha",
        gender=Gender.MALE,
        date_of_birth=date(2010, 1, 1),
        admission_date=date(2025, 4, 1),
        email="child_a1@schoola.com",
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
        admission_number="ADM-PA-002",
        roll_number="02",
        first_name="ChildA2",
        last_name="Alpha",
        gender=Gender.FEMALE,
        date_of_birth=date(2012, 2, 2),
        admission_date=date(2025, 4, 1),
        email="child_a2@schoola.com",
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
        admission_number="ADM-PB-001",
        roll_number="03",
        first_name="ChildB1",
        last_name="Beta",
        gender=Gender.MALE,
        date_of_birth=date(2011, 3, 3),
        admission_date=date(2025, 4, 1),
        email="child_b1@schoola.com",
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
        admission_number="ADM-B-001",
        roll_number="01",
        first_name="ChildB",
        last_name="SchoolB",
        gender=Gender.FEMALE,
        date_of_birth=date(2010, 5, 5),
        admission_date=date(2025, 4, 1),
        email="student_b@schoolb.com",
        address_line1="100 Beta Rd",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110002",
        status=StudentStatus.ACTIVE,
    )
    db.add_all([child_a1, child_a2, child_b1, student_school_b])
    db.commit()

    # 5. Identity Users & Headers
    user_parent_a, headers_parent_a = create_user_and_auth_headers(
        db, school_a.id, "parenta@schoola.com", parent_role, phone="+919876543210"
    )
    user_parent_b, headers_parent_b = create_user_and_auth_headers(
        db, school_a.id, "parentb@schoola.com", parent_role, phone="+919876543211"
    )
    user_parent_no_child, headers_parent_no_child = create_user_and_auth_headers(
        db, school_a.id, "parent_no_child@schoola.com", parent_role, phone="+919876543212"
    )
    user_student_a1, headers_student_a1 = create_user_and_auth_headers(
        db, school_a.id, "child_a1@schoola.com", student_role, username="ADM-PA-001"
    )
    user_student_b1, headers_student_b1 = create_user_and_auth_headers(
        db, school_a.id, "child_b1@schoola.com", student_role, username="ADM-PB-001"
    )
    user_teacher, headers_teacher = create_user_and_auth_headers(
        db, school_a.id, "teacher@schoola.com", teacher_role
    )
    user_superadmin, headers_superadmin = create_user_and_auth_headers(
        db, school_a.id, "superadmin@schoola.com", superadmin_role
    )

    return {
        "school_a": school_a,
        "school_b": school_b,
        "parent_a": parent_a,
        "child_a1": child_a1,
        "child_a2": child_a2,
        "child_b1": child_b1,
        "student_school_b": student_school_b,
        "headers_parent_a": headers_parent_a,
        "headers_parent_b": headers_parent_b,
        "headers_parent_no_child": headers_parent_no_child,
        "headers_student_a1": headers_student_a1,
        "headers_student_b1": headers_student_b1,
        "headers_teacher": headers_teacher,
        "headers_superadmin": headers_superadmin,
    }


# ============================================================================
# PARENT TESTS
# ============================================================================

def test_parent_list_returns_only_own_linked_children(client, student_api_fixture):
    fx = student_api_fixture
    response = client.get("/api/v1/students", headers=fx["headers_parent_a"])
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 2
    retrieved_ids = {item["id"] for item in data["items"]}
    assert retrieved_ids == {str(fx["child_a1"].id), str(fx["child_a2"].id)}


def test_parent_get_own_child_detail_success(client, student_api_fixture):
    fx = student_api_fixture
    url = f"/api/v1/students/{fx['child_a1'].id}"
    response = client.get(url, headers=fx["headers_parent_a"])
    assert response.status_code == 200
    assert response.json()["data"]["id"] == str(fx["child_a1"].id)


def test_parent_get_other_parent_child_detail_denied(client, student_api_fixture):
    fx = student_api_fixture
    url = f"/api/v1/students/{fx['child_b1'].id}"
    response = client.get(url, headers=fx["headers_parent_a"])
    assert response.status_code == 403


def test_parent_get_cross_tenant_child_denied(client, student_api_fixture):
    fx = student_api_fixture
    url = f"/api/v1/students/{fx['student_school_b'].id}"
    response = client.get(url, headers=fx["headers_parent_a"])
    assert response.status_code in (403, 404)


def test_parent_with_no_children_returns_empty_list(client, student_api_fixture):
    fx = student_api_fixture
    response = client.get("/api/v1/students", headers=fx["headers_parent_no_child"])
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 0
    assert data["items"] == []


# ============================================================================
# STUDENT TESTS
# ============================================================================

def test_student_get_own_detail_success(client, student_api_fixture):
    fx = student_api_fixture
    url = f"/api/v1/students/{fx['child_a1'].id}"
    response = client.get(url, headers=fx["headers_student_a1"])
    assert response.status_code == 200
    assert response.json()["data"]["id"] == str(fx["child_a1"].id)


def test_student_get_other_student_detail_denied(client, student_api_fixture):
    fx = student_api_fixture
    url = f"/api/v1/students/{fx['child_a2'].id}"
    response = client.get(url, headers=fx["headers_student_a1"])
    assert response.status_code == 403


def test_student_get_cross_tenant_student_denied(client, student_api_fixture):
    fx = student_api_fixture
    url = f"/api/v1/students/{fx['student_school_b'].id}"
    response = client.get(url, headers=fx["headers_student_a1"])
    assert response.status_code in (403, 404)


def test_student_list_returns_only_self(client, student_api_fixture):
    fx = student_api_fixture
    response = client.get("/api/v1/students", headers=fx["headers_student_a1"])
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == str(fx["child_a1"].id)


def test_student_search_and_filter_tampering_cannot_leak_others(client, student_api_fixture):
    fx = student_api_fixture
    # Student A1 attempts search for "ChildB1" or filtering by parent_b ID
    response = client.get(
        f"/api/v1/students?search=ChildB1&parent_id={fx['child_b1'].parent_id}",
        headers=fx["headers_student_a1"],
    )
    assert response.status_code == 200
    data = response.json()["data"]
    # Scope remains locked to Student A1. If Student A1 doesn't match search/filter, returns 0 items, never Child B1.
    for item in data["items"]:
        assert item["id"] == str(fx["child_a1"].id)


# ============================================================================
# STAFF & SUPER ADMIN TESTS
# ============================================================================

def test_teacher_unrestricted_list_and_detail_success(client, student_api_fixture):
    fx = student_api_fixture
    # Teacher lists students -> returns all students in school A (3)
    res_list = client.get("/api/v1/students", headers=fx["headers_teacher"])
    assert res_list.status_code == 200
    assert res_list.json()["data"]["total"] == 3

    # Teacher gets detail of any student in school A -> success
    res_detail = client.get(f"/api/v1/students/{fx['child_b1'].id}", headers=fx["headers_teacher"])
    assert res_detail.status_code == 200
    assert res_detail.json()["data"]["id"] == str(fx["child_b1"].id)


def test_superadmin_unrestricted_access_success(client, student_api_fixture):
    fx = student_api_fixture
    res_list = client.get("/api/v1/students", headers=fx["headers_superadmin"])
    assert res_list.status_code == 200

    res_detail = client.get(f"/api/v1/students/{fx['child_a1'].id}", headers=fx["headers_superadmin"])
    assert res_detail.status_code == 200
