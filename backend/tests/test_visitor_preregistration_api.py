import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.common.enums import Gender
from app.common.enums.visitor import HostType, IdProofType, VisitorStatus
from app.database.common_model import CommonModel
from app.dependencies.database import get_db
from app.identity.models.permission import IdentityPermission
from app.identity.models.role import IdentityRole
from app.identity.models.user import IdentityUser
from app.identity.security.current_user import get_current_user
from app.main import app as fastapi_app
from app.models.audit_log import AuditLog
from app.models.school.school import School
from app.models.teacher.teacher import Teacher
from app.models.visitor.visitor import Visitor


@pytest.fixture(autouse=True)
def setup_preregistration_api_tables(db_session):
    CommonModel.metadata.create_all(db_session.get_bind())
    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    yield
    fastapi_app.dependency_overrides.pop(get_db, None)
    fastapi_app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def prereg_api_fixture(db_session):
    # School A
    school_a = School(
        id=uuid.uuid4(),
        name="PreReg School A",
        code=f"PRA-{uuid.uuid4().hex[:4]}",
        address_line1="100 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    # School B
    school_b = School(
        id=uuid.uuid4(),
        name="PreReg School B",
        code=f"PRB-{uuid.uuid4().hex[:4]}",
        address_line1="200 Park Rd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([school_a, school_b])
    db_session.flush()

    # Permissions
    perm_checkin = IdentityPermission(id=uuid.uuid4(), name="visitors.checkin", action="checkin", module="VISITORS")
    perm_view = IdentityPermission(id=uuid.uuid4(), name="visitors.view", action="view", module="VISITORS")
    perm_checkout = IdentityPermission(id=uuid.uuid4(), name="visitors.checkout", action="checkout", module="VISITORS")
    db_session.add_all([perm_checkin, perm_view, perm_checkout])
    db_session.flush()

    # Roles
    role_receptionist = IdentityRole(id=uuid.uuid4(), school_id=school_a.id, name="Receptionist")
    role_unauthorized = IdentityRole(id=uuid.uuid4(), school_id=school_a.id, name="UnauthorizedUser")
    role_receptionist.permissions = [perm_checkin, perm_view, perm_checkout]
    db_session.add_all([role_receptionist, role_unauthorized])
    db_session.flush()

    # Users
    user_receptionist_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email="receptionist_a@prereg.com",
        first_name="Receptionist",
        password_hash="hash",
        is_active=True,
    )
    user_receptionist_a.roles = [role_receptionist]

    user_unauthorized_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email="unauthorized_a@prereg.com",
        first_name="Unauthorized",
        password_hash="hash",
        is_active=True,
    )
    user_unauthorized_a.roles = [role_unauthorized]

    user_b = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_b.id,
        email="receptionist_b@prereg.com",
        first_name="RecB",
        password_hash="hash",
        is_active=True,
    )
    user_b.roles = [role_receptionist]

    # Teachers
    teacher_a = Teacher(
        id=uuid.uuid4(),
        school_id=school_a.id,
        first_name="Alice",
        last_name="Teacher",
        gender=Gender.FEMALE,
        employee_id=f"EMP-A-{uuid.uuid4().hex[:4]}",
        date_of_birth=datetime(1985, 1, 1).date(),
        joining_date=datetime(2020, 1, 1).date(),
        qualification="M.Ed",
        phone=f"9800{uuid.uuid4().hex[:6]}",
        email=f"alice_{uuid.uuid4().hex[:4]}@schoola.com",
        address_line1="123 Teacher Lane",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    teacher_b = Teacher(
        id=uuid.uuid4(),
        school_id=school_b.id,
        first_name="Bob",
        last_name="Teacher",
        gender=Gender.MALE,
        employee_id=f"EMP-B-{uuid.uuid4().hex[:4]}",
        date_of_birth=datetime(1988, 5, 15).date(),
        joining_date=datetime(2021, 6, 1).date(),
        qualification="M.Ed",
        phone=f"9811{uuid.uuid4().hex[:6]}",
        email=f"bob_{uuid.uuid4().hex[:4]}@schoolb.com",
        address_line1="456 Teacher Road",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )

    db_session.add_all([user_receptionist_a, user_unauthorized_a, user_b, teacher_a, teacher_b])
    db_session.commit()

    return {
        "school_a": school_a,
        "school_b": school_b,
        "user_receptionist_a": user_receptionist_a,
        "user_unauthorized_a": user_unauthorized_a,
        "user_b": user_b,
        "teacher_a": teacher_a,
        "teacher_b": teacher_b,
    }


# =============================================================================
# PRE-REGISTRATION API TESTS
# =============================================================================

def test_01_successful_pre_registration(prereg_api_fixture, db_session):
    client = TestClient(fastapi_app)
    fastapi_app.dependency_overrides[get_current_user] = lambda: prereg_api_fixture["user_receptionist_a"]

    payload = {
        "visitor_name": "Samuel Expected",
        "phone": "9876500001",
        "email": "samuel@example.com",
        "id_proof_type": "AADHAAR",
        "id_proof_number": "1111-2222-3333",
        "purpose": "Guest Speaker Session",
        "host_type": "TEACHER",
        "host_id": str(prereg_api_fixture["teacher_a"].id),
        "remarks": "VIP Guest expected at 10 AM",
    }

    res = client.post("/api/v1/visitors/pre-register", json=payload)
    assert res.status_code == 201
    data = res.json()

    assert data["visitor_name"] == "Samuel Expected"
    assert data["phone"] == "9876500001"
    assert data["status"] == "EXPECTED"
    assert data["check_in_time"] is None
    assert data["pass_number"].startswith("GP-")

    # Verify DB state
    visitor = db_session.get(Visitor, uuid.UUID(data["id"]))
    assert visitor is not None
    assert visitor.status == VisitorStatus.EXPECTED
    assert visitor.school_id == prereg_api_fixture["school_a"].id

    # Verify Audit Log created
    audit = db_session.query(AuditLog).filter(AuditLog.action == "VISITOR_PRE_REGISTERED").first()
    assert audit is not None
    assert audit.entity_id == str(visitor.id)


def test_02_pre_registration_status_is_server_enforced(prereg_api_fixture):
    """
    Client attempt to pass status = CHECKED_IN during pre-registration should be ignored / enforced as EXPECTED.
    """
    client = TestClient(fastapi_app)
    fastapi_app.dependency_overrides[get_current_user] = lambda: prereg_api_fixture["user_receptionist_a"]

    payload = {
        "visitor_name": "Enforced Status Guest",
        "phone": "9876500002",
        "purpose": "Audit Check",
        "status": "CHECKED_IN",  # Extra field attempting to override
    }

    res = client.post("/api/v1/visitors/pre-register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "EXPECTED"
    assert data["check_in_time"] is None


def test_03_pre_registration_cross_tenant_host_rejected(prereg_api_fixture):
    """
    Attempting to register a host from School B when authenticated in School A must fail.
    """
    client = TestClient(fastapi_app)
    fastapi_app.dependency_overrides[get_current_user] = lambda: prereg_api_fixture["user_receptionist_a"]

    payload = {
        "visitor_name": "Bad Host Visitor",
        "phone": "9876500003",
        "purpose": "Meeting",
        "host_type": "TEACHER",
        "host_id": str(prereg_api_fixture["teacher_b"].id),  # Belongs to School B!
    }

    res = client.post("/api/v1/visitors/pre-register", json=payload)
    assert res.status_code == 422
    err_msg = res.json().get("error", {}).get("message", res.json().get("detail", str(res.json())))
    assert "not found or does not belong" in err_msg


def test_04_pre_registration_unauthorized_user_denied(prereg_api_fixture):
    client = TestClient(fastapi_app)
    fastapi_app.dependency_overrides[get_current_user] = lambda: prereg_api_fixture["user_unauthorized_a"]

    payload = {
        "visitor_name": "Unauthorized Visitor",
        "phone": "9876500004",
        "purpose": "Meeting",
    }

    res = client.post("/api/v1/visitors/pre-register", json=payload)
    assert res.status_code == 403


def test_05_pre_registration_duplicate_expected_rejected(prereg_api_fixture, db_session):
    client = TestClient(fastapi_app)
    fastapi_app.dependency_overrides[get_current_user] = lambda: prereg_api_fixture["user_receptionist_a"]

    payload = {
        "visitor_name": "Duplicate Guest",
        "phone": "9876500005",
        "purpose": "Interview",
    }

    res1 = client.post("/api/v1/visitors/pre-register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/visitors/pre-register", json=payload)
    assert res2.status_code == 422
    err_msg = res2.json().get("error", {}).get("message", res2.json().get("detail", str(res2.json())))
    assert "already pre-registered as EXPECTED" in err_msg


# =============================================================================
# QUICK CHECK-IN API TESTS
# =============================================================================

def test_06_successful_quick_check_in(prereg_api_fixture, db_session):
    client = TestClient(fastapi_app)
    fastapi_app.dependency_overrides[get_current_user] = lambda: prereg_api_fixture["user_receptionist_a"]

    # Pre-register first
    vis = Visitor(
        id=uuid.uuid4(),
        school_id=prereg_api_fixture["school_a"].id,
        visitor_name="PreRegistered Arriving",
        phone="9876500006",
        purpose="Scheduled Consultation",
        status=VisitorStatus.EXPECTED,
        pass_number="GP-20260907-0099",
    )
    db_session.add(vis)
    db_session.commit()

    res = client.post(f"/api/v1/visitors/{vis.id}/quick-check-in", json={"remarks": "Arrived at gate 1"})
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "CHECKED_IN"
    assert data["check_in_time"] is not None
    assert data["remarks"] == "Arrived at gate 1"

    # Verify audit event
    audit = db_session.query(AuditLog).filter(AuditLog.action == "VISITOR_QUICK_CHECK_IN").first()
    assert audit is not None
    assert audit.entity_id == str(vis.id)


def test_07_quick_check_in_already_checked_in_rejected(prereg_api_fixture, db_session):
    client = TestClient(fastapi_app)
    fastapi_app.dependency_overrides[get_current_user] = lambda: prereg_api_fixture["user_receptionist_a"]

    vis = Visitor(
        id=uuid.uuid4(),
        school_id=prereg_api_fixture["school_a"].id,
        visitor_name="Already Checked In",
        phone="9876500007",
        purpose="Consultation",
        status=VisitorStatus.CHECKED_IN,
        check_in_time=datetime.now(timezone.utc),
        pass_number="GP-20260907-0100",
    )
    db_session.add(vis)
    db_session.commit()

    res = client.post(f"/api/v1/visitors/{vis.id}/quick-check-in")
    assert res.status_code == 422
    err_msg = res.json().get("error", {}).get("message", res.json().get("detail", str(res.json())))
    assert "already checked in" in err_msg


def test_08_quick_check_in_checked_out_rejected(prereg_api_fixture, db_session):
    client = TestClient(fastapi_app)
    fastapi_app.dependency_overrides[get_current_user] = lambda: prereg_api_fixture["user_receptionist_a"]

    vis = Visitor(
        id=uuid.uuid4(),
        school_id=prereg_api_fixture["school_a"].id,
        visitor_name="Checked Out Guest",
        phone="9876500008",
        purpose="Consultation",
        status=VisitorStatus.CHECKED_OUT,
        check_in_time=datetime.now(timezone.utc),
        check_out_time=datetime.now(timezone.utc),
    )
    db_session.add(vis)
    db_session.commit()

    res = client.post(f"/api/v1/visitors/{vis.id}/quick-check-in")
    assert res.status_code == 422
    err_msg = res.json().get("error", {}).get("message", res.json().get("detail", str(res.json())))
    assert "Status must be EXPECTED" in err_msg


def test_09_quick_check_in_cross_tenant_rejected(prereg_api_fixture, db_session):
    client = TestClient(fastapi_app)
    # User B (School B) tries to check in School A's expected visitor
    fastapi_app.dependency_overrides[get_current_user] = lambda: prereg_api_fixture["user_b"]

    vis = Visitor(
        id=uuid.uuid4(),
        school_id=prereg_api_fixture["school_a"].id,
        visitor_name="School A Expected",
        phone="9876500009",
        purpose="Meeting",
        status=VisitorStatus.EXPECTED,
    )
    db_session.add(vis)
    db_session.commit()

    res = client.post(f"/api/v1/visitors/{vis.id}/quick-check-in")
    assert res.status_code == 404


# =============================================================================
# VISITOR PASS BADGE API TESTS (PII PROTECTION)
# =============================================================================

def test_10_get_visitor_badge_success_and_pii_protection(prereg_api_fixture, db_session):
    client = TestClient(fastapi_app)
    fastapi_app.dependency_overrides[get_current_user] = lambda: prereg_api_fixture["user_receptionist_a"]

    vis = Visitor(
        id=uuid.uuid4(),
        school_id=prereg_api_fixture["school_a"].id,
        visitor_name="Badge Guest",
        phone="9876500010",
        email="badge@example.com",
        id_proof_type=IdProofType.AADHAAR,
        id_proof_number="9999-8888-7777",  # Secret PII!
        purpose="Official Inspection",
        status=VisitorStatus.CHECKED_IN,
        check_in_time=datetime.now(timezone.utc),
        pass_number="GP-20260907-0888",
    )
    db_session.add(vis)
    db_session.commit()

    res = client.get(f"/api/v1/visitors/{vis.id}/badge")
    assert res.status_code == 200
    data = res.json()

    assert data["visitor_name"] == "Badge Guest"
    assert data["pass_number"] == "GP-20260907-0888"
    assert data["purpose"] == "Official Inspection"
    # CRITICAL PII VERIFICATION: id_proof_number MUST NOT exist in badge schema output!
    assert "id_proof_number" not in data


def test_11_get_visitor_badge_cross_tenant_rejected(prereg_api_fixture, db_session):
    client = TestClient(fastapi_app)
    # User B attempts to access School A's visitor badge
    fastapi_app.dependency_overrides[get_current_user] = lambda: prereg_api_fixture["user_b"]

    vis = Visitor(
        id=uuid.uuid4(),
        school_id=prereg_api_fixture["school_a"].id,
        visitor_name="Secret School A Guest",
        phone="9876500011",
        purpose="Secret Meeting",
        status=VisitorStatus.CHECKED_IN,
    )
    db_session.add(vis)
    db_session.commit()

    res = client.get(f"/api/v1/visitors/{vis.id}/badge")
    assert res.status_code == 404
