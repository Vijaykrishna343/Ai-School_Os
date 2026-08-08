import uuid
from datetime import date
import pytest

from app.common.enums import AcademicYearStatus, Gender, StudentStatus
from app.common.enums.parent import ParentRelationship
from app.models.academic_year.academic_year import AcademicYear
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.schemas.academic_year import AcademicYearCreate, AcademicYearUpdate
from app.services.academic_year_service import academic_year_service


def create_sample_school(db, name="Service Test School", code="STSCH"):
    school = School(
        id=uuid.uuid4(),
        name=name,
        code=code,
        address_line1="10 Main St",
        city="New Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def test_academic_year_enum_canonical_values():
    assert AcademicYearStatus.UPCOMING.value == "UPCOMING"
    assert AcademicYearStatus.ACTIVE.value == "ACTIVE"
    assert AcademicYearStatus.ARCHIVED.value == "ARCHIVED"
    values = {e.value for e in AcademicYearStatus}
    assert values == {"UPCOMING", "ACTIVE", "ARCHIVED"}


def test_academic_year_crud_and_current_switch(db_session):
    db = db_session
    school = create_sample_school(db, "Switch Test School", "SWITCH1")

    # 1. Create Academic Year 1 (is_current=True)
    ay1_in = AcademicYearCreate(
        school_id=school.id,
        name="2025-2026",
        start_date=date(2025, 4, 1),
        end_date=date(2026, 3, 31),
        is_current=True,
    )
    ay1 = academic_year_service.create_academic_year(db, ay1_in)
    assert ay1.id is not None
    assert ay1.is_current is True

    # 2. Create Academic Year 2 (is_current=True) - should deactivate AY1
    ay2_in = AcademicYearCreate(
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    ay2 = academic_year_service.create_academic_year(db, ay2_in)
    assert ay2.is_current is True

    # Refresh AY1 from DB to verify it was set to is_current=False
    ay1_refreshed = academic_year_service.get_academic_year(db, ay1.id)
    assert ay1_refreshed.is_current is False

    # 3. Get All Academic Years for school
    all_ays = academic_year_service.get_all_academic_years(db, school_id=school.id)
    assert len(all_ays) == 2

    # 4. Update Academic Year
    update_in = AcademicYearUpdate(name="2026-2027 Term 1-2")
    updated = academic_year_service.update_academic_year(db, ay2.id, update_in)
    assert updated.name == "2026-2027 Term 1-2"

    # 5. Delete Academic Year
    academic_year_service.delete_academic_year(db, ay1.id)
    academic_year_service.delete_academic_year(db, ay2.id)
    assert len(academic_year_service.get_all_academic_years(db, school_id=school.id)) == 0


def test_academic_year_database_pagination(db_session):
    db = db_session
    school = create_sample_school(db, "Paging Test School", "PAGE1")

    # Create 15 Academic Years
    for i in range(1, 16):
        ay_in = AcademicYearCreate(
            school_id=school.id,
            name=f"2030-2031-AY-{i:02d}",
            start_date=date(2030, 1, i),
            end_date=date(2030, 12, 31),
            is_current=False,
        )
        academic_year_service.create_academic_year(db, ay_in)

    # Page 1 (10 items)
    items_p1, total, total_pages = academic_year_service.get_paginated_academic_years(
        db, school_id=school.id, page=1, page_size=10
    )
    assert len(items_p1) == 10
    assert total == 15
    assert total_pages == 2

    # Page 2 (5 items)
    items_p2, total, total_pages = academic_year_service.get_paginated_academic_years(
        db, school_id=school.id, page=2, page_size=10
    )
    assert len(items_p2) == 5
    assert total == 15


def test_student_survives_academic_year_soft_deletion(db_session):
    db = db_session
    school = create_sample_school(db, "Student Safety School", "STU1")

    # 1. Create Academic Year
    ay_in = AcademicYearCreate(
        school_id=school.id,
        name="2027-2028",
        start_date=date(2027, 4, 1),
        end_date=date(2028, 3, 31),
        is_current=True,
    )
    ay = academic_year_service.create_academic_year(db, ay_in)

    # 2. Create Parent
    parent = Parent(
        id=uuid.uuid4(),
        school_id=school.id,
        father_name="Ramesh Kumar",
        primary_phone="9876543210",
        relationship=ParentRelationship.FATHER,
        address_line1="12 Park St",
        city="Delhi",
        district="Delhi",
        state="Delhi",
        postal_code="110001",
    )
    db.add(parent)

    # 3. Create Class & Section
    sclass = SchoolClass(
        id=uuid.uuid4(),
        school_id=school.id,
        name="Class 10",
        display_order=1,
    )
    db.add(sclass)

    section = Section(
        id=uuid.uuid4(),
        school_class_id=sclass.id,
        name="Section A",
    )
    db.add(section)
    db.commit()

    # 4. Create Student linked to Academic Year
    student = Student(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=sclass.id,
        section_id=section.id,
        parent_id=parent.id,
        admission_number="ADM-9999",
        roll_number="101",
        first_name="Aarav",
        last_name="Kumar",
        gender=Gender.MALE,
        date_of_birth=date(2010, 5, 15),
        admission_date=date(2027, 4, 1),
        address_line1="12 Park St",
        city="Delhi",
        district="Delhi",
        state="Delhi",
        postal_code="110001",
        status=StudentStatus.ACTIVE,
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    student_id = student.id

    # 5. Soft-delete Academic Year
    academic_year_service.delete_academic_year(db, ay.id)

    # 6. Verify Academic Year is soft-deleted
    refreshed_ay = db.get(AcademicYear, ay.id)
    assert refreshed_ay.is_deleted is True

    # 7. Verify Student still exists in database and is NOT deleted
    refreshed_student = db.get(Student, student_id)
    assert refreshed_student is not None
    assert refreshed_student.is_deleted is False
    assert refreshed_student.academic_year_id == ay.id
