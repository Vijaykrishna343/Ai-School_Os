import uuid
from datetime import date

from app.models.school.school import School
from app.schemas.teacher import TeacherCreate, TeacherUpdate, TeacherFilter
from app.services.teacher.teacher_service import teacher_service


def create_sample_school(db):
    school = School(
        id=uuid.uuid4(),
        name="National Public School",
        code="NPS001",
        address_line1="123 Ring Rd",
        city="Bangalore",
        district="Bangalore Urban",
        state="Karnataka",
        country="India",
        postal_code="560001",
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def test_teacher_crud_and_auto_employee_id(db_session):
    db = db_session
    school = create_sample_school(db)

    # 1. Create Teacher
    teacher_in = TeacherCreate(
        school_id=school.id,
        first_name="Ramesh",
        last_name="Verma",
        gender="MALE",
        date_of_birth=date(1985, 3, 20),
        joining_date=date(2015, 6, 1),
        qualification="M.Sc Physics",
        phone="9876501234",
        email="ramesh.verma@school.edu",
        address_line1="123 Ring Rd",
        city="Bangalore",
        district="Bangalore Urban",
        state="Karnataka",
        country="India",
        postal_code="560001",
    )
    created = teacher_service.create_teacher(db, teacher_in)
    assert created.id is not None
    assert created.first_name == "Ramesh"
    assert created.employee_id is not None

    # 2. Get Teacher by ID
    fetched = teacher_service.get_teacher(db, created.id)
    assert fetched.id == created.id

    # 3. Filter Teachers
    filters = TeacherFilter(school_id=school.id, page=1, page_size=10)
    res = teacher_service.get_teachers(db, filters)
    assert res.total == 1
    assert len(res.items) == 1

    # 4. Search Teachers
    search_res = teacher_service.search_teachers(db, "Ramesh")
    assert len(search_res) == 1

    # 5. Update Teacher
    update_in = TeacherUpdate(qualification="M.Sc Mathematics")
    updated = teacher_service.update_teacher(db, created.id, update_in)
    assert updated.qualification == "M.Sc Mathematics"

    # 6. Delete Teacher
    teacher_service.delete_teacher(db, created.id)
    res_after = teacher_service.get_teachers(db, filters)
    assert res_after.total == 0
