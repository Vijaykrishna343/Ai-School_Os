import uuid
from datetime import date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.school.school import School
from app.models.parent.parent import Parent
from app.models.student.student import Student
from app.models.academic_year.academic_year import AcademicYear
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.common.enums import Gender
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity


def test_hostel_fee_structure_and_payment(client: TestClient, db_session: Session):
    seed_identity(db_session)

    school = School(name="Fee School", code=f"FES-{uuid.uuid4().hex[:4]}", address_line1="123", city="Hyd", district="Hyd", state="TS", postal_code="500001")
    db_session.add(school)
    db_session.commit()

    admin_role = db_session.query(IdentityRole).filter_by(name="School Admin", school_id=None).first()
    admin_user = IdentityUser(
        school_id=school.id,
        email="fee_admin@school.com",
        password_hash="hash",
        first_name="Admin",
        last_name="Fee",
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
    parent = Parent(school_id=school.id, father_name="Papa", mother_name="Mama", primary_phone="9998887773", address_line1="123 St", city="Hyd", district="Hyd", state="TS", postal_code="500001")
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

    # 1. Create Fee Structure
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

    # 2. Allocate Fee to Student
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

    # 3. Pay Fee Allocation
    res_pay = client.put(
        f"/api/v1/hostel/fees/allocations/{fee_alloc_id}/pay",
        json={"payment_amount": 25000.00},
        headers=headers,
    )
    assert res_pay.status_code == 200
    assert res_pay.json()["data"]["status"] == "PAID"
