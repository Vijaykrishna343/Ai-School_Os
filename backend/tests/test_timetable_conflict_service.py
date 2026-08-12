from datetime import date, time
import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.common.enums.teacher import BloodGroup, Gender, TeacherStatus
from app.common.enums.timetable import DayOfWeek, PeriodType, RoomType
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
from app.models.subject.subject import Subject
from app.models.teacher.teacher import Teacher
from app.models.timetable.classroom import Classroom
from app.models.timetable.period_slot import PeriodSlot
from app.models.timetable.timetable import Timetable
from app.models.timetable.timetable_entry import TimetableEntry
from app.schemas.timetable.timetable import TimetableCreate
from app.schemas.timetable.timetable_entry import (
    TimetableEntryCreate,
    TimetableEntryUpdate,
)
from app.services.period_slot_service import PeriodSlotService
from app.services.timetable_entry_service import TimetableEntryService
from app.services.timetable_service import TimetableService


def make_school(name: str, code: str) -> School:
    return School(
        id=uuid.uuid4(),
        name=name,
        code=f"{code}_{uuid.uuid4().hex[:4]}",
        address_line1="100 Conflict Way",
        city="New Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )


@pytest.fixture
def conflict_setup(db_session):
    s1 = make_school("Conflict School 1", "CS1")
    s2 = make_school("Conflict School 2", "CS2")
    db_session.add_all([s1, s2])
    db_session.commit()

    ay1 = AcademicYear(school_id=s1.id, name="2026-2027", start_date=date(2026, 4, 1), end_date=date(2027, 3, 31), is_current=True)
    ay2 = AcademicYear(school_id=s2.id, name="2026-2027", start_date=date(2026, 4, 1), end_date=date(2027, 3, 31), is_current=True)
    db_session.add_all([ay1, ay2])
    db_session.commit()

    sc1 = SchoolClass(school_id=s1.id, name="Class 5", display_order=1)
    sc1_b = SchoolClass(school_id=s1.id, name="Class 6", display_order=2)
    sc2 = SchoolClass(school_id=s2.id, name="Class 5", display_order=1)
    db_session.add_all([sc1, sc1_b, sc2])
    db_session.commit()

    sec1_a = Section(school_class_id=sc1.id, name="Section A")
    sec1_b = Section(school_class_id=sc1_b.id, name="Section A")
    sec2_a = Section(school_class_id=sc2.id, name="Section A")
    db_session.add_all([sec1_a, sec1_b, sec2_a])
    db_session.commit()

    p1 = PeriodSlot(school_id=s1.id, name="Period 1", period_type=PeriodType.REGULAR, start_time=time(8, 30), end_time=time(9, 15), display_order=1)
    p2 = PeriodSlot(school_id=s1.id, name="Period 2", period_type=PeriodType.REGULAR, start_time=time(9, 15), end_time=time(10, 0), display_order=2)
    db_session.add_all([p1, p2])

    r1 = Classroom(school_id=s1.id, room_number="101", capacity=40, room_type=RoomType.CLASSROOM)
    r2 = Classroom(school_id=s1.id, room_number="102", capacity=40, room_type=RoomType.CLASSROOM)
    db_session.add_all([r1, r2])

    sub_math = Subject(school_id=s1.id, subject_name="Mathematics", subject_code="MATH5")
    sub_eng = Subject(school_id=s1.id, subject_name="English", subject_code="ENG5")
    db_session.add_all([sub_math, sub_eng])

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
    t2 = Teacher(
        school_id=s1.id,
        employee_id=f"EMP_{uuid.uuid4().hex[:6]}",
        first_name="Bob",
        last_name="Jones",
        gender=Gender.MALE,
        qualification="M.Ed",
        blood_group=BloodGroup.B_POSITIVE,
        date_of_birth=date(1988, 5, 5),
        joining_date=date(2019, 1, 1),
        email=f"bob_{uuid.uuid4().hex[:6]}@example.com",
        phone="9876543211",
        address_line1="101 St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
        status=TeacherStatus.ACTIVE,
    )
    db_session.add_all([t1, t2])
    db_session.commit()

    tt_service = TimetableService()
    tt1 = tt_service.create_timetable(
        db_session,
        TimetableCreate(school_id=s1.id, academic_year_id=ay1.id, school_class_id=sc1.id, section_id=sec1_a.id),
        current_school_id=s1.id,
    )
    tt2 = tt_service.create_timetable(
        db_session,
        TimetableCreate(school_id=s1.id, academic_year_id=ay1.id, school_class_id=sc1_b.id, section_id=sec1_b.id),
        current_school_id=s1.id,
    )

    return {
        "s1": s1, "s2": s2, "ay1": ay1,
        "sc1": sc1, "sc1_b": sc1_b, "sec1_a": sec1_a, "sec1_b": sec1_b,
        "p1": p1, "p2": p2, "r1": r1, "r2": r2,
        "sub_math": sub_math, "sub_eng": sub_eng,
        "t1": t1, "t2": t2,
        "tt1": tt1, "tt2": tt2,
    }


def test_section_slot_conflict_rejected(db_session, conflict_setup):
    service = TimetableEntryService()
    s = conflict_setup["s1"]
    tt1 = conflict_setup["tt1"]
    p1 = conflict_setup["p1"]
    sub_math = conflict_setup["sub_math"]
    sub_eng = conflict_setup["sub_eng"]
    t1 = conflict_setup["t1"]

    service.create_entry(
        db_session,
        tt1.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.MONDAY,
            period_slot_id=p1.id,
            subject_id=sub_math.id,
            teacher_id=t1.id,
        ),
        current_school_id=s.id,
    )

    # Second subject on same Monday + Period 1 should be rejected
    with pytest.raises(AlreadyExistsException):
        service.create_entry(
            db_session,
            tt1.id,
            TimetableEntryCreate(
                day_of_week=DayOfWeek.MONDAY,
                period_slot_id=p1.id,
                subject_id=sub_eng.id,
                teacher_id=t1.id,
            ),
            current_school_id=s.id,
        )


