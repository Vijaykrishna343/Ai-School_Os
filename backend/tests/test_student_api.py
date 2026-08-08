import uuid
from datetime import date

from app.models.school.school import School
from app.models.parent.parent import Parent
from app.models.academic_year.academic_year import AcademicYear
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.schemas.student.student_schema import StudentCreate, StudentUpdate, StudentFilter
from app.services.student.student_service import student_service


def setup_student_dependencies(db):
    school = School(
        id=uuid.uuid4(),
        name="Apex School",
        code="APEX",
        address_line1="100 Main St",
        city="Pune",
        district="Pune",
        state="Maharashtra",
        country="India",
        postal_code="411001",
    )
    db.add(school)
    db.commit()

    parent = Parent(
        id=uuid.uuid4(),
        school_id=school.id,
        father_name="Vikram Sharma",
        primary_phone="9988776655",
        address_line1="100 Main St",
        city="Pune",
        district="Pune",
        state="Maharashtra",
        postal_code="411001",
    )
    db.add(parent)

    academic_year = AcademicYear(
        id=uuid.uuid4(),
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    db.add(academic_year)

    school_class = SchoolClass(
        id=uuid.uuid4(),
        school_id=school.id,
        name="Class 1",
        display_order=1,
    )
    db.add(school_class)

    db.commit()

    section = Section(
        id=uuid.uuid4(),
        school_class_id=school_class.id,
        name="A",
    )
    db.add(section)
    db.commit()

    return school, parent, academic_year, school_class, section


def test_student_crud_and_auto_number_generation(db_session):
    db = db_session
    school, parent, ay, sclass, section = setup_student_dependencies(db)

    # 1. Create Student
    student_in = StudentCreate(
        school_id=school.id,
        parent_id=parent.id,
        academic_year_id=ay.id,
        school_class_id=sclass.id,
        section_id=section.id,
        first_name="Aarav",
        last_name="Sharma",
        gender="MALE",
        date_of_birth=date(2018, 5, 15),
        admission_date=date(2026, 4, 1),
        address_line1="100 Main St",
        city="Pune",
        district="Pune",
        state="Maharashtra",
        country="India",
        postal_code="411001",
    )
    created = student_service.create_student(db, student_in)
    assert created.id is not None
    assert created.first_name == "Aarav"
    assert created.admission_number is not None
    assert created.roll_number is not None

    # 2. Get Student by ID
    fetched = student_service.get_student(db, created.id)
    assert fetched.id == created.id

    # 3. Filter Students
    filters = StudentFilter(school_id=school.id, page=1, page_size=10)
    res = student_service.get_students(db, filters)
    assert res.total == 1
    assert len(res.items) == 1

    # 4. Search Students
    search_res = student_service.search_students(db, "Aarav")
    assert len(search_res) == 1

    # 5. Update Student
    update_in = StudentUpdate(middle_name="Kumar")
    updated = student_service.update_student(db, created.id, update_in)
    assert updated.middle_name == "Kumar"

    # 6. Delete Student
    student_service.delete_student(db, created.id)
    res_after = student_service.get_students(db, filters)
    assert res_after.total == 0
