"""
Unit & Integration Tests for Executive Reports & BI Analytics Center — Phase 30.2
"""
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from app.common.enums.fees import FeeCategory, FeeStructureStatus, PaymentMode
from app.common.enums.parent import ParentRelationship
from app.common.enums.student import Gender
from app.identity.models import (
    IdentityRole,
    IdentityRolePermission,
    IdentityUser,
    IdentityUserRole,
)
from app.identity.repositories import permission_repository
from app.identity.security.jwt_manager import jwt_manager
from app.identity.security.password import hash_password
from app.identity.seeders import seed_identity
from app.models.academic_term.academic_term import AcademicTerm
from app.models.academic_year.academic_year import AcademicYear
from app.common.enums.admissions import AdmissionApplicationStatus
from app.models.admissions.admission_application import AdmissionApplication
from app.models.admissions.admission_cycle import AdmissionCycle
from app.models.attendance.attendance import Attendance, AttendanceStatus
from app.models.fees.fee_payment import FeePayment
from app.models.fees.fee_structure import FeeItem, FeeStructure
from app.models.fees.student_fee_assignment import StudentFeeAssignment, StudentFeeItem
from app.models.grading.report_card import ReportCard, ReportCardStatus
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student, StudentStatus


def create_test_school_user(db: Session, school_name: str, school_code: str, permissions: list[str]):
    seed_identity(db)

    school = School(
        id=uuid.uuid4(),
        name=school_name,
        code=school_code,
        address_line1="100 Report Way",
        city="Analytics City",
        district="Central",
        state="State",
        country="India",
        postal_code="110001",
    )
    db.add(school)
    db.commit()

    role = IdentityRole(
        id=uuid.uuid4(),
        school_id=school.id,
        name=f"Role_{uuid.uuid4().hex[:6]}",
        description="Executive Report Test Role",
        is_system=False,
    )
    db.add(role)
    db.commit()

    for perm_name in permissions:
        perm = permission_repository.get_by_name(db, perm_name)
        if perm:
            rp = IdentityRolePermission(
                role_id=role.id,
                permission_id=perm.id,
            )
            db.add(rp)
    db.commit()

    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        email=f"user_{uuid.uuid4().hex[:6]}@school.com",
        password_hash=hash_password("Password123!"),
        first_name="Admin",
        last_name="User",
        is_active=True,
    )
    db.add(user)
    db.commit()

    ur = IdentityUserRole(
        user_id=user.id,
        role_id=role.id,
    )
    db.add(ur)
    db.commit()

    token = jwt_manager.create_access_token(
        user_id=user.id,
        school_id=school.id,
    )
    headers = {"Authorization": f"Bearer {token}"}
    return school, user, headers


def create_test_student(
    db: Session,
    school_id: uuid.UUID,
    first_name: str = "Test",
    last_name: str = "Student",
    class_name: str = "Class 10A",
    gender: Gender = Gender.MALE,
    academic_year: AcademicYear | None = None,
    school_class: SchoolClass | None = None,
):
    if not academic_year:
        academic_year = AcademicYear(
            id=uuid.uuid4(),
            school_id=school_id,
            name=f"AY-{uuid.uuid4().hex[:4]}",
            start_date=date(2026, 6, 1),
            end_date=date(2027, 5, 31),
        )
        db.add(academic_year)
        db.commit()

    if not school_class:
        school_class = SchoolClass(
            id=uuid.uuid4(),
            school_id=school_id,
            name=class_name,
            display_order=1,
        )
        db.add(school_class)
        db.commit()

    section = Section(
        id=uuid.uuid4(),
        school_class_id=school_class.id,
        name=f"Sec-{uuid.uuid4().hex[:3]}",
    )
    db.add(section)
    db.commit()

    parent = Parent(
        id=uuid.uuid4(),
        school_id=school_id,
        father_name="Father Name",
        relationship=ParentRelationship.FATHER,
        primary_phone=f"9{uuid.uuid4().int % 1000000000:09d}",
        address_line1="100 Report Way",
        city="Analytics City",
        district="Central",
        state="State",
        postal_code="110001",
    )
    db.add(parent)
    db.commit()

    student = Student(
        id=uuid.uuid4(),
        school_id=school_id,
        parent_id=parent.id,
        academic_year_id=academic_year.id,
        school_class_id=school_class.id,
        section_id=section.id,
        admission_number=f"ADM-{uuid.uuid4().hex[:6].upper()}",
        roll_number=f"{uuid.uuid4().int % 1000:03d}",
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        date_of_birth=date(2012, 1, 1),
        admission_date=date(2026, 6, 1),
        status=StudentStatus.ACTIVE,
        address_line1="100 Report Way",
        city="Analytics City",
        district="Central",
        state="State",
        postal_code="110001",
    )
    db.add(student)
    db.commit()

    return student, academic_year, school_class, section