def test_teacher_double_booking_rejected(db_session, conflict_setup):
    service = TimetableEntryService()
    s = conflict_setup["s1"]
    tt1 = conflict_setup["tt1"]
    tt2 = conflict_setup["tt2"]
    p1 = conflict_setup["p1"]
    sub_math = conflict_setup["sub_math"]
    sub_eng = conflict_setup["sub_eng"]
    t1 = conflict_setup["t1"]

    # Assign Teacher Alice to Section 5A on Monday Period 1
    service.create_entry(
        db_session,
        tt1.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.MONDAY,
            period_slot_id=p1.id,
            subject_id=sub_math.id,
            teacher_id=t1.id,
        ),
        current_school_id=s.id,
    )

    # Assign same Teacher Alice to Section 6A on Monday Period 1 should be rejected
    with pytest.raises(ValidationException, match="already scheduled to teach"):
        service.create_entry(
            db_session,
            tt2.id,
            TimetableEntryCreate(
                day_of_week=DayOfWeek.MONDAY,
                period_slot_id=p1.id,
                subject_id=sub_eng.id,
                teacher_id=t1.id,
            ),
            current_school_id=s.id,
        )


def test_classroom_double_booking_rejected(db_session, conflict_setup):
    service = TimetableEntryService()
    s = conflict_setup["s1"]
    tt1 = conflict_setup["tt1"]
    tt2 = conflict_setup["tt2"]
    p1 = conflict_setup["p1"]
    r1 = conflict_setup["r1"]
    sub_math = conflict_setup["sub_math"]
    sub_eng = conflict_setup["sub_eng"]
    t1 = conflict_setup["t1"]
    t2 = conflict_setup["t2"]

    # Assign Room 101 to Section 5A on Monday Period 1 with Teacher Alice
    service.create_entry(
        db_session,
        tt1.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.MONDAY,
            period_slot_id=p1.id,
            subject_id=sub_math.id,
            teacher_id=t1.id,
            classroom_id=r1.id,
        ),
        current_school_id=s.id,
    )

    # Assign same Room 101 to Section 6A on Monday Period 1 with Teacher Bob should be rejected
    with pytest.raises(ValidationException, match="already occupied"):
        service.create_entry(
            db_session,
            tt2.id,
            TimetableEntryCreate(
                day_of_week=DayOfWeek.MONDAY,
                period_slot_id=p1.id,
                subject_id=sub_eng.id,
                teacher_id=t2.id,
                classroom_id=r1.id,
            ),
            current_school_id=s.id,
        )


