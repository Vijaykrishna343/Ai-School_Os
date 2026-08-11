from datetime import date, time
from decimal import Decimal
import uuid

import pytest

from app.common.enums import (
    AcademicYearStatus,
    AssessmentType,
    AttemptType,
    AttendanceStatus,
    CalculationMode,
    Gender,
    ReportCardStatus,
    RetestPolicy,
    RoundingMode,
)
from app.common.exceptions import ValidationException
from app.models.academic_term.academic_term import AcademicTerm
from app.models.academic_year.academic_year import AcademicYear
from app.models.attendance.attendance import Attendance
from app.models.exam.exam import Exam
from app.models.exam.exam_schedule import ExamSchedule
from app.models.exam.student_exam_result import StudentExamResult
from app.models.grading.assessment_type_weightage import AssessmentTypeWeightage
from app.models.grading.evaluation_config import EvaluationConfig
from app.models.grading.grade_scale import GradeScale
from app.models.grading.grade_scale_entry import GradeScaleEntry
from app.models.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.subject.subject import Subject
from app.schemas.grading.report_card import ReportCardGenerateRequest
from app.services.report_card_service import report_card_service


def test_generate_and_finalize_report_card(db_session):
    # Setup domain hierarchy
    school = School(
        name="RC School",
        code=f"SCH-{uuid.uuid4().hex[:6]}",
        address_line1="100 RC St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db_session.add(school)
    db_session.flush()

    ay = AcademicYear(
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    db_session.add(ay)
    db_session.flush()

    term = AcademicTerm(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Term 1",
        code="T1",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 10, 31),
    )
    db_session.add(term)

    school_class = SchoolClass(school_id=school.id, name="Class 10", display_order=1)
    db_session.add(school_class)
    db_session.flush()

    section = Section(school_class_id=school_class.id, name="Section A")
    db_session.add(section)
    db_session.flush()

    parent = Parent(
        school_id=school.id,
        father_name="John Doe",
        primary_phone="9999999999",
        email=f"parent_{uuid.uuid4().hex[:6]}@example.com",
        address_line1="100 Parent St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db_session.add(parent)
    db_session.flush()

    student = Student(
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=school_class.id,
        section_id=section.id,
        parent_id=parent.id,
        admission_number=f"ADM-{uuid.uuid4().hex[:6]}",
        roll_number="1",
        first_name="Jane",
        last_name="Doe",
        gender=Gender.FEMALE,
        date_of_birth=date(2010, 1, 1),
        admission_date=date(2026, 6, 1),
        address_line1="100 Student St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db_session.add(student)

    subject = Subject(
        school_id=school.id,
        subject_name="Mathematics",
        subject_code="MATH10",
    )
    db_session.add(subject)
    db_session.flush()

    # Attendance
    att = Attendance(
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=school_class.id,
        section_id=section.id,
        student_id=student.id,
        attendance_date=date(2026, 7, 1),
        status=AttendanceStatus.PRESENT,
    )
    db_session.add(att)

    # Grade scale
    gs = GradeScale(school_id=school.id, name="Standard Scale", is_default=True)
    db_session.add(gs)
    db_session.flush()

    g1 = GradeScaleEntry(
        grade_scale_id=gs.id,
        grade_code="A",
        min_percentage=Decimal("80.00"),
        max_percentage=Decimal("100.00"),
        grade_point=Decimal("10.00"),
        is_pass=True,
    )
    g2 = GradeScaleEntry(
        grade_scale_id=gs.id,
        grade_code="B",
        min_percentage=Decimal("0.00"),
        max_percentage=Decimal("79.99"),
        grade_point=Decimal("7.00"),
        is_pass=True,
    )
    db_session.add_all([g1, g2])

    # Exam & Schedule
    exam = Exam(
        school_id=school.id,
        academic_year_id=ay.id,
        academic_term_id=term.id,
        name="Mid Term Exam",
        assessment_type=AssessmentType.TERM,
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 10),
    )
    db_session.add(exam)
    db_session.flush()

    sch = ExamSchedule(
        exam_id=exam.id,
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=school_class.id,
        section_id=section.id,
        subject_id=subject.id,
        exam_date=date(2026, 8, 5),
        start_time=time(9, 0),
        end_time=time(12, 0),
        maximum_marks=Decimal("100.00"),
        passing_marks=Decimal("40.00"),
    )
    db_session.add(sch)
    db_session.flush()

    res = StudentExamResult(
        exam_schedule_id=sch.id,
        student_id=student.id,
        marks_obtained=Decimal("85.00"),
    )
    db_session.add(res)
    db_session.flush()

    # Generate Report Card
    req = ReportCardGenerateRequest(
        school_id=school.id,
        academic_year_id=ay.id,
        academic_term_id=term.id,
        student_id=student.id,
    )
    cards = report_card_service.generate_report_cards(db_session, req, current_school_id=school.id)

    assert len(cards) == 1
    card = cards[0]
    assert card.total_obtained_marks == Decimal("85.00")
    assert card.overall_grade == "A"
    assert card.status == ReportCardStatus.DRAFT
    assert len(card.items) == 1
    assert card.items[0].subject_name == "Mathematics"

    # Finalize Report Card
    user_id = uuid.uuid4()
    finalized = report_card_service.finalize_report_card(
        db_session, card.id, current_user_id=user_id, current_school_id=school.id
    )
    assert finalized.status == ReportCardStatus.FINALIZED
    assert finalized.finalized_by_user_id == user_id

    # Regeneration attempt on finalized card should raise ValidationException
    with pytest.raises(ValidationException):
        report_card_service.generate_report_cards(db_session, req, current_school_id=school.id)


def test_weighted_assessment_type_calculation(db_session):
    school = School(
        name="Weighted School",
        code=f"SCH-{uuid.uuid4().hex[:6]}",
        address_line1="100 W St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db_session.add(school)
    db_session.flush()

    ay = AcademicYear(
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    db_session.add(ay)
    db_session.flush()

    school_class = SchoolClass(school_id=school.id, name="Class 10", display_order=1)
    db_session.add(school_class)
    db_session.flush()

    section = Section(school_class_id=school_class.id, name="Section A")
    db_session.add(section)
    db_session.flush()

    parent = Parent(
        school_id=school.id,
        father_name="John Doe",
        primary_phone="9999999999",
        email=f"parent_{uuid.uuid4().hex[:6]}@example.com",
        address_line1="100 Parent St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db_session.add(parent)
    db_session.flush()

    student = Student(
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=school_class.id,
        section_id=section.id,
        parent_id=parent.id,
        admission_number=f"ADM-{uuid.uuid4().hex[:6]}",
        roll_number="1",
        first_name="Alice",
        last_name="Smith",
        gender=Gender.FEMALE,
        date_of_birth=date(2010, 1, 1),
        admission_date=date(2026, 6, 1),
        address_line1="100 Student St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db_session.add(student)

    subject = Subject(
        school_id=school.id,
        subject_name="Physics",
        subject_code="PHY10",
    )
    db_session.add(subject)
    db_session.flush()

    # Evaluation Config with WEIGHTED_ASSESSMENT_TYPE: Formative=20%, Summative=80%
    eval_config = EvaluationConfig(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Weighted Config",
        calculation_mode=CalculationMode.WEIGHTED_ASSESSMENT_TYPE,
        is_default=True,
    )
    db_session.add(eval_config)
    db_session.flush()

    w1 = AssessmentTypeWeightage(
        evaluation_config_id=eval_config.id,
        assessment_type=AssessmentType.FORMATIVE_ASSESSMENT,
        weightage_percentage=Decimal("20.00"),
    )
    w2 = AssessmentTypeWeightage(
        evaluation_config_id=eval_config.id,
        assessment_type=AssessmentType.SUMMATIVE_ASSESSMENT,
        weightage_percentage=Decimal("80.00"),
    )
    db_session.add_all([w1, w2])

    gs = GradeScale(school_id=school.id, name="Grade Scale", is_default=True)
    db_session.add(gs)
    db_session.flush()
    db_session.add(
        GradeScaleEntry(
            grade_scale_id=gs.id,
            grade_code="A",
            min_percentage=Decimal("0.00"),
            max_percentage=Decimal("100.00"),
            grade_point=Decimal("10.00"),
            is_pass=True,
        )
    )

    # Formative Exam: 18/20 = 90%
    ex_formative = Exam(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Formative 1",
        assessment_type=AssessmentType.FORMATIVE_ASSESSMENT,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 5),
    )
    db_session.add(ex_formative)
    db_session.flush()

    sch_f = ExamSchedule(
        exam_id=ex_formative.id,
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=school_class.id,
        section_id=section.id,
        subject_id=subject.id,
        exam_date=date(2026, 7, 2),
        start_time=time(9, 0),
        end_time=time(10, 0),
        maximum_marks=Decimal("20.00"),
        passing_marks=Decimal("8.00"),
    )
    db_session.add(sch_f)
    db_session.flush()

    db_session.add(
        StudentExamResult(
            exam_schedule_id=sch_f.id,
            student_id=student.id,
            marks_obtained=Decimal("18.00"),
        )
    )

    # Summative Exam: 70/100 = 70%
    ex_summative = Exam(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Summative 1",
        assessment_type=AssessmentType.SUMMATIVE_ASSESSMENT,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 10),
    )
    db_session.add(ex_summative)
    db_session.flush()

    sch_s = ExamSchedule(
        exam_id=ex_summative.id,
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=school_class.id,
        section_id=section.id,
        subject_id=subject.id,
        exam_date=date(2026, 9, 5),
        start_time=time(9, 0),
        end_time=time(12, 0),
        maximum_marks=Decimal("100.00"),
        passing_marks=Decimal("40.00"),
    )
    db_session.add(sch_s)
    db_session.flush()

    db_session.add(
        StudentExamResult(
            exam_schedule_id=sch_s.id,
            student_id=student.id,
            marks_obtained=Decimal("70.00"),
        )
    )
    db_session.flush()

    # Generate report card
    req = ReportCardGenerateRequest(
        school_id=school.id,
        academic_year_id=ay.id,
        student_id=student.id,
    )
    cards = report_card_service.generate_report_cards(db_session, req, current_school_id=school.id)
    assert len(cards) == 1
    card = cards[0]

    # Weighted score: 90*0.20 + 70*0.80 = 18 + 56 = 74.00%
    assert card.items[0].percentage == Decimal("74.00")
    assert card.percentage == Decimal("74.00")


def test_weighted_assessment_type_invalid_weightages_rejected(db_session):
    school = School(
        name="Invalid Weight School",
        code=f"SCH-{uuid.uuid4().hex[:6]}",
        address_line1="100 W St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db_session.add(school)
    db_session.flush()

    ay = AcademicYear(
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    db_session.add(ay)
    db_session.flush()

    school_class = SchoolClass(school_id=school.id, name="Class 10", display_order=1)
    db_session.add(school_class)
    db_session.flush()

    section = Section(school_class_id=school_class.id, name="Section A")
    db_session.add(section)
    db_session.flush()

    parent = Parent(
        school_id=school.id,
        father_name="John Doe",
        primary_phone="9999999999",
        email=f"parent_{uuid.uuid4().hex[:6]}@example.com",
        address_line1="100 Parent St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db_session.add(parent)
    db_session.flush()

    student = Student(
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=school_class.id,
        section_id=section.id,
        parent_id=parent.id,
        admission_number=f"ADM-{uuid.uuid4().hex[:6]}",
        roll_number="1",
        first_name="Bob",
        last_name="Jones",
        gender=Gender.MALE,
        date_of_birth=date(2010, 1, 1),
        admission_date=date(2026, 6, 1),
        address_line1="100 Student St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db_session.add(student)

    # Invalid Weightage: 50% only (sum != 100%)
    eval_config = EvaluationConfig(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Bad Weight Config",
        calculation_mode=CalculationMode.WEIGHTED_ASSESSMENT_TYPE,
        is_default=True,
    )
    db_session.add(eval_config)
    db_session.flush()

    w1 = AssessmentTypeWeightage(
        evaluation_config_id=eval_config.id,
        assessment_type=AssessmentType.FORMATIVE_ASSESSMENT,
        weightage_percentage=Decimal("50.00"),
    )
    db_session.add(w1)

    gs = GradeScale(school_id=school.id, name="Grade Scale", is_default=True)
    db_session.add(gs)
    db_session.flush()

    req = ReportCardGenerateRequest(
        school_id=school.id,
        academic_year_id=ay.id,
        student_id=student.id,
    )
    with pytest.raises(ValidationException):
        report_card_service.generate_report_cards(db_session, req, current_school_id=school.id)


def test_rounding_modes(db_session):
    calc_service = report_card_service.calculation_service

    class DummyScaleEntry:
        min_percentage = Decimal("0.00")
        max_percentage = Decimal("100.00")
        grade_code = "A"
        grade_point = Decimal("10.00")
        is_pass = True
        is_deleted = False

    class DummyGradeScale:
        entries = [DummyScaleEntry()]

    class DummyEvalConfig:
        calculation_mode = CalculationMode.SIMPLE_TOTAL
        retest_policy = RetestPolicy.REPLACE_ORIGINAL
        gpa_enabled = False
        weightages = []

    class DummySubject:
        subject_name = "Math"
        subject_code = "M10"

    class DummyExam:
        assessment_type = AssessmentType.OTHER
        is_deleted = False

    class DummySchedule:
        id = uuid.uuid4()
        section_id = uuid.uuid4()
        subject_id = uuid.uuid4()
        subject = DummySubject()
        maximum_marks = Decimal("100.00")
        exam = DummyExam()

    class DummyResult:
        exam_schedule_id = DummySchedule.id
        marks_obtained = Decimal("74.555")

    class DummyStudent:
        id = uuid.uuid4()
        school_id = uuid.uuid4()
        section_id = DummySchedule.section_id

    class DummyYear:
        id = uuid.uuid4()

    pre_results = {(DummyStudent.id, DummySchedule.id): [DummyResult()]}
    pre_att = {"total_working_days": 10, "present_days": 10, "attendance_percentage": Decimal("100.00")}

    # Test ROUND_HALF_UP (74.555 -> 74.56)
    cfg_half_up = DummyEvalConfig()
    cfg_half_up.rounding_mode = RoundingMode.ROUND_HALF_UP
    res_half_up = calc_service.calculate_student_evaluation(
        db_session, DummyStudent(), DummyYear(), None, DummyGradeScale(), cfg_half_up,
        preloaded_schedules=[DummySchedule()], preloaded_results=pre_results, preloaded_att_summary=pre_att
    )
    assert res_half_up["items"][0]["percentage"] == Decimal("74.56")

    # Test ROUND_FLOOR (74.555 -> 74.55)
    cfg_floor = DummyEvalConfig()
    cfg_floor.rounding_mode = RoundingMode.ROUND_FLOOR
    res_floor = calc_service.calculate_student_evaluation(
        db_session, DummyStudent(), DummyYear(), None, DummyGradeScale(), cfg_floor,
        preloaded_schedules=[DummySchedule()], preloaded_results=pre_results, preloaded_att_summary=pre_att
    )
    assert res_floor["items"][0]["percentage"] == Decimal("74.55")

    # Test ROUND_CEIL (74.551 -> 74.56)
    DummyResult.marks_obtained = Decimal("74.551")
    cfg_ceiling = DummyEvalConfig()
    cfg_ceiling.rounding_mode = RoundingMode.ROUND_CEIL
    res_ceiling = calc_service.calculate_student_evaluation(
        db_session, DummyStudent(), DummyYear(), None, DummyGradeScale(), cfg_ceiling,
        preloaded_schedules=[DummySchedule()], preloaded_results=pre_results, preloaded_att_summary=pre_att
    )
    assert res_ceiling["items"][0]["percentage"] == Decimal("74.56")


def test_bulk_report_card_generation_batching(db_session):
    school = School(
        name="Bulk School",
        code=f"SCH-{uuid.uuid4().hex[:6]}",
        address_line1="100 Bulk St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db_session.add(school)
    db_session.flush()

    ay = AcademicYear(
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    db_session.add(ay)
    db_session.flush()

    school_class = SchoolClass(school_id=school.id, name="Class 10", display_order=1)
    db_session.add(school_class)
    db_session.flush()

    section = Section(school_class_id=school_class.id, name="Section A")
    db_session.add(section)
    db_session.flush()

    parent = Parent(
        school_id=school.id,
        father_name="John Doe",
        primary_phone="9999999999",
        email=f"parent_{uuid.uuid4().hex[:6]}@example.com",
        address_line1="100 Parent St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db_session.add(parent)
    db_session.flush()

    # Create 3 students
    students = []
    for i in range(3):
        st = Student(
            school_id=school.id,
            academic_year_id=ay.id,
            school_class_id=school_class.id,
            section_id=section.id,
            parent_id=parent.id,
            admission_number=f"ADM-{uuid.uuid4().hex[:6]}",
            roll_number=str(i + 1),
            first_name=f"Student{i}",
            last_name="Test",
            gender=Gender.MALE,
            date_of_birth=date(2010, 1, 1),
            admission_date=date(2026, 6, 1),
            address_line1="100 Student St",
            city="Delhi",
            district="Central",
            state="Delhi",
            country="India",
            postal_code="110001",
        )
        db_session.add(st)
        students.append(st)

    subject = Subject(
        school_id=school.id,
        subject_name="English",
        subject_code="ENG10",
    )
    db_session.add(subject)
    db_session.flush()

    gs = GradeScale(school_id=school.id, name="Grade Scale", is_default=True)
    db_session.add(gs)
    db_session.flush()
    db_session.add(
        GradeScaleEntry(
            grade_scale_id=gs.id,
            grade_code="A",
            min_percentage=Decimal("0.00"),
            max_percentage=Decimal("100.00"),
            grade_point=Decimal("10.00"),
            is_pass=True,
        )
    )

    eval_config = EvaluationConfig(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Default Config",
        is_default=True,
    )
    db_session.add(eval_config)
    db_session.flush()

    exam = Exam(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Unit Test 1",
        assessment_type=AssessmentType.UNIT_TEST,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 5),
    )
    db_session.add(exam)
    db_session.flush()

    sch = ExamSchedule(
        exam_id=exam.id,
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=school_class.id,
        section_id=section.id,
        subject_id=subject.id,
        exam_date=date(2026, 7, 2),
        start_time=time(9, 0),
        end_time=time(10, 0),
        maximum_marks=Decimal("50.00"),
        passing_marks=Decimal("20.00"),
    )
    db_session.add(sch)
    db_session.flush()

    for st in students:
        db_session.add(
            StudentExamResult(
                exam_schedule_id=sch.id,
                student_id=st.id,
                marks_obtained=Decimal("40.00"),
            )
        )
    db_session.flush()

    # Section bulk generation request
    req = ReportCardGenerateRequest(
        school_id=school.id,
        academic_year_id=ay.id,
        section_id=section.id,
    )
    cards = report_card_service.generate_report_cards(db_session, req, current_school_id=school.id)

    assert len(cards) == 3
    for card in cards:
        assert card.total_obtained_marks == Decimal("40.00")
        assert card.total_max_marks == Decimal("50.00")
        assert card.percentage == Decimal("80.00")

