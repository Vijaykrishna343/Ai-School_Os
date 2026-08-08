import uuid

from app.models.school.school import School
from app.schemas.school_class import SchoolClassCreate, SchoolClassUpdate
from app.services.school_class_service import school_class_service


def create_sample_school(db):
    school = School(
        id=uuid.uuid4(),
        name="St Jude School",
        code="STJUDE",
        address_line1="45 Lake Rd",
        city="Chennai",
        district="Chennai",
        state="Tamil Nadu",
        country="India",
        postal_code="600001",
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def test_school_class_crud_operations(db_session):
    db = db_session
    school = create_sample_school(db)

    # 1. Create Class
    class_in = SchoolClassCreate(
        school_id=school.id,
        name="Class 10",
        display_order=1,
    )
    created = school_class_service.create_school_class(db, class_in)
    assert created.id is not None
    assert created.name == "Class 10"
    assert created.school_id == school.id

    # 2. Get Class
    fetched = school_class_service.get_school_class(db, created.id)
    assert fetched.id == created.id

    # 3. Get Classes by School
    school_classes = school_class_service.get_school_classes_by_school(db, school.id)
    assert len(school_classes) == 1

    # 4. Update Class
    update_in = SchoolClassUpdate(name="Class 10-A", display_order=2)
    updated = school_class_service.update_school_class(db, created.id, update_in)
    assert updated.name == "Class 10-A"
    assert updated.display_order == 2

    # 5. Delete Class
    school_class_service.delete_school_class(db, created.id)
    assert len(school_class_service.get_school_classes_by_school(db, school.id)) == 0
