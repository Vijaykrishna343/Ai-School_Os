import uuid

from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.schemas.section.section import SectionCreate, SectionUpdate
from app.services.section_service import section_service


def create_sample_class(db):
    school = School(
        id=uuid.uuid4(),
        name="Oakridge School",
        code="OAKRIDGE",
        address_line1="78 Hill Rd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        country="India",
        postal_code="500001",
    )
    db.add(school)
    db.commit()

    school_class = SchoolClass(
        id=uuid.uuid4(),
        school_id=school.id,
        name="Grade 5",
        display_order=1,
    )
    db.add(school_class)
    db.commit()
    db.refresh(school_class)
    return school_class


def test_section_crud_operations(db_session):
    db = db_session
    school_class = create_sample_class(db)

    # 1. Create Section
    section_in = SectionCreate(
        school_class_id=school_class.id,
        name="A",
        capacity=35,
        room_number="R-101",
    )
    created = section_service.create_section(db, section_in)
    assert created.id is not None
    assert created.name == "A"

    # 2. Get Section by ID
    fetched = section_service.get_section(db, created.id)
    assert fetched.id == created.id

    # 3. Get Sections by Class
    sections = section_service.get_sections(db, school_class.id)
    assert len(sections) == 1

    # 4. Update Section
    update_in = SectionUpdate(room_number="R-102", capacity=40)
    updated = section_service.update_section(db, created.id, update_in)
    assert updated.room_number == "R-102"
    assert updated.capacity == 40

    # 5. Delete Section
    section_service.delete_section(db, created.id)
    assert len(section_service.get_sections(db, school_class.id)) == 0
