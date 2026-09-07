import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.common.enums import Gender
from app.common.enums.visitor import HostType, IdProofType, VisitorStatus
from app.database.common_model import CommonModel
from app.dependencies.database import get_db
from app.identity.models.role import IdentityRole
from app.identity.models.user import IdentityUser
from app.identity.security.current_user import get_current_user
from app.main import app as fastapi_app
from app.models.academic_year.academic_year import AcademicYear
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.parent.parent import Parent
from app.models.student.student import Student
from app.models.teacher.teacher import Teacher
from app.models.visitor.visitor import Visitor


@pytest.fixture(autouse=True)
def setup_visitor_api_tables(db_session):
    CommonModel.metadata.create_all(db_session.get_bind())
    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    yield
    fastapi_app.dependency_overrides.pop(get_db, None)
    fastapi_app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def visitor_api_fixture(db_session):
    # School A
    school_a = School(
        id=uuid.uuid4(),
        name="Visitor API School A",
        code=f"VAA-{uuid.uuid4().hex[:4]}",
        address_line1="100 Gate Pass Rd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    # School B
    school_b = School(
        id=uuid.uuid4(),
        name="Visitor API School B",
        code=f"VAB-{uuid.uuid4().hex[:4]}",
        address_line1="200 Gate Pass Rd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([school_a, school_b])
    db_session.flush()

    role_super_a = IdentityRole(id=uuid.uuid4(), school_id=school_a.id, name="Super Admin")
    role_super_b = IdentityRole(id=uuid.uuid4(), school_id=school_b.id, name="Super Admin")
    db_session.add_all([role_super_a, role_super_b])
    db_session.flush()

    user_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email="admin.a@visitor.com",
        username="admin_a",
        password_hash="hash",
        first_name="Admin",
        last_name="A",
        is_active=True,
    )
    user_a.roles.append(role_super_a)

    user_b = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_b.id,
        email="admin.b@visitor.com",
        username="admin_b",
        password_hash="hash",
        first_name="Admin",
        last_name="B",
        is_active=True,
    )
    user_b.roles.append(role_super_b)
    db_session.add_all([user_a, user_b])
    db_session.flush()

    # Teacher host in School A
    teacher_a = Teacher(
        id=uuid.uuid4(),
        school_id=school_a.id,
        employee_id=f"EMP-{uuid.uuid4().hex[:4]}",
        first_name="Theresa",
        last_name="Teacher",
        gender=Gender.FEMALE,
        date_of_birth="1985-01-01",
        email="teacher.a@school.com",
        phone="9876500001",
        joining_date="2020-01-01",
        qualification="M.Ed",
        address_line1="100 School Lane",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    # Teacher host in School B
    teacher_b = Teacher(
        id=uuid.uuid4(),
        school_id=school_b.id,
        employee_id=f"EMP-{uuid.uuid4().hex[:4]}",
        first_name="Tobias",
        last_name="Teacher",
        gender=Gender.MALE,
        date_of_birth="1985-01-01",
        email="teacher.b@school.com",
        phone="9876500002",
        joining_date="2020-01-01",
        qualification="M.Sc",
        address_line1="200 School Lane",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([teacher_a, teacher_b])
    db_session.flush()

    # Academic Year, Class, Section, Student in School A
    ay_a = AcademicYear(
        id=uuid.uuid4(), school_id=school_a.id, name="2026-2027", start_date="2026-06-01", end_date="2027-05-31"
    )
    sc_a = SchoolClass(id=uuid.uuid4(), school_id=school_a.id, name="Grade 10", display_order=10)
    sec_a = Section(id=uuid.uuid4(), school_class_id=sc_a.id, name="Section A")
    parent_a = Parent(
        id=uuid.uuid4(),
        school_id=school_a.id,
        father_name="Perry Parent",
        primary_phone=f"98765{uuid.uuid4().hex[:5]}",
        address_line1="100 Parent Rd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(parent_a)
    db_session.flush()

    student_a = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        school_class_id=sc_a.id,
        section_id=sec_a.id,
        parent_id=parent_a.id,
        admission_number=f"ADM-{uuid.uuid4().hex[:4]}",
        roll_number=f"R-{uuid.uuid4().hex[:4]}",
        first_name="Sammy",
        last_name="Student",
        gender=Gender.MALE,
        date_of_birth="2010-01-01",
        admission_date="2026-06-01",
        address_line1="100 Student Rd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([ay_a, sc_a, sec_a, student_a])
    db_session.commit()

    return {
        "school_a": school_a,
        "school_b": school_b,
        "user_a": user_a,
        "user_b": user_b,
        "teacher_a": teacher_a,
        "teacher_b": teacher_b,
        "student_a": student_a,
    }


# ==============================================================================
# 1. CHECK-IN API TESTS
# ==============================================================================

def test_check_in_visitor_success(visitor_api_fixture):
    user_a = visitor_api_fixture["user_a"]
    teacher_a = visitor_api_fixture["teacher_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a

    client = TestClient(fastapi_app)
    payload = {
        "visitor_name": "Marcus Vance",
        "phone": "9876543210",
        "email": "marcus@example.com",
        "id_proof_type": "AADHAAR",
        "id_proof_number": "9999-8888-7777",
        "purpose": "Academic Discussion",
        "host_type": "TEACHER",
        "host_id": str(teacher_a.id),
        "remarks": "Registered at front gate",
    }

    res = client.post("/api/v1/visitors/check-in", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["visitor_name"] == "Marcus Vance"
    assert data["phone"] == "9876543210"
    assert data["status"] == "CHECKED_IN"
    assert data["check_in_time"] is not None
    assert data["pass_number"].startswith("GP-")
    assert data["id_proof_number"] == "9999-8888-7777"


def test_check_in_visitor_with_student_host(visitor_api_fixture):
    user_a = visitor_api_fixture["user_a"]
    student_a = visitor_api_fixture["student_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a

    client = TestClient(fastapi_app)
    payload = {
        "visitor_name": "Parent Visitor",
        "phone": "9123456789",
        "purpose": "Early Pickup",
        "host_type": "STUDENT",
        "host_id": str(student_a.id),
    }

    res = client.post("/api/v1/visitors/check-in", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["host_type"] == "STUDENT"
    assert data["host_id"] == str(student_a.id)


def test_check_in_visitor_cross_tenant_host_rejection(visitor_api_fixture):
    user_a = visitor_api_fixture["user_a"]
    teacher_b = visitor_api_fixture["teacher_b"]  # Teacher in School B!
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a

    client = TestClient(fastapi_app)
    payload = {
        "visitor_name": "Intruder Visitor",
        "phone": "9000000000",
        "purpose": "Malicious Visit",
        "host_type": "TEACHER",
        "host_id": str(teacher_b.id),
    }

    res = client.post("/api/v1/visitors/check-in", json=payload)
    assert res.status_code == 422  # Validation exception
    assert "does not belong to your school" in res.json()["error"]["message"]


def test_check_in_duplicate_active_visitor_rejection(visitor_api_fixture):
    user_a = visitor_api_fixture["user_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a

    client = TestClient(fastapi_app)
    payload = {
        "visitor_name": "Repeat Visitor",
        "phone": "9555555555",
        "purpose": "Delivery",
    }

    res1 = client.post("/api/v1/visitors/check-in", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/visitors/check-in", json=payload)
    assert res2.status_code == 422
    assert "already actively checked in" in res2.json()["error"]["message"]


# ==============================================================================
# 2. CHECK-OUT API TESTS
# ==============================================================================

def test_check_out_visitor_success(visitor_api_fixture):
    user_a = visitor_api_fixture["user_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a

    client = TestClient(fastapi_app)
    # Check in first
    check_in_res = client.post(
        "/api/v1/visitors/check-in",
        json={"visitor_name": "Checkout Test", "phone": "9777777777", "purpose": "Meeting"},
    )
    assert check_in_res.status_code == 201
    visitor_id = check_in_res.json()["id"]

    # Check out
    check_out_res = client.post(
        f"/api/v1/visitors/{visitor_id}/check-out",
        json={"remarks": "Visit completed successfully"},
    )
    assert check_out_res.status_code == 200
    data = check_out_res.json()
    assert data["status"] == "CHECKED_OUT"
    assert data["check_out_time"] is not None
    assert data["remarks"] == "Visit completed successfully"


def test_check_out_already_checked_out_rejection(visitor_api_fixture):
    user_a = visitor_api_fixture["user_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a

    client = TestClient(fastapi_app)
    check_in_res = client.post(
        "/api/v1/visitors/check-in",
        json={"visitor_name": "Double Checkout Test", "phone": "9888888888", "purpose": "Meeting"},
    )
    visitor_id = check_in_res.json()["id"]

    # First checkout
    res1 = client.post(f"/api/v1/visitors/{visitor_id}/check-out")
    assert res1.status_code == 200

    # Second checkout fails
    res2 = client.post(f"/api/v1/visitors/{visitor_id}/check-out")
    assert res2.status_code == 422
    assert "already checked out" in res2.json()["error"]["message"]


def test_check_out_cross_tenant_rejection(visitor_api_fixture):
    user_a = visitor_api_fixture["user_a"]
    user_b = visitor_api_fixture["user_b"]

    # School A user checks in visitor in School A
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a
    client = TestClient(fastapi_app)
    check_in_res = client.post(
        "/api/v1/visitors/check-in",
        json={"visitor_name": "School A Visitor", "phone": "9111111111", "purpose": "Meeting"},
    )
    visitor_id = check_in_res.json()["id"]

    # School B user attempts checkout on School A's visitor -> DENY (404)
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_b
    res_checkout = client.post(f"/api/v1/visitors/{visitor_id}/check-out")
    assert res_checkout.status_code == 404


# ==============================================================================
# 3. LIST & PRIVACY PROTECTION API TESTS
# ==============================================================================

def test_list_visitors_tenant_isolation_and_privacy(visitor_api_fixture):
    user_a = visitor_api_fixture["user_a"]
    user_b = visitor_api_fixture["user_b"]
    client = TestClient(fastapi_app)

    # Check in visitor in School A
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a
    client.post(
        "/api/v1/visitors/check-in",
        json={
            "visitor_name": "School A Visitor",
            "phone": "9222222222",
            "purpose": "Audit",
            "id_proof_type": "PAN",
            "id_proof_number": "ABCDE1234F",
        },
    )

    # Check in visitor in School B
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_b
    client.post(
        "/api/v1/visitors/check-in",
        json={
            "visitor_name": "School B Visitor",
            "phone": "9333333333",
            "purpose": "Inspection",
            "id_proof_type": "PASSPORT",
            "id_proof_number": "Z9876543",
        },
    )

    # Query list as School A user
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a
    list_a = client.get("/api/v1/visitors").json()
    assert list_a["total"] == 1
    assert list_a["items"][0]["visitor_name"] == "School A Visitor"
    # PRIVACY PROTECTION ASSERTION: Summary list response MUST NOT expose id_proof_number!
    assert "id_proof_number" not in list_a["items"][0]

    # Query list as School B user
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_b
    list_b = client.get("/api/v1/visitors").json()
    assert list_b["total"] == 1
    assert list_b["items"][0]["visitor_name"] == "School B Visitor"
    assert "id_proof_number" not in list_b["items"][0]


def test_list_visitors_filtering_and_search(visitor_api_fixture):
    user_a = visitor_api_fixture["user_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a
    client = TestClient(fastapi_app)

    # Add visitors
    client.post("/api/v1/visitors/check-in", json={"visitor_name": "Alice Green", "phone": "9444444441", "purpose": "Admissions"})
    client.post("/api/v1/visitors/check-in", json={"visitor_name": "Bob Brown", "phone": "9444444442", "purpose": "Vendor Maintenance"})

    # Search filter
    res_search = client.get("/api/v1/visitors?search=Admissions")
    assert res_search.status_code == 200
    data = res_search.json()
    assert data["total"] == 1
    assert data["items"][0]["visitor_name"] == "Alice Green"


# ==============================================================================
# 4. DETAIL API TESTS
# ==============================================================================

def test_get_visitor_detail_authorized(visitor_api_fixture):
    user_a = visitor_api_fixture["user_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a
    client = TestClient(fastapi_app)

    check_in_res = client.post(
        "/api/v1/visitors/check-in",
        json={
            "visitor_name": "Detailed Visitor",
            "phone": "9666666666",
            "purpose": "Interview",
            "id_proof_type": "PASSPORT",
            "id_proof_number": "A12345678",
        },
    )
    visitor_id = check_in_res.json()["id"]

    # Authorized detail view EXPOSES full operational identity details
    detail_res = client.get(f"/api/v1/visitors/{visitor_id}")
    assert detail_res.status_code == 200
    data = detail_res.json()
    assert data["visitor_name"] == "Detailed Visitor"
    assert data["id_proof_number"] == "A12345678"


def test_get_visitor_detail_cross_tenant_denial(visitor_api_fixture):
    user_a = visitor_api_fixture["user_a"]
    user_b = visitor_api_fixture["user_b"]
    client = TestClient(fastapi_app)

    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a
    check_in_res = client.post(
        "/api/v1/visitors/check-in",
        json={"visitor_name": "School A Private Visitor", "phone": "9998887776", "purpose": "Confidential"},
    )
    visitor_id = check_in_res.json()["id"]

    # School B user attempts detail fetch -> DENY (404)
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_b
    res_detail = client.get(f"/api/v1/visitors/{visitor_id}")
    assert res_detail.status_code == 404
