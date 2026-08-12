from datetime import date, time
import uuid

import pytest

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
from app.schemas.timetable.teacher_substitution import (
    TeacherSubstitutionCreate,
    TeacherSubstitutionFilter,
    TeacherSubstitutionUpdate,
)
from app.schemas.timetable.timetable import TimetableCreate
from app.schemas.timetable.timetable_entry import TimetableEntryCreate
from app.services.teacher_substitution_service import TeacherSubstitutionService
from app.services.timetable_entry_service import TimetableEntryService
from app.services.timetable_service import TimetableService


def make_school(name: str, code: str) -> School:
    return School(
        id=uuid.uuid4(),
        name=name,
        code=f"{code}_{uuid.uuid4().hex[:4]}",
        address_line1="100 Substitution Way",
        city="New Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )


@pytest.fixture
def sub_setup(db_session):
    s1 = make_school("Substitution School 1", "SS1")
    s2 = make_school("Substitution School 2", "SS2")
    db_session.add_all([s1, s2])
    db_session.commit()

    ay1 = AcademicYear(school_id=s1.id, name="2026-2027", start_date=date(2026, 4, 1), end_date=date(2027, 3, 31), is_current=True)
    db_session.add(ay1)
    db_session.commit()

    sc1 = SchoolClass(school_id=s1.id, name="Class 5", display_order=1)
    sc1_b = SchoolClass(school_id=s1.id, name="Class 6", display_order=2)
    db_session.add_all([sc1, sc1_b])
    db_session.commit()

    sec1_a = Section(school_class_id=sc1.id, name="Section A")
    sec1_b = Section(school_class_id=sc1_b.id, name="Section A")
    db_session.add_all([sec1_a, sec1_b])
    db_session.commit()

    p1 = PeriodSlot(school_id=s1.id, name="Period 1", period_type=PeriodType.REGULAR, start_time=time(8, 30), end_time=time(9, 15), display_order=1)
    r1 = Classroom(school_id=s1.id, room_number="101", capacity=40, room_type=RoomType.CLASSROOM)
    r2 = Classroom(school_id=s1.id, room_number="102", capacity=40, room_type=RoomType.CLASSROOM)
    sub = Subject(school_id=s1.id, subject_name="Mathematics", subject_code="MATH5")

    t_orig = Teacher(
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
    t_sub = Teacher(
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
    t_sub2 = Teacher(
        school_id=s1.id,
        employee_id=f"EMP_{uuid.uuid4().hex[:6]}",
        first_name="Charlie",
        last_name="Brown",
        gender=Gender.MALE,
        qualification="Ph.D",
        blood_group=BloodGroup.O_POSITIVE,
        date_of_birth=date(1985, 3, 3),
        joining_date=date(2018, 1, 1),
        email=f"charlie_{uuid.uuid4().hex[:6]}@example.com",
        phone="9876543212",
        address_line1="102 St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
        status=TeacherStatus.ACTIVE,
    )
    db_session.add_all([sec1_a, sec1_b, p1, r1, r2, sub, t_orig, t_sub, t_sub2])
    db_session.commit()

    tt_service = TimetableService()
    entry_service = TimetableEntryService()

    tt1 = tt_service.create_timetable(
        db_session,
        TimetableCreate(school_id=s1.id, academic_year_id=ay1.id, school_class_id=sc1.id, section_id=sec1_a.id),
        current_school_id=s1.id,
    )
    entry1 = entry_service.create_entry(
        db_session,
        tt1.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.MONDAY,
            period_slot_id=p1.id,
            subject_id=sub.id,
            teacher_id=t_orig.id,
            classroom_id=r1.id,
        ),
        current_school_id=s1.id,
    )

    tt2 = tt_service.create_timetable(
        db_session,
        TimetableCreate(school_id=s1.id, academic_year_id=ay1.id, school_class_id=sc1_b.id, section_id=sec1_b.id),
        current_school_id=s1.id,
    )
    entry2 = entry_service.create_entry(
        db_session,
        tt2.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.MONDAY,
            period_slot_id=p1.id,
            subject_id=sub.id,
            teacher_id=t_sub2.id,
            classroom_id=r2.id,
        ),
        current_school_id=s1.id,
    )

    # Publish tt1 and tt2
    tt_service.publish_timetable(db_session, tt1.id, current_school_id=s1.id)
    tt_service.publish_timetable(db_session, tt2.id, current_school_id=s1.id)

    return {
        "s1": s1, "s2": s2, "ay1": ay1,
        "sc1": sc1, "sec1_a": sec1_a, "p1": p1, "sub": sub,
        "t_orig": t_orig, "t_sub": t_sub, "t_sub2": t_sub2,
        "tt1": tt1, "entry1": entry1,
        "tt2": tt2, "entry2": entry2,
    }


def test_create_substitution_success(db_session, sub_setup):
    service = TeacherSubstitutionService()
    s = sub_setup["s1"]
    entry1 = sub_setup["entry1"]
    t_sub = sub_setup["t_sub"]

    # 2026-08-10 is a MONDAY
    sub_date = date(2026, 8, 10)
    sub = service.create_substitution(
        db_session,
        TeacherSubstitutionCreate(
            school_id=s.id,
            timetable_entry_id=entry1.id,
            substitution_date=sub_date,
            substitute_teacher_id=t_sub.id,
            remarks="Alice on sick leave",
        ),
        current_school_id=s.id,
    )

    assert sub.id is not None
    assert sub.timetable_entry_id == entry1.id
    assert sub.original_teacher_id == sub_setup["t_orig"].id
    assert sub.substitute_teacher_id == t_sub.id
    assert sub.remarks == "Alice on sick leave"


def test_create_substitution_draft_timetable_rejected(db_session, sub_setup):
    service = TeacherSubstitutionService()
    tt_service = TimetableService()
    entry_service = TimetableEntryService()
    s = sub_setup["s1"]
    ay = sub_setup["ay1"]
    p1 = sub_setup["p1"]
    sub_item = sub_setup["sub"]
    t_orig = sub_setup["t_orig"]
    t_sub = sub_setup["t_sub"]

    # Create section 3
    sc3 = SchoolClass(school_id=s.id, name="Class 7", display_order=3)
    db_session.add(sc3)
    db_session.commit()

    sec3 = Section(school_class_id=sc3.id, name="Section A")
    db_session.add(sec3)
    db_session.commit()

    draft_tt = tt_service.create_timetable(
        db_session,
        TimetableCreate(school_id=s.id, academic_year_id=ay.id, school_class_id=sc3.id, section_id=sec3.id),
        current_school_id=s.id,
    )
    draft_entry = entry_service.create_entry(
        db_session,
        draft_tt.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.TUESDAY,
            period_slot_id=p1.id,
            subject_id=sub_item.id,
            teacher_id=t_orig.id,
        ),
        current_school_id=s.id,
    )

    # Attempting substitution on DRAFT timetable must fail
    with pytest.raises(ValidationException, match="Substitutions can only be assigned to PUBLISHED timetables"):
        service.create_substitution(
            db_session,
            TeacherSubstitutionCreate(
                school_id=s.id,
                timetable_entry_id=draft_entry.id,
                substitution_date=date(2026, 8, 11),
                substitute_teacher_id=t_sub.id,
            ),
            current_school_id=s.id,
        )


