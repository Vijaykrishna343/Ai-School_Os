from datetime import date, time
import uuid

import pytest

from app.common.enums.teacher import BloodGroup, Gender, TeacherStatus
from app.common.enums.timetable import DayOfWeek, PeriodType, RoomType, TimetableStatus
from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from app.models.academic_year.academic_year import AcademicYear
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.subject.subject import Subject
from app.models.teacher.teacher import Teacher
from app.models.timetable.classroom import Classroom
from app.models.timetable.period_slot import PeriodSlot
from app.schemas.timetable.timetable import TimetableCreate
from app.schemas.timetable.timetable_entry import (
    TimetableEntryCreate,
    TimetableEntryUpdate,
)
from app.services.timetable_entry_service import TimetableEntryService
from app.services.timetable_service import TimetableService


def make_school(name: str, code: str) -> School:
    return School(
        id=uuid.uuid4(),
        name=name,
        code=f"{code}_{uuid.uuid4().hex[:4]}",
        address_line1="100 Lifecycle Way",
        city="New Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )


@pytest.fixture
def lifecycle_setup(db_session):
    s1 = make_school("Lifecycle School 1", "LS1")
    db_session.add(s1)
    db_session.commit()

    ay1 = AcademicYear(school_id=s1.id, name="2026-2027", start_date=date(2026, 4, 1), end_date=date(2027, 3, 31), is_current=True)
    db_session.add(ay1)
    db_session.commit()

    sc1 = SchoolClass(school_id=s1.id, name="Class 5", display_order=1)
    db_session.add(sc1)
    db_session.commit()

    sec1 = Section(school_class_id=sc1.id, name="Section A")
    p1 = PeriodSlot(school_id=s1.id, name="Period 1", period_type=PeriodType.REGULAR, start_time=time(8, 30), end_time=time(9, 15), display_order=1)
    r1 = Classroom(school_id=s1.id, room_number="101", capacity=40, room_type=RoomType.CLASSROOM)
    sub = Subject(school_id=s1.id, subject_name="Mathematics", subject_code="MATH5")
    t1 = Teacher(
        school_id=s1.id,
        employee_id=f"EMP_{uuid.uuid4().hex[:6]}",
        first_name="Alice",
        last_name="Smith",
        gender=Gender.FEMALE,
        qualification="B.Ed",
        blood_group=BloodGroup.A_POSITIVE,
        date_of_birth=date(1990, 1, 1),
        joining_date=date(2020, 1, 1),
        email=f"alice_{uuid.uuid4().hex[:6]}@example.com",
        phone="9876543210",
        address_line1="100 St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
        status=TeacherStatus.ACTIVE,
    )
    db_session.add_all([sec1, p1, r1, sub, t1])
    db_session.commit()

    tt_service = TimetableService()
    entry_service = TimetableEntryService()

    tt = tt_service.create_timetable(
        db_session,
        TimetableCreate(school_id=s1.id, academic_year_id=ay1.id, school_class_id=sc1.id, section_id=sec1.id),
        current_school_id=s1.id,
    )
    entry = entry_service.create_entry(
        db_session,
        tt.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.MONDAY,
            period_slot_id=p1.id,
            subject_id=sub.id,
            teacher_id=t1.id,
            classroom_id=r1.id,
        ),
        current_school_id=s1.id,
    )

    return {
        "s1": s1, "ay1": ay1, "sc1": sc1, "sec1": sec1,
        "p1": p1, "r1": r1, "sub": sub, "t1": t1,
        "tt": tt, "entry": entry,
    }