def test_different_teachers_different_rooms_allowed(db_session, conflict_setup):
    service = TimetableEntryService()
    s = conflict_setup["s1"]
    tt1 = conflict_setup["tt1"]
    tt2 = conflict_setup["tt2"]
    p1 = conflict_setup["p1"]
    r1 = conflict_setup["r1"]
    r2 = conflict_setup["r2"]
    sub_math = conflict_setup["sub_math"]
    sub_eng = conflict_setup["sub_eng"]
    t1 = conflict_setup["t1"]
    t2 = conflict_setup["t2"]

    e1 = service.create_entry(
        db_session,
        tt1.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.MONDAY,
            period_slot_id=p1.id,
            subject_id=sub_math.id,
            teacher_id=t1.id,
            classroom_id=r1.id,
        ),
        current_school_id=s.id,
    )

    e2 = service.create_entry(
        db_session,
        tt2.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.MONDAY,
            period_slot_id=p1.id,
            subject_id=sub_eng.id,
            teacher_id=t2.id,
            classroom_id=r2.id,
        ),
        current_school_id=s.id,
    )

    assert e1.id is not None
    assert e2.id is not None


def test_different_periods_allowed(db_session, conflict_setup):
    service = TimetableEntryService()
    s = conflict_setup["s1"]
    tt1 = conflict_setup["tt1"]
    tt2 = conflict_setup["tt2"]
    p1 = conflict_setup["p1"]
    p2 = conflict_setup["p2"]
    r1 = conflict_setup["r1"]
    sub_math = conflict_setup["sub_math"]
    t1 = conflict_setup["t1"]

    # Teacher Alice in Room 101 on Period 1
    e1 = service.create_entry(
        db_session,
        tt1.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.MONDAY,
            period_slot_id=p1.id,
            subject_id=sub_math.id,
            teacher_id=t1.id,
            classroom_id=r1.id,
        ),
        current_school_id=s.id,
    )

    # Same Teacher Alice in same Room 101 on Period 2 for Section 6A is ALLOWED
    e2 = service.create_entry(
        db_session,
        tt2.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.MONDAY,
            period_slot_id=p2.id,
            subject_id=sub_math.id,
            teacher_id=t1.id,
            classroom_id=r1.id,
        ),
        current_school_id=s.id,
    )
    assert e1.id is not None
    assert e2.id is not None


def test_different_days_allowed(db_session, conflict_setup):
    service = TimetableEntryService()
    s = conflict_setup["s1"]
    tt1 = conflict_setup["tt1"]
    tt2 = conflict_setup["tt2"]
    p1 = conflict_setup["p1"]
    r1 = conflict_setup["r1"]
    sub_math = conflict_setup["sub_math"]
    t1 = conflict_setup["t1"]

    e1 = service.create_entry(
        db_session,
        tt1.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.MONDAY,
            period_slot_id=p1.id,
            subject_id=sub_math.id,
            teacher_id=t1.id,
            classroom_id=r1.id,
        ),
        current_school_id=s.id,
    )

    e2 = service.create_entry(
        db_session,
        tt2.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.TUESDAY,
            period_slot_id=p1.id,
            subject_id=sub_math.id,
            teacher_id=t1.id,
            classroom_id=r1.id,
        ),
        current_school_id=s.id,
    )
    assert e1.id is not None
    assert e2.id is not None


def test_null_classroom_allowed(db_session, conflict_setup):
    service = TimetableEntryService()
    s = conflict_setup["s1"]
    tt1 = conflict_setup["tt1"]
    tt2 = conflict_setup["tt2"]
    p1 = conflict_setup["p1"]
    sub_math = conflict_setup["sub_math"]
    sub_eng = conflict_setup["sub_eng"]
    t1 = conflict_setup["t1"]
    t2 = conflict_setup["t2"]

    # Two sections scheduled on Monday Period 1 with NULL classrooms should NOT conflict on classroom
    e1 = service.create_entry(
        db_session,
        tt1.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.MONDAY,
            period_slot_id=p1.id,
            subject_id=sub_math.id,
            teacher_id=t1.id,
            classroom_id=None,
        ),
        current_school_id=s.id,
    )

    e2 = service.create_entry(
        db_session,
        tt2.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.MONDAY,
            period_slot_id=p1.id,
            subject_id=sub_eng.id,
            teacher_id=t2.id,
            classroom_id=None,
        ),
        current_school_id=s.id,
    )
    assert e1.classroom_id is None
    assert e2.classroom_id is None


