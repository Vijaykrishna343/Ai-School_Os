import uuid
from datetime import date
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
from app.services.hostel_service import hostel_service


def test_hostel_night_roll_call_attendance(client: TestClient, db_session: Session):
    seed_identity(db_session)

    school = School(name="Att School", code=f"ATS-{uuid.uuid4().hex[:4]}", address_line1="123", city="Hyd", district="Hyd", state="TS", postal_code="500001")
    db_session.add(school)
    db_session.commit()

    admin_role = db_session.query(IdentityRole).filter_by(name="School Admin", school_id=None).first()
    admin_user = IdentityUser(
        school_id=school.id,
        email="att_admin@school.com",
        password_hash="hash",
        first_name="Admin",
        last_name="Att",
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
    parent = Parent(school_id=school.id, father_name="Papa", mother_name="Mama", primary_phone="9998887771", address_line1="123 St", city="Hyd", district="Hyd", state="TS", postal_code="500001")
    db_session.add_all([sec, parent])
    db_session.commit()

    student = Student(
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=sc.id,
        section_id=sec.id,
        parent_id=parent.id,
        admission_number=f"ADM-{uuid.uuid4().hex[:4]}",
        roll_number="102",
        first_name="RollCall",
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

    bldg = hostel_service.create_building(db_session, school.id, {"name": "Att Block", "code": f"AB-{uuid.uuid4().hex[:4]}", "gender_designation": "BOYS", "capacity": 50})
    room = hostel_service.create_room(db_session, school.id, bldg.id, {"room_number": "102", "floor": 1, "room_type": "STANDARD", "capacity": 2})
    bed = hostel_service.create_bed(db_session, school.id, room.id, {"bed_number": "102-A"})
    hostel_service.allocate_student(db_session, school.id, student.id, bldg.id, room.id, bed.id, date(2025, 6, 1))

    # Bulk Record Night Roll Call Attendance
    res_att = client.post(
        "/api/v1/hostel/attendance/bulk",
        json={
            "attendance_date": "2025-08-24",
            "building_id": str(bldg.id),
            "room_id": str(room.id),
            "records": [
                {
                    "student_id": str(student.id),
                    "status": "PRESENT",
                    "remarks": "On time",
                }
            ],
        },
        headers=headers,
    )
    assert res_att.status_code == 201

    # Get Attendance Records
    res_get = client.get(
        "/api/v1/hostel/attendance",
        params={"attendance_date": "2025-08-24", "building_id": str(bldg.id)},
        headers=headers,
    )
    assert res_get.status_code == 200
    assert len(res_get.json()["data"]) == 1
