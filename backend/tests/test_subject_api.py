import uuid

from app.models.school.school import School
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectFilter
from app.services.subject.subject_service import subject_service


def create_sample_school(db):
    school = School(
        id=uuid.uuid4(),
        name="Loyola School",
        code="LOYOLA",
        address_line1="12 Church St",
        city="Kolkata",
        district="Kolkata",
        state="West Bengal",
        country="India",
        postal_code="700001",
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def test_subject_crud_operations(db_session):
    db = db_session
    school = create_sample_school(db)

    # 1. Create Subject
    subject_in = SubjectCreate(
        school_id=school.id,
        subject_name="Mathematics",
        subject_code="MATH101",
        is_optional=False,
    )
    created = subject_service.create_subject(db, subject_in)
    assert created.id is not None
    assert created.subject_name == "Mathematics"

    # 2. Get Subject by ID
    fetched = subject_service.get_subject(db, created.id)
    assert fetched.id == created.id

    # 3. Get Subjects List with Filter
    filters = SubjectFilter(school_id=school.id, page=1, page_size=10)
    res = subject_service.get_subjects(db, filters)
    assert res.total == 1
    assert len(res.items) == 1

    # 4. Update Subject
    update_in = SubjectUpdate(subject_name="Advanced Mathematics")
    updated = subject_service.update_subject(db, created.id, update_in)
    assert updated.subject_name == "Advanced Mathematics"

    # 5. Delete Subject
    subject_service.delete_subject(db, created.id)
    res_after = subject_service.get_subjects(db, filters)
    assert res_after.total == 0