def test_weekday_mismatch_rejected(db_session, sub_setup):
    service = TeacherSubstitutionService()
    s = sub_setup["s1"]
    entry1 = sub_setup["entry1"]
    t_sub = sub_setup["t_sub"]

    # 2026-08-11 is a TUESDAY, but entry1 is MONDAY!
    sub_date = date(2026, 8, 11)
    with pytest.raises(ValidationException, match="does not match the timetable entry day"):
        service.create_substitution(
            db_session,
            TeacherSubstitutionCreate(
                school_id=s.id,
                timetable_entry_id=entry1.id,
                substitution_date=sub_date,
                substitute_teacher_id=t_sub.id,
            ),
            current_school_id=s.id,
        )


def test_same_substitute_as_original_rejected(db_session, sub_setup):
    service = TeacherSubstitutionService()
    s = sub_setup["s1"]
    entry1 = sub_setup["entry1"]
    t_orig = sub_setup["t_orig"]

    sub_date = date(2026, 8, 10)
    with pytest.raises(ValidationException, match="Substitute teacher cannot be the same as the original teacher"):
        service.create_substitution(
            db_session,
            TeacherSubstitutionCreate(
                school_id=s.id,
                timetable_entry_id=entry1.id,
                substitution_date=sub_date,
                substitute_teacher_id=t_orig.id,
            ),
            current_school_id=s.id,
        )