def test_update_entry_excluding_self(db_session, conflict_setup):
    service = TimetableEntryService()
    s = conflict_setup["s1"]
    tt1 = conflict_setup["tt1"]
    p1 = conflict_setup["p1"]
    r1 = conflict_setup["r1"]
    sub_math = conflict_setup["sub_math"]
    sub_eng = conflict_setup["sub_eng"]
    t1 = conflict_setup["t1"]

    e1 = service.create_entry(
        db_session,
        tt1.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.MONDAY,
            period_slot_id=p1.id,
            subject_id=sub_math.id,
            teacher_id=t1.id,
            classroom_id=r1.id,
        ),
        current_school_id=s.id,
    )

    # Updating subject on e1 without changing day/period/teacher/room should succeed!
    updated = service.update_entry(
        db_session,
        e1.id,
        TimetableEntryUpdate(subject_id=sub_eng.id),
        current_school_id=s.id,
    )
    assert updated.subject_id == sub_eng.id


def test_database_level_unique_constraint(db_session, conflict_setup):
    tt1 = conflict_setup["tt1"]
    p1 = conflict_setup["p1"]
    sub_math = conflict_setup["sub_math"]
    t1 = conflict_setup["t1"]

    e1 = TimetableEntry(
        timetable_id=tt1.id,
        day_of_week=DayOfWeek.MONDAY,
        period_slot_id=p1.id,
        subject_id=sub_math.id,
        teacher_id=t1.id,
    )
    db_session.add(e1)
    db_session.commit()

    # Direct database insertion bypassing application service
    e2 = TimetableEntry(
        timetable_id=tt1.id,
        day_of_week=DayOfWeek.MONDAY,
        period_slot_id=p1.id,
        subject_id=sub_math.id,
        teacher_id=t1.id,
    )
    db_session.add(e2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_soft_deleted_entry_allows_recreation(db_session, conflict_setup):
    service = TimetableEntryService()
    s = conflict_setup["s1"]
    tt1 = conflict_setup["tt1"]
    p1 = conflict_setup["p1"]
    sub_math = conflict_setup["sub_math"]
    t1 = conflict_setup["t1"]

    e1 = service.create_entry(
        db_session,
        tt1.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.MONDAY,
            period_slot_id=p1.id,
            subject_id=sub_math.id,
            teacher_id=t1.id,
        ),
        current_school_id=s.id,
    )

    service.delete_entry(db_session, e1.id, current_school_id=s.id)

    # Re-creating entry for same slot should succeed after soft delete
    e2 = service.create_entry(
        db_session,
        tt1.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.MONDAY,
            period_slot_id=p1.id,
            subject_id=sub_math.id,
            teacher_id=t1.id,
        ),
        current_school_id=s.id,
    )
    assert e2.id != e1.id


def test_eager_loading_matrix_performance(db_session, conflict_setup):
    service = TimetableService()
    entry_service = TimetableEntryService()
    s = conflict_setup["s1"]
    tt1 = conflict_setup["tt1"]
    p1 = conflict_setup["p1"]
    p2 = conflict_setup["p2"]
    r1 = conflict_setup["r1"]
    sub_math = conflict_setup["sub_math"]
    t1 = conflict_setup["t1"]

    entry_service.create_entry(
        db_session,
        tt1.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.MONDAY,
            period_slot_id=p1.id,
            subject_id=sub_math.id,
            teacher_id=t1.id,
            classroom_id=r1.id,
        ),
        current_school_id=s.id,
    )
    entry_service.create_entry(
        db_session,
        tt1.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.TUESDAY,
            period_slot_id=p2.id,
            subject_id=sub_math.id,
            teacher_id=t1.id,
            classroom_id=r1.id,
        ),
        current_school_id=s.id,
    )

    detail = service.get_timetable(db_session, tt1.id, current_school_id=s.id)

    assert len(detail.entries) == 2
    assert detail.entries[0].period_slot.name is not None
    assert detail.entries[0].subject.subject_name is not None
    assert detail.entries[0].teacher.first_name is not None
    assert detail.entries[0].classroom.room_number is not None