def test_publish_empty_timetable_rejected(db_session, lifecycle_setup):
    tt_service = TimetableService()
    s = lifecycle_setup["s1"]
    ay = lifecycle_setup["ay1"]
    sc = lifecycle_setup["sc1"]
    sec = lifecycle_setup["sec1"]

    # Create second section
    sec2 = Section(school_class_id=sc.id, name="Section B")
    db_session.add(sec2)
    db_session.commit()

    empty_tt = tt_service.create_timetable(
        db_session,
        TimetableCreate(school_id=s.id, academic_year_id=ay.id, school_class_id=sc.id, section_id=sec2.id),
        current_school_id=s.id,
    )

    with pytest.raises(ValidationException, match="Cannot publish an empty timetable"):
        tt_service.publish_timetable(db_session, empty_tt.id, current_school_id=s.id)


def test_publish_and_archive_lifecycle(db_session, lifecycle_setup):
    tt_service = TimetableService()
    s = lifecycle_setup["s1"]
    tt = lifecycle_setup["tt"]

    # 1. Publish timetable
    published = tt_service.publish_timetable(db_session, tt.id, current_school_id=s.id)
    assert published.status == TimetableStatus.PUBLISHED

    # 2. Archive timetable
    archived = tt_service.archive_timetable(db_session, tt.id, current_school_id=s.id)
    assert archived.status == TimetableStatus.ARCHIVED
    assert archived.is_active is False


def test_published_timetable_entry_immutability(db_session, lifecycle_setup):
    tt_service = TimetableService()
    entry_service = TimetableEntryService()
    s = lifecycle_setup["s1"]
    tt = lifecycle_setup["tt"]
    entry = lifecycle_setup["entry"]
    p1 = lifecycle_setup["p1"]
    sub = lifecycle_setup["sub"]
    t1 = lifecycle_setup["t1"]

    tt_service.publish_timetable(db_session, tt.id, current_school_id=s.id)

    # Adding entry to published timetable should fail
    with pytest.raises(ValidationException, match="Structure is immutable"):
        entry_service.create_entry(
            db_session,
            tt.id,
            TimetableEntryCreate(
                day_of_week=DayOfWeek.TUESDAY,
                period_slot_id=p1.id,
                subject_id=sub.id,
                teacher_id=t1.id,
            ),
            current_school_id=s.id,
        )

    # Updating entry on published timetable should fail
    with pytest.raises(ValidationException, match="Structure is immutable"):
        entry_service.update_entry(
            db_session,
            entry.id,
            TimetableEntryUpdate(day_of_week=DayOfWeek.TUESDAY),
            current_school_id=s.id,
        )

    # Deleting entry on published timetable should fail
    with pytest.raises(ValidationException, match="Structure is immutable"):
        entry_service.delete_entry(db_session, entry.id, current_school_id=s.id)


def test_single_active_published_timetable_enforced(db_session, lifecycle_setup):
    tt_service = TimetableService()
    entry_service = TimetableEntryService()
    s = lifecycle_setup["s1"]
    ay = lifecycle_setup["ay1"]
    sc = lifecycle_setup["sc1"]
    sec = lifecycle_setup["sec1"]
    p1 = lifecycle_setup["p1"]
    sub = lifecycle_setup["sub"]
    t1 = lifecycle_setup["t1"]
    tt1 = lifecycle_setup["tt"]

    tt_service.publish_timetable(db_session, tt1.id, current_school_id=s.id)

    # Create a draft timetable for the SAME section after deleting first draft or creating v2
    # Note: create_timetable prevents duplicate DRAFT for section unless previous is published/archived
    tt2 = tt_service.create_timetable(
        db_session,
        TimetableCreate(school_id=s.id, academic_year_id=ay.id, school_class_id=sc.id, section_id=sec.id),
        current_school_id=s.id,
    )
    entry_service.create_entry(
        db_session,
        tt2.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.TUESDAY,
            period_slot_id=p1.id,
            subject_id=sub.id,
            teacher_id=t1.id,
        ),
        current_school_id=s.id,
    )

    # Attempting to publish tt2 while tt1 is active PUBLISHED must fail
    with pytest.raises(AlreadyExistsException):
        tt_service.publish_timetable(db_session, tt2.id, current_school_id=s.id)
