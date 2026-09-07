import uuid

from app.schemas.school.school import SchoolCreate, SchoolUpdate
from app.services.school_service import school_service


def test_school_create_get_update_delete(db_session):
    db = db_session
    suffix = uuid.uuid4().hex[:6]

    # Count schools before the test
    count_before = len(school_service.get_all_schools(db))

    # 1. Create School
    school_in = SchoolCreate(
        name="Greenwood High",
        code=f"GWH_{suffix}",
        email=f"info_{suffix}@greenwood.edu",
        phone=f"9{uuid.uuid4().int % 1000000009:09d}",
        address_line1="100 Park Ave",
        city="Bangalore",
        district="Bangalore Urban",
        state="Karnataka",
        postal_code="560001",
    )
    created = school_service.create_school(db, school_in)
    assert created.id is not None
    assert created.name == "Greenwood High"
    assert created.code == f"GWH_{suffix}"

    # 2. Get School
    fetched = school_service.get_school(db, created.id)
    assert fetched.id == created.id
    assert fetched.email == f"info_{suffix}@greenwood.edu"

    # 3. Get All Schools — should have one more than before
    all_schools = school_service.get_all_schools(db)
    assert len(all_schools) == count_before + 1

    # 4. Update School
    update_in = SchoolUpdate(name="Greenwood International High")
    updated = school_service.update_school(db, created.id, update_in)
    assert updated.name == "Greenwood International High"

    # 5. Delete School
    school_service.delete_school(db, created.id)
    assert len(school_service.get_all_schools(db)) == count_before

