import uuid
from datetime import date, datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.common.enums import Gender
from app.common.enums.visitor import HostType, ReceptionInquiryStatus, VisitorStatus
from app.database.common_model import CommonModel
from app.dependencies.database import get_db
from app.identity.models.role import IdentityRole
from app.identity.models.user import IdentityUser
from app.identity.security.current_user import get_current_user
from app.main import app as fastapi_app
from app.models.academic_year.academic_year import AcademicYear
from app.models.academic_term.academic_term import AcademicTerm
from app.models.audit_log import AuditLog
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.teacher.teacher import Teacher
from app.models.visitor.reception_inquiry import ReceptionInquiry
from app.models.visitor.visitor import Visitor


@pytest.fixture(autouse=True)
def setup_reception_api_tables(db_session):
    import app.models  # Ensure all mapped models are loaded in SQLAlchemy registry
    CommonModel.metadata.create_all(db_session.get_bind())
    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    yield
    fastapi_app.dependency_overrides.pop(get_db, None)
    fastapi_app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def reception_api_fixture(db_session):
    uid_suffix = uuid.uuid4().hex[:6]

    # School A
    school_a = School(
        id=uuid.uuid4(),
        name=f"Reception API School A {uid_suffix}",
        code=f"RAA-{uid_suffix[:4]}",
        address_line1="100 Front Desk Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    # School B
    school_b = School(
        id=uuid.uuid4(),
        name=f"Reception API School B {uid_suffix}",
        code=f"RAB-{uid_suffix[:4]}",
        address_line1="200 Front Desk Way",
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
        email=f"receptionist.a.{uid_suffix}@school.com",
        username=f"receptionist_a_{uid_suffix}",
        password_hash="hash",
        first_name="Receptionist",
        last_name="A",
        is_active=True,
    )
    user_a.roles.append(role_super_a)

    user_b = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_b.id,
        email=f"receptionist.b.{uid_suffix}@school.com",
        username=f"receptionist_b_{uid_suffix}",
        password_hash="hash",
        first_name="Receptionist",
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
        employee_id=f"EMP-{uid_suffix[:4]}",
        first_name="Alice",
        last_name="Teacher",
        gender=Gender.FEMALE,
        date_of_birth=date(1985, 1, 1),
        email=f"alice.teacher.{uid_suffix}@schoola.com",
        phone=f"98765{uid_suffix[:5]}",
        joining_date=date(2020, 1, 1),
        qualification="M.Ed",
        address_line1="100 School Lane",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )

    # Student host in School A
    academic_year = AcademicYear(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        is_current=True,
    )
    school_class = SchoolClass(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="Class 10",
        display_order=10,
    )
    section = Section(
        id=uuid.uuid4(),
        school_class_id=school_class.id,
        name="A",
    )
    parent_a = Parent(
        id=uuid.uuid4(),
        school_id=school_a.id,
        father_name="Perry Parent",
        primary_phone=f"98764{uid_suffix[:5]}",
        address_line1="100 Parent Rd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([teacher_a, academic_year, school_class, section, parent_a])
    db_session.flush()

    student_a = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        academic_year_id=academic_year.id,
        school_class_id=school_class.id,
        section_id=section.id,
        parent_id=parent_a.id,
        admission_number=f"ADM-{uid_suffix[:4]}",
        roll_number=f"R-{uid_suffix[:4]}",
        first_name="Bob",
        last_name="Student",
        gender=Gender.MALE,
        date_of_birth=date(2010, 5, 15),
        admission_date=date(2026, 6, 1),
        address_line1="100 Student Lane",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(student_a)

    # Visitor in School A
    visitor_a = Visitor(
        id=uuid.uuid4(),
        school_id=school_a.id,
        visitor_name="John Visitor",
        phone=f"99887{uid_suffix[:5]}",
        purpose="General Inquiry",
        status=VisitorStatus.CHECKED_IN,
        check_in_time=datetime.now(timezone.utc),
        pass_number=f"GP-20260907-{uid_suffix[:4]}",
    )

    # Visitor in School B
    visitor_b = Visitor(
        id=uuid.uuid4(),
        school_id=school_b.id,
        visitor_name="Other Tenant Visitor",
        phone=f"99886{uid_suffix[:5]}",
        purpose="Cross Tenant Test",
        status=VisitorStatus.CHECKED_IN,
        check_in_time=datetime.now(timezone.utc),
        pass_number=f"GP-20260907-{uid_suffix[2:6]}",
    )

    db_session.add_all([visitor_a, visitor_b])
    db_session.commit()

    return {
        "school_a": school_a,
        "school_b": school_b,
        "user_a": user_a,
        "user_b": user_b,
        "teacher_a": teacher_a,
        "student_a": student_a,
        "visitor_a": visitor_a,
        "visitor_b": visitor_b,
    }


def test_create_inquiry_success(db_session, reception_api_fixture):
    user_a = reception_api_fixture["user_a"]
    teacher_a = reception_api_fixture["teacher_a"]
    visitor_a = reception_api_fixture["visitor_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a

    client = TestClient(fastapi_app)
    payload = {
        "contact_name": "Mary Parent",
        "contact_phone": "9123456789",
        "contact_email": "mary@example.com",
        "subject": "Admission Discussion",
        "details": "Inquiring about Grade 11 science stream availability.",
        "visitor_id": str(visitor_a.id),
        "host_type": HostType.TEACHER.value,
        "host_id": str(teacher_a.id),
        "appointment_time": "2026-09-10T10:30:00Z",
        "notes": "Scheduled meeting with Vice Principal.",
    }

    res = client.post("/api/v1/reception/inquiries", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["contact_name"] == "Mary Parent"
    assert data["contact_phone"] == "9123456789"
    assert data["subject"] == "Admission Discussion"
    assert data["status"] == ReceptionInquiryStatus.PENDING.value
    assert data["visitor_id"] == str(visitor_a.id)
    assert data["host_type"] == HostType.TEACHER.value
    assert data["host_id"] == str(teacher_a.id)
    assert data["school_id"] == str(user_a.school_id)

    # Verify Audit Log
    audit = db_session.query(AuditLog).filter_by(entity_id=data["id"]).first()
    assert audit is not None
    assert audit.action == "RECEPTION_INQUIRY_CREATED"
    assert audit.school_id == user_a.school_id


def test_create_inquiry_ignores_client_school_id(reception_api_fixture):
    user_a = reception_api_fixture["user_a"]
    school_b = reception_api_fixture["school_b"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a

    client = TestClient(fastapi_app)
    payload = {
        "contact_name": "Tamper Test",
        "contact_phone": "9876543210",
        "subject": "Tenant Tamper Attempt",
        "school_id": str(school_b.id),
    }

    res = client.post("/api/v1/reception/inquiries", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["school_id"] == str(user_a.school_id)
    assert data["school_id"] != str(school_b.id)


def test_create_inquiry_initial_status_rejection(reception_api_fixture):
    user_a = reception_api_fixture["user_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a

    client = TestClient(fastapi_app)
    payload = {
        "contact_name": "Direct Resolve Test",
        "contact_phone": "9876543210",
        "subject": "Initial Status Check",
        "status": ReceptionInquiryStatus.RESOLVED.value,
    }

    res = client.post("/api/v1/reception/inquiries", json=payload)
    assert res.status_code == 422
    assert "Newly created inquiry cannot be assigned initial status" in res.json()["error"]["message"]


def test_create_inquiry_cross_tenant_visitor_rejection(reception_api_fixture):
    user_a = reception_api_fixture["user_a"]
    visitor_b = reception_api_fixture["visitor_b"]  # Belongs to School B
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a

    client = TestClient(fastapi_app)
    payload = {
        "contact_name": "Cross Tenant Visitor",
        "contact_phone": "9876543210",
        "subject": "Cross Tenant Link",
        "visitor_id": str(visitor_b.id),
    }

    res = client.post("/api/v1/reception/inquiries", json=payload)
    assert res.status_code == 422
    assert "Referenced visitor not found or does not belong to your school" in res.json()["error"]["message"]


def test_create_inquiry_invalid_host_rejection(reception_api_fixture):
    user_a = reception_api_fixture["user_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a

    client = TestClient(fastapi_app)
    payload = {
        "contact_name": "Invalid Host Test",
        "contact_phone": "9876543210",
        "subject": "Invalid Host ID",
        "host_type": HostType.TEACHER.value,
        "host_id": str(uuid.uuid4()),
    }

    res = client.post("/api/v1/reception/inquiries", json=payload)
    assert res.status_code == 422
    assert "Referenced teacher host not found" in res.json()["error"]["message"]


def test_get_inquiry_details_success(db_session, reception_api_fixture):
    user_a = reception_api_fixture["user_a"]
    inquiry = ReceptionInquiry(
        id=uuid.uuid4(),
        school_id=user_a.school_id,
        contact_name="Get Detail Test",
        contact_phone="9998887776",
        subject="Fee Receipt Request",
        status=ReceptionInquiryStatus.PENDING,
    )
    db_session.add(inquiry)
    db_session.commit()

    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a
    client = TestClient(fastapi_app)

    res = client.get(f"/api/v1/reception/inquiries/{inquiry.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == str(inquiry.id)
    assert data["contact_name"] == "Get Detail Test"


def test_get_inquiry_cross_tenant_denial(db_session, reception_api_fixture):
    user_a = reception_api_fixture["user_a"]
    school_b = reception_api_fixture["school_b"]
    inquiry_b = ReceptionInquiry(
        id=uuid.uuid4(),
        school_id=school_b.id,
        contact_name="School B Inquiry",
        contact_phone="9998887776",
        subject="Private B Data",
        status=ReceptionInquiryStatus.PENDING,
    )
    db_session.add(inquiry_b)
    db_session.commit()

    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a
    client = TestClient(fastapi_app)

    res = client.get(f"/api/v1/reception/inquiries/{inquiry_b.id}")
    assert res.status_code == 404


def test_list_inquiries_filtering_and_tenant_isolation(db_session, reception_api_fixture):
    user_a = reception_api_fixture["user_a"]
    school_b = reception_api_fixture["school_b"]

    inquiry_a1 = ReceptionInquiry(
        id=uuid.uuid4(),
        school_id=user_a.school_id,
        contact_name="Alice Smith",
        contact_phone="9111111111",
        subject="Sports Day Inquiry",
        status=ReceptionInquiryStatus.PENDING,
    )
    inquiry_a2 = ReceptionInquiry(
        id=uuid.uuid4(),
        school_id=user_a.school_id,
        contact_name="Bob Jones",
        contact_phone="9222222222",
        subject="TC Inquiry",
        status=ReceptionInquiryStatus.RESOLVED,
    )
    inquiry_b = ReceptionInquiry(
        id=uuid.uuid4(),
        school_id=school_b.id,
        contact_name="Charlie Brown",
        contact_phone="9333333333",
        subject="School B Event",
        status=ReceptionInquiryStatus.PENDING,
    )
    db_session.add_all([inquiry_a1, inquiry_a2, inquiry_b])
    db_session.commit()

    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a
    client = TestClient(fastapi_app)

    # 1. List all for School A
    res = client.get("/api/v1/reception/inquiries")
    assert res.status_code == 200
    data = res.json()
    ids = [item["id"] for item in data["items"]]
    assert str(inquiry_a1.id) in ids
    assert str(inquiry_a2.id) in ids
    assert str(inquiry_b.id) not in ids

    # 2. Filter by status
    res_status = client.get("/api/v1/reception/inquiries?status=RESOLVED")
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert data_status["total"] == 1
    assert data_status["items"][0]["id"] == str(inquiry_a2.id)

    # 3. Search filter
    res_search = client.get("/api/v1/reception/inquiries?search=Sports")
    assert res_search.status_code == 200
    data_search = res_search.json()
    assert data_search["total"] == 1
    assert data_search["items"][0]["id"] == str(inquiry_a1.id)


def test_update_inquiry_status_state_machine(db_session, reception_api_fixture):
    user_a = reception_api_fixture["user_a"]
    inquiry = ReceptionInquiry(
        id=uuid.uuid4(),
        school_id=user_a.school_id,
        contact_name="State Machine Test",
        contact_phone="9876543210",
        subject="Status Transition Flow",
        status=ReceptionInquiryStatus.PENDING,
    )
    db_session.add(inquiry)
    db_session.commit()

    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a
    client = TestClient(fastapi_app)

    # 1. PENDING -> IN_PROGRESS
    res1 = client.patch(
        f"/api/v1/reception/inquiries/{inquiry.id}",
        json={"status": ReceptionInquiryStatus.IN_PROGRESS.value},
    )
    assert res1.status_code == 200
    assert res1.json()["status"] == ReceptionInquiryStatus.IN_PROGRESS.value

    # 2. IN_PROGRESS -> RESOLVED
    res2 = client.patch(
        f"/api/v1/reception/inquiries/{inquiry.id}",
        json={"status": ReceptionInquiryStatus.RESOLVED.value, "notes": "Resolved successfully."},
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == ReceptionInquiryStatus.RESOLVED.value
    assert res2.json()["notes"] == "Resolved successfully."

    # 3. Invalid Transition: RESOLVED -> IN_PROGRESS (Must fail)
    res3 = client.patch(
        f"/api/v1/reception/inquiries/{inquiry.id}",
        json={"status": ReceptionInquiryStatus.IN_PROGRESS.value},
    )
    assert res3.status_code == 422
    assert "Cannot modify status of an already RESOLVED inquiry" in res3.json()["error"]["message"]


def test_update_inquiry_cancelled_state_rejection(db_session, reception_api_fixture):
    user_a = reception_api_fixture["user_a"]
    inquiry = ReceptionInquiry(
        id=uuid.uuid4(),
        school_id=user_a.school_id,
        contact_name="Cancellation Test",
        contact_phone="9876543210",
        subject="Cancellation Flow",
        status=ReceptionInquiryStatus.CANCELLED,
    )
    db_session.add(inquiry)
    db_session.commit()

    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a
    client = TestClient(fastapi_app)

    # CANCELLED -> IN_PROGRESS must be rejected
    res = client.patch(
        f"/api/v1/reception/inquiries/{inquiry.id}",
        json={"status": ReceptionInquiryStatus.IN_PROGRESS.value},
    )
    assert res.status_code == 422
    assert "Cannot modify status of a CANCELLED inquiry" in res.json()["error"]["message"]


def test_update_inquiry_audit_log(db_session, reception_api_fixture):
    user_a = reception_api_fixture["user_a"]
    inquiry = ReceptionInquiry(
        id=uuid.uuid4(),
        school_id=user_a.school_id,
        contact_name="Audit Log Test",
        contact_phone="9876543210",
        subject="Audit Check",
        status=ReceptionInquiryStatus.PENDING,
    )
    db_session.add(inquiry)
    db_session.commit()

    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a
    client = TestClient(fastapi_app)

    res = client.patch(
        f"/api/v1/reception/inquiries/{inquiry.id}",
        json={"notes": "Updated notes for audit test."},
    )
    assert res.status_code == 200

    # Verify Audit Log
    audit = db_session.query(AuditLog).filter_by(entity_id=str(inquiry.id)).order_by(AuditLog.created_at.desc()).first()
    assert audit is not None
    assert audit.action in ("RECEPTION_INQUIRY_UPDATED", "RECEPTION_INQUIRY_STATUS_CHANGED")
    assert audit.school_id == user_a.school_id