def test_reports_authorization(client: TestClient, db_session: Session):
    # User with reports.view and reports.export
    school, user, auth_headers = create_test_school_user(
        db_session, "Auth School", f"AUTH_{uuid.uuid4().hex[:4]}", ["reports.view", "reports.export"]
    )
    # User without reports.view (only student.view)
    school2, user2, unauth_headers = create_test_school_user(
        db_session, "Unauth School", f"UNAUTH_{uuid.uuid4().hex[:4]}", ["student.view"]
    )

    # 1. Authorized access
    res = client.get("/api/v1/reports/executive-summary", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["success"] is True

    res = client.get("/api/v1/reports/students", headers=auth_headers)
    assert res.status_code == 200

    res = client.get("/api/v1/reports/attendance", headers=auth_headers)
    assert res.status_code == 200

    res = client.get("/api/v1/reports/finance", headers=auth_headers)
    assert res.status_code == 200

    res = client.get("/api/v1/reports/admissions", headers=auth_headers)
    assert res.status_code == 200

    res = client.get("/api/v1/reports/academic", headers=auth_headers)
    assert res.status_code == 200

    res = client.get("/api/v1/reports/operations", headers=auth_headers)
    assert res.status_code == 200

    # 2. Unauthorized access (missing reports.view)
    res_unauth = client.get("/api/v1/reports/executive-summary", headers=unauth_headers)
    assert res_unauth.status_code == 403

    res_unauth = client.get("/api/v1/reports/finance", headers=unauth_headers)
    assert res_unauth.status_code == 403

    # 3. Unauthenticated access
    res_anon = client.get("/api/v1/reports/executive-summary")
    assert res_anon.status_code == 401


def test_reports_tenant_isolation(client: TestClient, db_session: Session):
    # Create School A and School B
    school_a, user_a, headers_a = create_test_school_user(
        db_session, "School Alpha", f"ALPH_{uuid.uuid4().hex[:4]}", ["reports.view", "reports.export"]
    )
    school_b, user_b, headers_b = create_test_school_user(
        db_session, "School Beta", f"BETA_{uuid.uuid4().hex[:4]}", ["reports.view", "reports.export"]
    )

    # Add Class & Students to School A
    st_a1, ay_a, cls_a, _ = create_test_student(
        db_session, school_a.id, first_name="Alice", last_name="Alpha", class_name="Class 10A", gender=Gender.FEMALE
    )
    st_a2, _, _, _ = create_test_student(
        db_session, school_a.id, first_name="Aaron", last_name="Alpha", class_name="Class 10A", gender=Gender.MALE, academic_year=ay_a, school_class=cls_a
    )

    # Add Class & Students to School B
    st_b1, ay_b, cls_b, _ = create_test_student(
        db_session, school_b.id, first_name="Bob", last_name="Beta", class_name="Class 10B", gender=Gender.MALE
    )

    # Query School A reports
    res_a = client.get("/api/v1/reports/executive-summary", headers=headers_a)
    assert res_a.status_code == 200
    data_a = res_a.json()["data"]
    assert data_a["active_students"] == 2
    assert data_a["school_name"] == "School Alpha"

    # Query School B reports
    res_b = client.get("/api/v1/reports/executive-summary", headers=headers_b)
    assert res_b.status_code == 200
    data_b = res_b.json()["data"]
    assert data_b["active_students"] == 1
    assert data_b["school_name"] == "School Beta"

    # Verify CSV export isolation
    csv_a = client.get("/api/v1/reports/export/csv?category=students", headers=headers_a)
    assert csv_a.status_code == 200
    assert "Class 10A" in csv_a.text
    assert "Class 10B" not in csv_a.text


def test_reports_financial_integrity(client: TestClient, db_session: Session):
    school, user, headers = create_test_school_user(
        db_session, "Finance School", f"FIN_{uuid.uuid4().hex[:4]}", ["reports.view", "reports.export"]
    )

    st, ay, cls, sec = create_test_student(
        db_session, school.id, first_name="Frank", last_name="Finance"
    )

    # Fee Structure
    fs = FeeStructure(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        name="Standard Annual Fee",
        status=FeeStructureStatus.ACTIVE,
    )
    db_session.add(fs)
    db_session.commit()

    fi1 = FeeItem(
        id=uuid.uuid4(),
        fee_structure_id=fs.id,
        category=FeeCategory.TUITION,
        name="Tuition Fee",
        amount=Decimal("5000.00"),
        is_optional=False,
    )
    fi2 = FeeItem(
        id=uuid.uuid4(),
        fee_structure_id=fs.id,
        category=FeeCategory.TRANSPORTATION,
        name="Bus Fee",
        amount=Decimal("2000.00"),
        is_optional=False,
    )
    db_session.add_all([fi1, fi2])
    db_session.commit()

    # Fee Assignment
    assignment = StudentFeeAssignment(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        student_id=st.id,
        fee_structure_id=fs.id,
    )
    db_session.add(assignment)
    db_session.commit()

    sfi1 = StudentFeeItem(
        id=uuid.uuid4(),
        student_fee_assignment_id=assignment.id,
        fee_item_id=fi1.id,
        category=FeeCategory.TUITION,
        name="Tuition Fee",
        amount=Decimal("5000.00"),
        is_applicable=True,
    )
    sfi2 = StudentFeeItem(
        id=uuid.uuid4(),
        student_fee_assignment_id=assignment.id,
        fee_item_id=fi2.id,
        category=FeeCategory.TRANSPORTATION,
        name="Bus Fee",
        amount=Decimal("2000.00"),
        is_applicable=True,
    )
    db_session.add_all([sfi1, sfi2])
    db_session.commit()

    # Payment: 4000.00 via CARD
    payment = FeePayment(
        id=uuid.uuid4(),
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        receipt_number=f"REC-{uuid.uuid4().hex[:6].upper()}",
        amount=Decimal("4000.00"),
        payment_date=date.today(),
        payment_mode=PaymentMode.CARD,
    )
    db_session.add(payment)
    db_session.commit()

    # Verify finance report numbers
    res = client.get("/api/v1/reports/finance", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]

    # Total Assigned = 5000 + 2000 = 7000.00
    assert data["total_fees_assigned"] == 7000.00
    # Total Collected = 4000.00
    assert data["total_fees_collected"] == 4000.00
    # Total Outstanding = 7000 - 4000 = 3000.00
    assert data["total_fees_outstanding"] == 3000.00
    # Collection rate = (4000 / 7000) * 100 = 57.14%
    assert 57.0 <= data["collection_rate_pct"] <= 58.0

    # Payment method breakdown
    assert len(data["payment_methods_breakdown"]) == 1
    assert data["payment_methods_breakdown"][0]["method"] == "CARD"
    assert data["payment_methods_breakdown"][0]["total_amount"] == 4000.00


def test_reports_filtering_and_empty_states(client: TestClient, db_session: Session):
    school, user, headers = create_test_school_user(
        db_session, "Filter School", f"FILT_{uuid.uuid4().hex[:4]}", ["reports.view", "reports.export"]
    )

    # Empty school state should return gracefully
    res = client.get("/api/v1/reports/executive-summary", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["active_students"] == 0
    assert data["total_fees_assigned"] == 0.0
    assert data["total_fees_collected"] == 0.0
    assert data["overall_attendance_pct"] == 0.0

    # Attendance report empty state
    res_att = client.get("/api/v1/reports/attendance", headers=headers)
    assert res_att.status_code == 200
    assert res_att.json()["data"]["overall_attendance_pct"] == 0.0
    assert res_att.json()["data"]["chronic_absentee_count"] == 0

    # CSV export empty state
    res_csv = client.get("/api/v1/reports/export/csv?category=attendance", headers=headers)
    assert res_csv.status_code == 200
    assert "class_name" in res_csv.text