def test_substitute_regular_schedule_double_booking_rejected(db_session, sub_setup):
    service = TeacherSubstitutionService()
    s = sub_setup["s1"]
    entry1 = sub_setup["entry1"]
    t_sub2 = sub_setup["t_sub2"]  # t_sub2 already teaches entry2 on Monday Period 1!

    sub_date = date(2026, 8, 10)  # Monday
    with pytest.raises(ValidationException, match="already scheduled to teach another class"):
        service.create_substitution(
            db_session,
            TeacherSubstitutionCreate(
                school_id=s.id,
                timetable_entry_id=entry1.id,
                substitution_date=sub_date,
                substitute_teacher_id=t_sub2.id,
            ),
            current_school_id=s.id,
        )


def test_substitute_double_booking_on_substitution_rejected(db_session, sub_setup):
    service = TeacherSubstitutionService()
    s = sub_setup["s1"]
    entry1 = sub_setup["entry1"]
    entry2 = sub_setup["entry2"]
    t_sub = sub_setup["t_sub"]

    sub_date = date(2026, 8, 10)

    # Assign Bob to substitute entry1 on Monday Period 1
    service.create_substitution(
        db_session,
        TeacherSubstitutionCreate(
            school_id=s.id,
            timetable_entry_id=entry1.id,
            substitution_date=sub_date,
            substitute_teacher_id=t_sub.id,
        ),
        current_school_id=s.id,
    )

    # Assign same Bob to substitute entry2 on same Monday Period 1 must fail
    with pytest.raises(ValidationException, match="already assigned to another substitution"):
        service.create_substitution(
            db_session,
            TeacherSubstitutionCreate(
                school_id=s.id,
                timetable_entry_id=entry2.id,
                substitution_date=sub_date,
                substitute_teacher_id=t_sub.id,
            ),
            current_school_id=s.id,
        )


def test_duplicate_substitution_for_same_slot_rejected(db_session, sub_setup):
    service = TeacherSubstitutionService()
    s = sub_setup["s1"]
    entry1 = sub_setup["entry1"]
    t_sub = sub_setup["t_sub"]

    sub_date = date(2026, 8, 10)
    service.create_substitution(
        db_session,
        TeacherSubstitutionCreate(
            school_id=s.id,
            timetable_entry_id=entry1.id,
            substitution_date=sub_date,
            substitute_teacher_id=t_sub.id,
        ),
        current_school_id=s.id,
    )

    # Second substitution for entry1 on same date must fail
    with pytest.raises(AlreadyExistsException):
        service.create_substitution(
            db_session,
            TeacherSubstitutionCreate(
                school_id=s.id,
                timetable_entry_id=entry1.id,
                substitution_date=sub_date,
                substitute_teacher_id=t_sub.id,
            ),
            current_school_id=s.id,
        )


def test_soft_deleted_substitution_allows_recreation(db_session, sub_setup):
    service = TeacherSubstitutionService()
    s = sub_setup["s1"]
    entry1 = sub_setup["entry1"]
    t_sub = sub_setup["t_sub"]

    sub_date = date(2026, 8, 10)
    sub1 = service.create_substitution(
        db_session,
        TeacherSubstitutionCreate(
            school_id=s.id,
            timetable_entry_id=entry1.id,
            substitution_date=sub_date,
            substitute_teacher_id=t_sub.id,
        ),
        current_school_id=s.id,
    )

    service.delete_substitution(db_session, sub1.id, current_school_id=s.id)

    # Re-creating substitution for same entry + date succeeds after soft delete
    sub2 = service.create_substitution(
        db_session,
        TeacherSubstitutionCreate(
            school_id=s.id,
            timetable_entry_id=entry1.id,
            substitution_date=sub_date,
            substitute_teacher_id=t_sub.id,
        ),
        current_school_id=s.id,
    )
    assert sub2.id != sub1.id


def test_tenant_isolation_substitution(db_session, sub_setup):
    service = TeacherSubstitutionService()
    s1 = sub_setup["s1"]
    s2 = sub_setup["s2"]
    entry1 = sub_setup["entry1"]
    t_sub = sub_setup["t_sub"]

    sub1 = service.create_substitution(
        db_session,
        TeacherSubstitutionCreate(
            school_id=s1.id,
            timetable_entry_id=entry1.id,
            substitution_date=date(2026, 8, 10),
            substitute_teacher_id=t_sub.id,
        ),
        current_school_id=s1.id,
    )

    # s2 cannot read s1's substitution
    with pytest.raises(NotFoundException):
        service.get_substitution(db_session, sub1.id, current_school_id=s2.id)

    # s2 cannot delete s1's substitution
    with pytest.raises(NotFoundException):
        service.delete_substitution(db_session, sub1.id, current_school_id=s2.id)
