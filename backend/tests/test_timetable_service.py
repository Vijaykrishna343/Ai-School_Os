from datetime import date
import uuid

import pytest

from app.common.enums.timetable import TimetableStatus
from app.common.exceptions import (
    AlreadyExistsException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.academic_year.academic_year import AcademicYear
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.schemas.timetable.timetable import (
    TimetableCreate,
    TimetableFilter,
    TimetableUpdate,
)
from app.services.timetable_service import TimetableService


def make_school(name: str, code: str) -> School:
    return School(
        id=uuid.uuid4(),
        name=name,
        code=f"{code}_{uuid.uuid4().hex[:4]}",
        address_line1="100 Timetable St",
        city="New Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )


@pytest.fixture
def timetable_setup(db_session):
    s1 = make_school("Timetable School 1", "TS1")
    s2 = make_school("Timetable School 2", "TS2")
    db_session.add_all([s1, s2])
    db_session.commit()

    ay1 = AcademicYear(school_id=s1.id, name="2026-2027", start_date=date(2026, 4, 1), end_date=date(2027, 3, 31), is_current=True)
    ay2 = AcademicYear(school_id=s2.id, name="2026-2027", start_date=date(2026, 4, 1), end_date=date(2027, 3, 31), is_current=True)
    db_session.add_all([ay1, ay2])
    db_session.commit()

    sc1 = SchoolClass(school_id=s1.id, name="Class 5", display_order=1)
    sc2 = SchoolClass(school_id=s2.id, name="Class 5", display_order=1)
    db_session.add_all([sc1, sc2])
    db_session.commit()

    sec1 = Section(school_class_id=sc1.id, name="Section A")
    sec2 = Section(school_class_id=sc2.id, name="Section A")
    db_session.add_all([sec1, sec2])
    db_session.commit()

    return {
        "s1": s1,
        "s2": s2,
        "ay1": ay1,
        "ay2": ay2,
        "sc1": sc1,
        "sc2": sc2,
        "sec1": sec1,
        "sec2": sec2,
    }


def test_create_timetable_success(db_session, timetable_setup):
    service = TimetableService()
    s = timetable_setup["s1"]
    ay = timetable_setup["ay1"]
    sc = timetable_setup["sc1"]
    sec = timetable_setup["sec1"]

    payload = TimetableCreate(
        school_id=s.id,
        academic_year_id=ay.id,
        school_class_id=sc.id,
        section_id=sec.id,
    )
    res = service.create_timetable(db_session, payload, current_school_id=s.id)

    assert res.id is not None
    assert res.school_id == s.id
    assert res.academic_year_id == ay.id
    assert res.section_id == sec.id
    assert res.status == TimetableStatus.DRAFT
    assert res.is_active is True


def test_create_timetable_cross_school_rejected(db_session, timetable_setup):
    service = TimetableService()
    s1 = timetable_setup["s1"]
    s2 = timetable_setup["s2"]
    ay1 = timetable_setup["ay1"]
    sc1 = timetable_setup["sc1"]
    sec1 = timetable_setup["sec1"]

    payload = TimetableCreate(
        school_id=s1.id,
        academic_year_id=ay1.id,
        school_class_id=sc1.id,
        section_id=sec1.id,
    )
    with pytest.raises(ForbiddenException):
        service.create_timetable(db_session, payload, current_school_id=s2.id)


def test_create_timetable_section_class_mismatch_rejected(db_session, timetable_setup):
    service = TimetableService()
    s = timetable_setup["s1"]
    ay = timetable_setup["ay1"]
    sc = timetable_setup["sc1"]
    sec2 = timetable_setup["sec2"]  # sec2 belongs to sc2!

    payload = TimetableCreate(
        school_id=s.id,
        academic_year_id=ay.id,
        school_class_id=sc.id,
        section_id=sec2.id,
    )
    with pytest.raises(ValidationException, match="Section must belong to the specified school class"):
        service.create_timetable(db_session, payload, current_school_id=s.id)


def test_create_timetable_duplicate_section_rejected(db_session, timetable_setup):
    service = TimetableService()
    s = timetable_setup["s1"]
    ay = timetable_setup["ay1"]
    sc = timetable_setup["sc1"]
    sec = timetable_setup["sec1"]

    payload = TimetableCreate(
        school_id=s.id,
        academic_year_id=ay.id,
        school_class_id=sc.id,
        section_id=sec.id,
    )
    service.create_timetable(db_session, payload, current_school_id=s.id)

    with pytest.raises(AlreadyExistsException):
        service.create_timetable(db_session, payload, current_school_id=s.id)


def test_tenant_isolation_timetable(db_session, timetable_setup):
    service = TimetableService()
    s1 = timetable_setup["s1"]
    s2 = timetable_setup["s2"]
    ay1 = timetable_setup["ay1"]
    sc1 = timetable_setup["sc1"]
    sec1 = timetable_setup["sec1"]

    t1 = service.create_timetable(
        db_session,
        TimetableCreate(
            school_id=s1.id,
            academic_year_id=ay1.id,
            school_class_id=sc1.id,
            section_id=sec1.id,
        ),
        current_school_id=s1.id,
    )

    # s2 cannot read s1's timetable
    with pytest.raises(NotFoundException):
        service.get_timetable(db_session, t1.id, current_school_id=s2.id)

    # s2 cannot list s1's section timetable
    with pytest.raises(NotFoundException):
        service.get_section_timetable(db_session, sec1.id, current_school_id=s2.id)


def test_list_timetables(db_session, timetable_setup):
    service = TimetableService()
    s = timetable_setup["s1"]
    ay = timetable_setup["ay1"]
    sc = timetable_setup["sc1"]
    sec = timetable_setup["sec1"]

    service.create_timetable(
        db_session,
        TimetableCreate(
            school_id=s.id,
            academic_year_id=ay.id,
            school_class_id=sc.id,
            section_id=sec.id,
        ),
        current_school_id=s.id,
    )

    result = service.list_timetables(
        db_session,
        TimetableFilter(page=1, page_size=10),
        current_school_id=s.id,
    )
    assert result.total == 1
    assert len(result.items) == 1
