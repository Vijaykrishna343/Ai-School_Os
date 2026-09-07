import uuid

from app.models.school.school import School
from app.schemas.parent import ParentCreate, ParentUpdate
from app.services.parent_service import parent_service


def create_sample_school(db):
    s = uuid.uuid4().hex[:6]
    school = School(
        id=uuid.uuid4(),
        name=f"Delhi Public School {s}",
        code=f"DPS_{s}",
        address_line1="1 Ring Rd",
        city="New Delhi",
        district="Central Delhi",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def test_parent_crud_operations(db_session):
    db = db_session
    school = create_sample_school(db)
    s = uuid.uuid4().hex[:6]

    # Count parents before the test
    all_parents_before = parent_service.get_all_parents(db)
    count_before = len(all_parents_before)

    # 1. Create Parent
    parent_in = ParentCreate(
        school_id=school.id,
        father_name="Rajesh Kumar",
        mother_name="Sunita Kumar",
        primary_phone=f"98{s[:8].ljust(8, '0')}",
        email=f"rajesh_{s}@example.com",
        address_line1="45 Connaught Place",
        city="New Delhi",
        district="Central Delhi",
        state="Delhi",
        postal_code="110001",
    )
    created = parent_service.create_parent(db, parent_in)
    assert created.id is not None
    assert created.father_name == "Rajesh Kumar"

    # 2. Get Parent
    fetched = parent_service.get_parent(db, created.id)
    assert fetched.id == created.id
    assert fetched.primary_phone == parent_in.primary_phone

    # 3. Get All Parents — should have one more than before
    all_parents = parent_service.get_all_parents(db)
    assert len(all_parents) == count_before + 1

    # 4. Update Parent
    update_in = ParentUpdate(occupation="Engineer")
    updated = parent_service.update_parent(db, created.id, update_in)
    assert updated.occupation == "Engineer"

    # 5. Delete Parent
    parent_service.delete_parent(db, created.id)
    assert len(parent_service.get_all_parents(db)) == count_before

