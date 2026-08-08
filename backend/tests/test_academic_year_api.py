import uuid
from datetime import date

from app.models.school.school import School
from app.schemas.academic_year import AcademicYearCreate, AcademicYearUpdate
from app.services.academic_year_service import academic_year_service


def create_sample_school(db):
    school = School(
        id=uuid.uuid4(),
        name="Modern School",
        code="MODERN",
        address_line1="5 Barakhamba Rd",
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


def test_academic_year_crud_and_current_switch(db_session):
    db = db_session
    school = create_sample_school(db)

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

    # 3. Get All Academic Years
    all_ays = academic_year_service.get_all_academic_years(db)
    assert len(all_ays) == 2

    # 4. Update Academic Year
    update_in = AcademicYearUpdate(name="2026-2027 Term 1-2")
    updated = academic_year_service.update_academic_year(db, ay2.id, update_in)
    assert updated.name == "2026-2027 Term 1-2"

    # 5. Delete Academic Year
    academic_year_service.delete_academic_year(db, ay1.id)
    academic_year_service.delete_academic_year(db, ay2.id)
    assert len(academic_year_service.get_all_academic_years(db)) == 0
