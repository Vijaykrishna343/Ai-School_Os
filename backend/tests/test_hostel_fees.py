import uuid
from datetime import date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.school.school import School
from app.models.parent.parent import Parent
from app.models.student.student import Student
from app.models.academic_year.academic_year import AcademicYear
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.fees.student_fee_assignment import StudentFeeAssignment, StudentFeeItem
from app.models.fees.fee_payment import FeePayment
from app.models.hostel.hostel_fee import HostelFeeAllocation, HostelFeeStructure
from app.common.enums import Gender
from app.common.enums.fees import FeeCategory, StudentFeeAssignmentStatus
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity


def setup_hostel_fee_environment(db_session: Session):
    seed_identity(db_session)

    school = School(
        name="Hostel Fee School",
        code=f"HFS-{uuid.uuid4().hex[:4]}",
        address_line1="123 Academic Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(school)
    db_session.commit()

    admin_role = db_session.query(IdentityRole).filter_by(name="School Admin", school_id=None).first()
    admin_user = IdentityUser(
        school_id=school.id,
        email=f"hostel_admin_{uuid.uuid4().hex[:4]}@school.com",
        password_hash="hash",
        first_name="Hostel",
        last_name="Admin",
        is_active=True,
        status="ACTIVE",
    )
    db_session.add(admin_user)
    db_session.commit()

    db_session.add(IdentityUserRole(user_id=admin_user.id, role_id=admin_role.id))
    db_session.commit()

    headers = {"Authorization": f"Bearer {jwt_manager.create_access_token(admin_user.id, school.id)}"}

    ay = AcademicYear(school_id=school.id, name="2025-2026", start_date=date(2025, 4, 1), end_date=date(2026, 3, 31))
    sc = SchoolClass(school_id=school.id, name="Class 10", display_order=1)
    db_session.add_all([ay, sc])
    db_session.commit()

    sec = Section(school_class_id=sc.id, name="Sec A")
    unique_num = f"{uuid.uuid4().int % 10000000:07d}"
    parent = Parent(
        school_id=school.id,
        father_name="Papa",
        mother_name="Mama",
        primary_phone=f"99{unique_num}",
        address_line1="123 St",
        city="Hyd",
        district="Hyd",
        state="TS",
        postal_code="500001",
    )
    db_session.add_all([sec, parent])
    db_session.commit()

    student = Student(
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=sc.id,
        section_id=sec.id,
        parent_id=parent.id,
        admission_number=f"ADM-{uuid.uuid4().hex[:4]}",
        roll_number="104",
        first_name="Fee",
        last_name="Student",
        gender=Gender.MALE,
        date_of_birth=date(2010, 1, 1),
        admission_date=date(2025, 4, 1),
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(student)
    db_session.commit()

    return {
        "school": school,
        "admin_user": admin_user,
        "headers": headers,
        "ay": ay,
        "sc": sc,
        "sec": sec,
        "parent": parent,
        "student": student,
    }


def test_hostel_fee_structure_and_central_payment_integration(client: TestClient, db_session: Session):
    env = setup_hostel_fee_environment(db_session)
    headers = env["headers"]
    ay = env["ay"]
    student = env["student"]
    school = env["school"]

    # 1. Create Hostel Fee Structure
    res_fs = client.post(
        "/api/v1/hostel/fees/structures",
        json={
            "academic_year_id": str(ay.id),
            "name": "Annual Mess & Boarding Fee",
            "amount": 25000.00,
            "description": "Boarding and food expenses",
        },
        headers=headers,
    )
    assert res_fs.status_code == 201
    fs_id = res_fs.json()["data"]["id"]

    # 2. Allocate Fee to Student -> Automatically registers on Central Fee Assignment
    res_alloc = client.post(
        "/api/v1/hostel/fees/allocations",
        json={
            "student_id": str(student.id),
            "fee_structure_id": fs_id,
            "due_date": "2025-09-30",
        },
        headers=headers,
    )
    assert res_alloc.status_code == 201
    fee_alloc_id = res_alloc.json()["data"]["id"]

    # Verify central student fee assignment was created and has the hostel line item
    assignment = db_session.execute(
        select(StudentFeeAssignment).where(
            StudentFeeAssignment.school_id == school.id,
            StudentFeeAssignment.academic_year_id == ay.id,
            StudentFeeAssignment.student_id == student.id,
            StudentFeeAssignment.is_deleted.is_(False),
        )
    ).scalar_one_or_none()
    assert assignment is not None
    assert assignment.status == StudentFeeAssignmentStatus.PENDING

    # Verify line items contain the hostel charge under FeeCategory.OTHER
    hostel_item = next((item for item in assignment.student_fee_items if "Hostel:" in item.name and not item.is_deleted), None)
    assert hostel_item is not None
    assert hostel_item.category == FeeCategory.OTHER
    assert hostel_item.amount == Decimal("25000.00")

    # 3. Pay Hostel Fee Allocation (Partial Payment)
    res_pay_partial = client.put(
        f"/api/v1/hostel/fees/allocations/{fee_alloc_id}/pay",
        json={"payment_amount": 10000.00, "payment_mode": "CASH", "remarks": "First installment"},
        headers=headers,
    )
    assert res_pay_partial.status_code == 200
    assert res_pay_partial.json()["data"]["status"] == "PARTIAL"
    assert res_pay_partial.json()["data"]["paid_amount"] == 10000.00

    # Verify central FeePayment record exists
    payments = db_session.execute(
        select(FeePayment).where(
            FeePayment.school_id == school.id,
            FeePayment.student_fee_assignment_id == assignment.id,
            FeePayment.is_deleted.is_(False),
        )
    ).scalars().all()
    assert len(payments) == 1
    assert payments[0].amount == Decimal("10000.00")
    assert payments[0].receipt_number.startswith("REC-")

    # 4. Complete Remaining Payment
    res_pay_final = client.put(
        f"/api/v1/hostel/fees/allocations/{fee_alloc_id}/pay",
        json={"payment_amount": 15000.00, "payment_mode": "UPI", "reference_number": "UPI-123456789"},
        headers=headers,
    )
    assert res_pay_final.status_code == 200
    assert res_pay_final.json()["data"]["status"] == "PAID"
    assert res_pay_final.json()["data"]["paid_amount"] == 25000.00

    # Verify central assignment status updated to PAID
    db_session.refresh(assignment)
    assert assignment.status == StudentFeeAssignmentStatus.PAID


def test_hostel_fee_duplicate_allocation_protection(client: TestClient, db_session: Session):
    env = setup_hostel_fee_environment(db_session)
    headers = env["headers"]
    ay = env["ay"]
    student = env["student"]

    res_fs = client.post(
        "/api/v1/hostel/fees/structures",
        json={
            "academic_year_id": str(ay.id),
            "name": "Hostel Amenities Fee",
            "amount": 12000.00,
        },
        headers=headers,
    )
    fs_id = res_fs.json()["data"]["id"]

    # First allocation
    res1 = client.post(
        "/api/v1/hostel/fees/allocations",
        json={
            "student_id": str(student.id),
            "fee_structure_id": fs_id,
            "due_date": "2025-10-01",
        },
        headers=headers,
    )
    assert res1.status_code == 201

    # Second allocation attempt of same structure to same student -> Rejected (Duplicate)
    res2 = client.post(
        "/api/v1/hostel/fees/allocations",
        json={
            "student_id": str(student.id),
            "fee_structure_id": fs_id,
            "due_date": "2025-10-01",
        },
        headers=headers,
    )
    assert res2.status_code in [400, 409]


def test_hostel_fee_academic_year_integrity(client: TestClient, db_session: Session):
    env = setup_hostel_fee_environment(db_session)
    headers = env["headers"]
    school = env["school"]
    student = env["student"]

    # Create different academic year
    other_ay = AcademicYear(
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
    )
    db_session.add(other_ay)
    db_session.commit()

    # Create structure in 2026-2027
    res_fs = client.post(
        "/api/v1/hostel/fees/structures",
        json={
            "academic_year_id": str(other_ay.id),
            "name": "Next Year Hostel Fee",
            "amount": 30000.00,
        },
        headers=headers,
    )
    fs_id = res_fs.json()["data"]["id"]

    # Student belongs to 2025-2026 -> Allocation should be rejected
    res_alloc = client.post(
        "/api/v1/hostel/fees/allocations",
        json={
            "student_id": str(student.id),
            "fee_structure_id": fs_id,
            "due_date": "2026-05-01",
        },
        headers=headers,
    )
    assert res_alloc.status_code in [400, 422]


def test_hostel_fee_tenant_isolation(client: TestClient, db_session: Session):
    env1 = setup_hostel_fee_environment(db_session)
    env2 = setup_hostel_fee_environment(db_session)

    # School 1 creates structure
    res_fs = client.post(
        "/api/v1/hostel/fees/structures",
        json={
            "academic_year_id": str(env1["ay"].id),
            "name": "School 1 Hostel Fee",
            "amount": 20000.00,
        },
        headers=env1["headers"],
    )
    fs1_id = res_fs.json()["data"]["id"]

    # School 2 attempts to allocate School 1 structure to School 2 student -> 404
    res_alloc = client.post(
        "/api/v1/hostel/fees/allocations",
        json={
            "student_id": str(env2["student"].id),
            "fee_structure_id": fs1_id,
            "due_date": "2025-09-30",
        },
        headers=env2["headers"],
    )
    assert res_alloc.status_code == 404


def test_hostel_fee_payment_overpay_rejected(client: TestClient, db_session: Session):
    env = setup_hostel_fee_environment(db_session)
    headers = env["headers"]
    ay = env["ay"]
    student = env["student"]

    res_fs = client.post(
        "/api/v1/hostel/fees/structures",
        json={
            "academic_year_id": str(ay.id),
            "name": "Hostel Fixed Fee",
            "amount": 10000.00,
        },
        headers=headers,
    )
    fs_id = res_fs.json()["data"]["id"]

    res_alloc = client.post(
        "/api/v1/hostel/fees/allocations",
        json={
            "student_id": str(student.id),
            "fee_structure_id": fs_id,
            "due_date": "2025-09-30",
        },
        headers=headers,
    )
    fee_alloc_id = res_alloc.json()["data"]["id"]

    # Attempt to pay 15000 when due is 10000 -> Should be rejected
    res_pay = client.put(
        f"/api/v1/hostel/fees/allocations/{fee_alloc_id}/pay",
        json={"payment_amount": 15000.00},
        headers=headers,
    )
    assert res_pay.status_code in [400, 422]

