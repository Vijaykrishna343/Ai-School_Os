import uuid
from datetime import date, time
from decimal import Decimal

import pytest

from app.common.enums.exam import AssessmentType, AttemptType, ExamStatus, parse_legacy_exam_type
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
from app.schemas.exam.exam import ExamCreate, ExamFilter, ExamUpdate
from app.schemas.exam.exam_schedule import (
    ExamScheduleCreate,
    ExamScheduleFilter,
    ExamScheduleUpdate,
)
from app.services.exam_schedule_service import exam_schedule_service
from app.services.exam_service import exam_service


def create_test_school(db, name="Service School", code="SSCH"):
    school = School(
        id=uuid.uuid4(),
        name=name,
        code=f"{code}_{uuid.uuid4().hex[:4]}",
        address_line1="10 Exam St",
        city="New Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def create_test_academic_year(db, school_id, name="2026-2027"):
    ay = AcademicYear(
        id=uuid.uuid4(),
        school_id=school_id,
        name=f"{name}_{uuid.uuid4().hex[:4]}",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    db.add(ay)
    db.commit()
    db.refresh(ay)
    return ay


def create_test_class_section_subject(db, school_id):
    sc = SchoolClass(
        id=uuid.uuid4(),
        school_id=school_id,
        name=f"Class_{uuid.uuid4().hex[:4]}",
        display_order=1,
    )
    db.add(sc)
    db.commit()

    sec = Section(
        id=uuid.uuid4(),
        school_class_id=sc.id,
        name="Section A",
    )
    db.add(sec)

    subj = Subject(
        id=uuid.uuid4(),
        school_id=school_id,
        subject_code=f"SUBJ_{uuid.uuid4().hex[:4]}",
        subject_name="Mathematics",
    )
    db.add(subj)
    db.commit()
    db.refresh(sc)
    db.refresh(sec)
    db.refresh(subj)
    return sc, sec, subj


def test_exam_enums_canonical():
    assert len(AssessmentType) == 12
    assert len(AttemptType) == 3
    assert AssessmentType.FORMATIVE_ASSESSMENT.value == "FORMATIVE_ASSESSMENT"
    assert AssessmentType.FINAL.value == "FINAL"
    assert AttemptType.REGULAR.value == "REGULAR"
    assert AttemptType.RETEST.value == "RETEST"
    assert AttemptType.MAKEUP.value == "MAKEUP"
    assert ExamStatus.DRAFT.value == "DRAFT"


def test_legacy_exam_type_parser():
    assert parse_legacy_exam_type("REGULAR") == (AssessmentType.OTHER, AttemptType.REGULAR)
    assert parse_legacy_exam_type("RETEST") == (AssessmentType.OTHER, AttemptType.RETEST)
    assert parse_legacy_exam_type("OTHER") == (AssessmentType.OTHER, AttemptType.REGULAR)

    with pytest.raises(ValueError, match="Invalid legacy exam_type"):
        parse_legacy_exam_type("INVALID_TYPE")


def test_exam_service_create_and_invalid_dates(db_session):
    db = db_session
    school = create_test_school(db, "Service Exam School 1", "SES1")
    ay = create_test_academic_year(db, school.id, "2026-2027")

    invalid_in = ExamCreate(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Invalid Date Exam",
        assessment_type=AssessmentType.UNIT_TEST,
        attempt_type=AttemptType.REGULAR,
        start_date=date(2026, 10, 20),
        end_date=date(2026, 10, 10),
    )
    with pytest.raises(ValidationException):
        exam_service.create_exam(db, invalid_in)

    valid_in = ExamCreate(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Valid Exam 1",
        assessment_type=AssessmentType.UNIT_TEST,
        attempt_type=AttemptType.REGULAR,
        start_date=date(2026, 10, 10),
        end_date=date(2026, 10, 20),
    )
    exam = exam_service.create_exam(db, valid_in)
    assert exam.id is not None
    assert exam.name == "Valid Exam 1"
    assert exam.assessment_type == AssessmentType.UNIT_TEST
    assert exam.attempt_type == AttemptType.REGULAR


def test_all_assessment_and_attempt_types_creation(db_session):
    db = db_session
    school = create_test_school(db, "All Types School", "ATS1")
    ay = create_test_academic_year(db, school.id, "2026-2027")

    for idx, ast in enumerate(AssessmentType):
        for att in AttemptType:
            exam_in = ExamCreate(
                school_id=school.id,
                academic_year_id=ay.id,
                name=f"Exam_{ast.value}_{att.value}_{idx}",
                assessment_type=ast,
                attempt_type=att,
                start_date=date(2026, 10, 1),
                end_date=date(2026, 10, 15),
            )
            exam = exam_service.create_exam(db, exam_in)
            assert exam.assessment_type == ast
            assert exam.attempt_type == att


def test_legacy_exam_type_create_and_update_behavior(db_session):
    db = db_session
    school = create_test_school(db, "Legacy Exam School", "LES1")
    ay = create_test_academic_year(db, school.id, "2026-2027")

    # Create using legacy exam_type="RETEST"
    legacy_create = ExamCreate(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Legacy Retest Exam",
        exam_type="RETEST",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 15),
    )
    exam = exam_service.create_exam(db, legacy_create)
    assert exam.assessment_type == AssessmentType.OTHER
    assert exam.attempt_type == AttemptType.RETEST

    # Update assessment_type to TERM
    up_ast = ExamUpdate(assessment_type=AssessmentType.TERM)
    exam_up = exam_service.update_exam(db, exam.id, up_ast, school_id=school.id)
    assert exam_up.assessment_type == AssessmentType.TERM
    assert exam_up.attempt_type == AttemptType.RETEST

    # Update using legacy exam_type="REGULAR" -> must update attempt_type to REGULAR while PRESERVING assessment_type=TERM
    up_legacy = ExamUpdate(exam_type="REGULAR")
    exam_up2 = exam_service.update_exam(db, exam.id, up_legacy, school_id=school.id)
    assert exam_up2.assessment_type == AssessmentType.TERM
    assert exam_up2.attempt_type == AttemptType.REGULAR


def test_exam_service_duplicate_active_name(db_session):
    db = db_session
    school = create_test_school(db, "Service Exam School 2", "SES2")
    ay = create_test_academic_year(db, school.id, "2026-2027")

    valid_in = ExamCreate(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Unique Name Exam",
        assessment_type=AssessmentType.FINAL,
        attempt_type=AttemptType.REGULAR,
        start_date=date(2026, 10, 10),
        end_date=date(2026, 10, 20),
    )
    exam_service.create_exam(db, valid_in)

    with pytest.raises(AlreadyExistsException):
        exam_service.create_exam(db, valid_in)


def test_exam_service_cross_school_academic_year(db_session):
    db = db_session
    school1 = create_test_school(db, "School A", "SCHA")
    school2 = create_test_school(db, "School B", "SCHB")

    ay2 = create_test_academic_year(db, school2.id, "2026-2027")

    exam_in = ExamCreate(
        school_id=school1.id,
        academic_year_id=ay2.id,
        name="Cross AY Exam",
        assessment_type=AssessmentType.QUARTERLY,
        start_date=date(2026, 10, 10),
        end_date=date(2026, 10, 20),
    )
    with pytest.raises(ValidationException):
        exam_service.create_exam(db, exam_in)


def test_exam_schedule_service_validations(db_session):
    db = db_session
    school = create_test_school(db, "Schedule Service School", "SSS1")
    ay = create_test_academic_year(db, school.id, "2026-2027")
    sc, sec, subj = create_test_class_section_subject(db, school.id)

    exam_in = ExamCreate(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Term 1 Exam",
        assessment_type=AssessmentType.TERM,
        attempt_type=AttemptType.REGULAR,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 15),
    )
    exam = exam_service.create_exam(db, exam_in)

    # Date outside exam start/end range
    sched_out_date = ExamScheduleCreate(
        exam_id=exam.id,
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=sc.id,
        section_id=sec.id,
        subject_id=subj.id,
        exam_date=date(2026, 10, 20),
        start_time=time(9, 0),
        end_time=time(11, 0),
        maximum_marks=Decimal("100.00"),
        passing_marks=Decimal("35.00"),
    )
    with pytest.raises(ValidationException):
        exam_schedule_service.create_exam_schedule(db, sched_out_date)


def test_exam_schedule_section_class_mismatch(db_session):
    db = db_session
    school = create_test_school(db, "Mismatch School", "MIS1")
    ay = create_test_academic_year(db, school.id, "2026-2027")
    sc1, sec1, subj = create_test_class_section_subject(db, school.id)
    sc2, sec2, _ = create_test_class_section_subject(db, school.id)

    exam_in = ExamCreate(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Mismatch Test Exam",
        assessment_type=AssessmentType.PERIODIC_TEST,
        attempt_type=AttemptType.REGULAR,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 15),
    )
    exam = exam_service.create_exam(db, exam_in)

    sched_mismatch = ExamScheduleCreate(
        exam_id=exam.id,
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=sc1.id,
        section_id=sec2.id,
        subject_id=subj.id,
        exam_date=date(2026, 10, 5),
        start_time=time(9, 0),
        end_time=time(11, 0),
        maximum_marks=Decimal("100.00"),
        passing_marks=Decimal("35.00"),
    )
    with pytest.raises(ValidationException):
        exam_schedule_service.create_exam_schedule(db, sched_mismatch)
