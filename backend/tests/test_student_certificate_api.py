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
from app.models.student.student_certificate import StudentCertificate, CertificateType
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.password import hash_password
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity


@pytest.fixture
def setup_certificate_data(db_session: Session):
    seed_identity(db_session)
    suffix = uuid.uuid4().hex[:6]

    # Create School A & B
    school_a = School(name=f"Cert School A {suffix}", code=f"CSA_{suffix}", address_line1="123 Campus St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001")
    school_b = School(name=f"Cert School B {suffix}", code=f"CSB_{suffix}", address_line1="456 Campus St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001")
    db_session.add_all([school_a, school_b])
    db_session.commit()

    # Academic Year
    ay_a = AcademicYear(school_id=school_a.id, name=f"2026-2027_{suffix}", start_date=date(2026, 6, 1), end_date=date(2027, 4, 30), status=AcademicYearStatus.ACTIVE)
    ay_b = AcademicYear(school_id=school_b.id, name=f"2026-2027_{suffix}", start_date=date(2026, 6, 1), end_date=date(2027, 4, 30), status=AcademicYearStatus.ACTIVE)
    db_session.add_all([ay_a, ay_b])
    db_session.commit()

    # Class & Section
    class_a = SchoolClass(school_id=school_a.id, name=f"Class 10_{suffix}", display_order=1)
    class_b = SchoolClass(school_id=school_b.id, name=f"Class 10_{suffix}", display_order=1)
    db_session.add_all([class_a, class_b])
    db_session.commit()

    sec_a = Section(school_class_id=class_a.id, name="A")
    sec_b = Section(school_class_id=class_b.id, name="A")
    db_session.add_all([sec_a, sec_b])
    db_session.commit()

    # Parent
    parent_a = Parent(school_id=school_a.id, father_name="ParentA User", primary_phone=f"9100{suffix[:6]}", email=f"parenta_{suffix}@school.edu", address_line1="123 St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001")
    parent_b = Parent(school_id=school_b.id, father_name="ParentB User", primary_phone=f"9101{suffix[:6]}", email=f"parentb_{suffix}@school.edu", address_line1="456 St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001")
    db_session.add_all([parent_a, parent_b])
    db_session.commit()

    # Student A & B
    student_a = Student(
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        school_class_id=class_a.id,
        section_id=sec_a.id,
        parent_id=parent_a.id,
        admission_number=f"ADM_CA_{suffix}",
        roll_number="1",
        first_name="Daniel",
        last_name="Student",
        gender=Gender.MALE,
        date_of_birth=date(2010, 5, 15),
        admission_date=date(2020, 6, 1),
        status=StudentStatus.ACTIVE,
        address_line1="123 Campus St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    student_b = Student(
        school_id=school_b.id,
        academic_year_id=ay_b.id,
        school_class_id=class_b.id,
        section_id=sec_b.id,
        parent_id=parent_b.id,
        admission_number=f"ADM_CB_{suffix}",
        roll_number="1",
        first_name="Eva",
        last_name="Student",
        gender=Gender.FEMALE,
        date_of_birth=date(2010, 8, 20),
        admission_date=date(2020, 6, 1),
        status=StudentStatus.ACTIVE,
        address_line1="456 Campus St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([student_a, student_b])
    db_session.commit()

    admin_role = db_session.query(IdentityRole).filter_by(name="School Admin").first()

    # User Admin School A
    admin_a = IdentityUser(
        school_id=school_a.id,
        email=f"admin_ca_{suffix}@school.edu",
        password_hash=hash_password("AdminPass123!"),
        first_name="Admin",
        last_name="A",
        is_active=True,
        status="ACTIVE",
    )
    db_session.add(admin_a)
    db_session.commit()
    db_session.add(IdentityUserRole(user_id=admin_a.id, role_id=admin_role.id))

    # User Admin School B
    admin_b = IdentityUser(
        school_id=school_b.id,
        email=f"admin_cb_{suffix}@school.edu",
        password_hash=hash_password("AdminPass123!"),
        first_name="Admin",
        last_name="B",
        is_active=True,
        status="ACTIVE",
    )
    db_session.add(admin_b)
    db_session.commit()
    db_session.add(IdentityUserRole(user_id=admin_b.id, role_id=admin_role.id))

    db_session.commit()

    token_a = jwt_manager.create_access_token(user_id=admin_a.id, school_id=school_a.id)
    token_b = jwt_manager.create_access_token(user_id=admin_b.id, school_id=school_b.id)

    return {
        "school_a": school_a,
        "school_b": school_b,
        "student_a": student_a,
        "student_b": student_b,
        "token_a": token_a,
        "token_b": token_b,
    }


def test_01_issue_transfer_certificate(client: TestClient, setup_certificate_data):
    data = setup_certificate_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    student_id = str(data["student_a"].id)
    payload = {
        "reason_for_leaving": "Parent transferred to another city",
        "conduct": "Exemplary",
        "update_student_status": True,
    }

    res = client.post(f"/api/v1/students/{student_id}/certificates/tc", json=payload, headers=headers)
    assert res.status_code == 201
    cert_data = res.json()["data"]
    assert cert_data["certificate_type"] == "TC"
    assert cert_data["certificate_number"].startswith("TC-")
    assert cert_data["student_name"] == "Daniel Student"

    # Verify student status updated
    res_st = client.get(f"/api/v1/students/{student_id}", headers=headers)
    assert res_st.status_code == 200
    assert res_st.json()["data"]["status"] == "TRANSFERRED"


def test_02_issue_bonafide_certificate(client: TestClient, setup_certificate_data):
    data = setup_certificate_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    student_id = str(data["student_a"].id)
    payload = {
        "purpose": "Passport Application",
        "conduct": "Good",
    }

    res = client.post(f"/api/v1/students/{student_id}/certificates/bonafide", json=payload, headers=headers)
    assert res.status_code == 201
    cert_data = res.json()["data"]
    assert cert_data["certificate_type"] == "BONAFIDE"
    assert cert_data["certificate_number"].startswith("BC-")
    assert cert_data["purpose"] == "Passport Application"


def test_03_get_certificate_print_view(client: TestClient, setup_certificate_data):
    data = setup_certificate_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    student_id = str(data["student_a"].id)
    payload = {"purpose": "Bank Account", "conduct": "Good"}
    res_create = client.post(f"/api/v1/students/{student_id}/certificates/bonafide", json=payload, headers=headers)
    cert_id = res_create.json()["data"]["id"]

    # Request print view HTML
    res_print = client.get(f"/api/v1/certificates/{cert_id}/print", headers=headers)
    assert res_print.status_code == 200
    assert "text/html" in res_print.headers["content-type"]
    assert "BONAFIDE CERTIFICATE" in res_print.text
    assert "Daniel Student" in res_print.text


def test_04_certificate_tenant_isolation(client: TestClient, setup_certificate_data):
    data = setup_certificate_data
    headers_b = {"Authorization": f"Bearer {data['token_b']}"}

    student_a_id = str(data["student_a"].id)
    payload = {"purpose": "Unauthorized Test", "conduct": "Good"}

    # School B admin attempting to issue certificate for School A student -> 404/403
    res_cross = client.post(f"/api/v1/students/{student_a_id}/certificates/bonafide", json=payload, headers=headers_b)
    assert res_cross.status_code in (403, 404)
