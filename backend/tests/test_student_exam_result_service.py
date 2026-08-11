import uuid
from datetime import date, time
from decimal import Decimal

import pytest

from app.common.enums import Gender, StudentStatus
from app.common.enums.exam import AssessmentType, AttemptType, ExamStatus
from app.common.enums.parent import ParentRelationship
from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from app.models.academic_year.academic_year import AcademicYear
from app.models.exam.exam import Exam
from app.models.exam.exam_schedule import ExamSchedule
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.schemas.exam.student_exam_result import (
    StudentExamResultCreate,
    StudentExamResultUpdate,
)
from app.services.student_exam_result_service import (
    student_exam_result_service,
)


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
    db.commit()
    db.refresh(sc)
    db.refresh(sec)
    return sc, sec


def create_test_parent(db, school_id):
    parent = Parent(
        id=uuid.uuid4(),
        school_id=school_id,
        father_name="Parent User",
        primary_phone=f"9{uuid.uuid4().int % 1000000009:09d}",
        relationship=ParentRelationship.FATHER,
        address_line1="100 Main St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent


def create_test_student(
    db,
    school_id,
    academic_year_id,
    school_class_id,
    section_id,
    parent_id,
    status=StudentStatus.ACTIVE,
):
    student = Student(
        id=uuid.uuid4(),
        school_id=school_id,
        academic_year_id=academic_year_id,
        school_class_id=school_class_id,
        section_id=section_id,
        parent_id=parent_id,
        admission_number=f"ADM_{uuid.uuid4().hex[:6]}",
        roll_number=f"R_{uuid.uuid4().hex[:4]}",
        first_name="Test",
        last_name="Student",
        gender=Gender.MALE,
        date_of_birth=date(2012, 1, 1),
        admission_date=date(2026, 4, 1),
        address_line1="100 Student St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
        status=status,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def create_test_exam_and_schedule(
    db, school_id, academic_year_id, school_class_id, section_id, max_marks="100.00"
):
    exam = Exam(
        id=uuid.uuid4(),
        school_id=school_id,
        academic_year_id=academic_year_id,
        name=f"Exam_{uuid.uuid4().hex[:6]}",
        assessment_type=AssessmentType.TERM,
        attempt_type=AttemptType.REGULAR,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 20),
        status=ExamStatus.DRAFT,
    )
    db.add(exam)
    db.commit()

    schedule = ExamSchedule(
        id=uuid.uuid4(),
        exam_id=exam.id,
        school_id=school_id,
        academic_year_id=academic_year_id,
        school_class_id=school_class_id,
        section_id=section_id,
        subject_id=uuid.uuid4(),
        exam_date=date(2026, 10, 5),
        start_time=time(9, 0),
        end_time=time(11, 0),
        maximum_marks=Decimal(max_marks),
        passing_marks=Decimal("35.00"),
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return exam, schedule


def test_create_student_exam_result_success(db_session):
    db = db_session
    school = create_test_school(db)
    ay = create_test_academic_year(db, school.id)
    sc, sec = create_test_class_section_subject(db, school.id)
    parent = create_test_parent(db, school.id)
    student = create_test_student(db, school.id, ay.id, sc.id, sec.id, parent.id)
    exam, schedule = create_test_exam_and_schedule(db, school.id, ay.id, sc.id, sec.id)

    payload = StudentExamResultCreate(
        exam_schedule_id=schedule.id,
        student_id=student.id,
        marks_obtained=Decimal("85.50"),
        remarks="Excellent performance",
    )

    result = student_exam_result_service.create_student_exam_result(
        db, payload, current_school_id=school.id
    )
    assert result.id is not None
    assert result.marks_obtained == Decimal("85.50")
    assert result.remarks == "Excellent performance"


def test_create_student_exam_result_user_without_school(db_session):
    db = db_session
    payload = StudentExamResultCreate(
        exam_schedule_id=uuid.uuid4(),
        student_id=uuid.uuid4(),
        marks_obtained=Decimal("50.00"),
    )
    with pytest.raises(ValidationException, match="Authenticated user is not associated with a school"):
        student_exam_result_service.create_student_exam_result(
            db, payload, current_school_id=None
        )


def test_create_student_exam_result_missing_schedule(db_session):
    db = db_session
    school = create_test_school(db)
    ay = create_test_academic_year(db, school.id)
    sc, sec = create_test_class_section_subject(db, school.id)
    parent = create_test_parent(db, school.id)
    student = create_test_student(db, school.id, ay.id, sc.id, sec.id, parent.id)

    payload = StudentExamResultCreate(
        exam_schedule_id=uuid.uuid4(),
        student_id=student.id,
        marks_obtained=Decimal("50.00"),
    )
    with pytest.raises(NotFoundException, match="ExamSchedule"):
        student_exam_result_service.create_student_exam_result(
            db, payload, current_school_id=school.id
        )


def test_create_student_exam_result_cross_school_schedule(db_session):
    db = db_session
    school1 = create_test_school(db, "School 1", "SCH1")
    school2 = create_test_school(db, "School 2", "SCH2")

    ay1 = create_test_academic_year(db, school1.id)
    sc1, sec1 = create_test_class_section_subject(db, school1.id)
    parent1 = create_test_parent(db, school1.id)
    student1 = create_test_student(db, school1.id, ay1.id, sc1.id, sec1.id, parent1.id)

    ay2 = create_test_academic_year(db, school2.id)
    sc2, sec2 = create_test_class_section_subject(db, school2.id)
    exam2, schedule2 = create_test_exam_and_schedule(db, school2.id, ay2.id, sc2.id, sec2.id)

    payload = StudentExamResultCreate(
        exam_schedule_id=schedule2.id,
        student_id=student1.id,
        marks_obtained=Decimal("50.00"),
    )
    with pytest.raises(ValidationException, match="Exam schedule must belong to the user's school"):
        student_exam_result_service.create_student_exam_result(
            db, payload, current_school_id=school1.id
        )


def test_create_student_exam_result_cross_school_student(db_session):
    db = db_session
    school1 = create_test_school(db, "School 1", "SCH1")
    school2 = create_test_school(db, "School 2", "SCH2")

    ay1 = create_test_academic_year(db, school1.id)
    sc1, sec1 = create_test_class_section_subject(db, school1.id)
    exam1, schedule1 = create_test_exam_and_schedule(db, school1.id, ay1.id, sc1.id, sec1.id)

    ay2 = create_test_academic_year(db, school2.id)
    sc2, sec2 = create_test_class_section_subject(db, school2.id)
    parent2 = create_test_parent(db, school2.id)
    student2 = create_test_student(db, school2.id, ay2.id, sc2.id, sec2.id, parent2.id)

    payload = StudentExamResultCreate(
        exam_schedule_id=schedule1.id,
        student_id=student2.id,
        marks_obtained=Decimal("50.00"),
    )
    with pytest.raises(ValidationException, match="Student must belong to the user's school"):
        student_exam_result_service.create_student_exam_result(
            db, payload, current_school_id=school1.id
        )


def test_create_student_exam_result_inactive_student(db_session):
    db = db_session
    school = create_test_school(db)
    ay = create_test_academic_year(db, school.id)
    sc, sec = create_test_class_section_subject(db, school.id)
    parent = create_test_parent(db, school.id)
    student = create_test_student(
        db, school.id, ay.id, sc.id, sec.id, parent.id, status=StudentStatus.INACTIVE
    )
    exam, schedule = create_test_exam_and_schedule(db, school.id, ay.id, sc.id, sec.id)

    payload = StudentExamResultCreate(
        exam_schedule_id=schedule.id,
        student_id=student.id,
        marks_obtained=Decimal("50.00"),
    )
    with pytest.raises(ValidationException, match="inactive student"):
        student_exam_result_service.create_student_exam_result(
            db, payload, current_school_id=school.id
        )


def test_create_student_exam_result_mismatches(db_session):
    db = db_session
    school = create_test_school(db)
    ay1 = create_test_academic_year(db, school.id, "AY1")
    ay2 = create_test_academic_year(db, school.id, "AY2")

    sc1, sec1 = create_test_class_section_subject(db, school.id)
    sc2, sec2 = create_test_class_section_subject(db, school.id)
    parent = create_test_parent(db, school.id)

    exam, schedule = create_test_exam_and_schedule(db, school.id, ay1.id, sc1.id, sec1.id)

    # Academic Year mismatch
    student_ay_mismatch = create_test_student(db, school.id, ay2.id, sc1.id, sec1.id, parent.id)
    payload = StudentExamResultCreate(
        exam_schedule_id=schedule.id,
        student_id=student_ay_mismatch.id,
        marks_obtained=Decimal("50.00"),
    )
    with pytest.raises(ValidationException, match="academic year"):
        student_exam_result_service.create_student_exam_result(
            db, payload, current_school_id=school.id
        )

    # Class mismatch
    student_class_mismatch = create_test_student(db, school.id, ay1.id, sc2.id, sec2.id, parent.id)
    payload = StudentExamResultCreate(
        exam_schedule_id=schedule.id,
        student_id=student_class_mismatch.id,
        marks_obtained=Decimal("50.00"),
    )
    with pytest.raises(ValidationException, match="class"):
        student_exam_result_service.create_student_exam_result(
            db, payload, current_school_id=school.id
        )

    # Section mismatch (same class sc1, but sec2)
    sec_other = Section(id=uuid.uuid4(), school_class_id=sc1.id, name="Section B")
    db.add(sec_other)
    db.commit()
    student_sec_mismatch = create_test_student(db, school.id, ay1.id, sc1.id, sec_other.id, parent.id)
    payload = StudentExamResultCreate(
        exam_schedule_id=schedule.id,
        student_id=student_sec_mismatch.id,
        marks_obtained=Decimal("50.00"),
    )
    with pytest.raises(ValidationException, match="section"):
        student_exam_result_service.create_student_exam_result(
            db, payload, current_school_id=school.id
        )


def test_create_student_exam_result_marks_validations(db_session):
    db = db_session
    school = create_test_school(db)
    ay = create_test_academic_year(db, school.id)
    sc, sec = create_test_class_section_subject(db, school.id)
    parent = create_test_parent(db, school.id)
    student = create_test_student(db, school.id, ay.id, sc.id, sec.id, parent.id)
    exam, schedule = create_test_exam_and_schedule(
        db, school.id, ay.id, sc.id, sec.id, max_marks="100.00"
    )

    # Marks > maximum_marks
    payload_exceed = StudentExamResultCreate(
        exam_schedule_id=schedule.id,
        student_id=student.id,
        marks_obtained=Decimal("105.00"),
    )
    with pytest.raises(ValidationException, match="exceed maximum marks"):
        student_exam_result_service.create_student_exam_result(
            db, payload_exceed, current_school_id=school.id
        )


def test_create_student_exam_result_duplicate_active(db_session):
    db = db_session
    school = create_test_school(db)
    ay = create_test_academic_year(db, school.id)
    sc, sec = create_test_class_section_subject(db, school.id)
    parent = create_test_parent(db, school.id)
    student = create_test_student(db, school.id, ay.id, sc.id, sec.id, parent.id)
    exam, schedule = create_test_exam_and_schedule(db, school.id, ay.id, sc.id, sec.id)

    payload = StudentExamResultCreate(
        exam_schedule_id=schedule.id,
        student_id=student.id,
        marks_obtained=Decimal("75.00"),
    )
    student_exam_result_service.create_student_exam_result(
        db, payload, current_school_id=school.id
    )

    with pytest.raises(AlreadyExistsException):
        student_exam_result_service.create_student_exam_result(
            db, payload, current_school_id=school.id
        )


def test_update_student_exam_result_service(db_session):
    db = db_session
    school = create_test_school(db)
    ay = create_test_academic_year(db, school.id)
    sc, sec = create_test_class_section_subject(db, school.id)
    parent = create_test_parent(db, school.id)
    student = create_test_student(db, school.id, ay.id, sc.id, sec.id, parent.id)
    exam, schedule = create_test_exam_and_schedule(
        db, school.id, ay.id, sc.id, sec.id, max_marks="100.00"
    )

    payload = StudentExamResultCreate(
        exam_schedule_id=schedule.id,
        student_id=student.id,
        marks_obtained=Decimal("75.00"),
    )
    result = student_exam_result_service.create_student_exam_result(
        db, payload, current_school_id=school.id
    )

    # Valid update
    update_in = StudentExamResultUpdate(
        marks_obtained=Decimal("90.00"), remarks="Revised score"
    )
    updated = student_exam_result_service.update_student_exam_result(
        db, result.id, update_in, school_id=school.id
    )
    assert updated.marks_obtained == Decimal("90.00")
    assert updated.remarks == "Revised score"

    # Invalid update (exceeds max marks)
    invalid_update = StudentExamResultUpdate(marks_obtained=Decimal("150.00"))
    with pytest.raises(ValidationException, match="exceed maximum marks"):
        student_exam_result_service.update_student_exam_result(
            db, result.id, invalid_update, school_id=school.id
        )


def test_soft_delete_and_recreate(db_session):
    db = db_session
    school = create_test_school(db)
    ay = create_test_academic_year(db, school.id)
    sc, sec = create_test_class_section_subject(db, school.id)
    parent = create_test_parent(db, school.id)
    student = create_test_student(db, school.id, ay.id, sc.id, sec.id, parent.id)
    exam, schedule = create_test_exam_and_schedule(db, school.id, ay.id, sc.id, sec.id)

    payload = StudentExamResultCreate(
        exam_schedule_id=schedule.id,
        student_id=student.id,
        marks_obtained=Decimal("70.00"),
    )
    res1 = student_exam_result_service.create_student_exam_result(
        db, payload, current_school_id=school.id
    )
    assert res1.id is not None

    # Soft delete res1
    student_exam_result_service.delete_student_exam_result(
        db, res1.id, school_id=school.id
    )

    # Getting deleted result raises NotFoundException
    with pytest.raises(NotFoundException):
        student_exam_result_service.get_student_exam_result(
            db, res1.id, school_id=school.id
        )

    # Re-creating result for same schedule and student succeeds
    payload2 = StudentExamResultCreate(
        exam_schedule_id=schedule.id,
        student_id=student.id,
        marks_obtained=Decimal("88.00"),
        remarks="Re-evaluated",
    )
    res2 = student_exam_result_service.create_student_exam_result(
        db, payload2, current_school_id=school.id
    )
    assert res2.id is not None
    assert res2.id != res1.id
    assert res2.marks_obtained == Decimal("88.00")


def test_get_by_id_and_school_with_soft_deleted_exam_schedule(db_session):
    db = db_session
    school = create_test_school(db)
    ay = create_test_academic_year(db, school.id)
    sc, sec = create_test_class_section_subject(db, school.id)
    parent = create_test_parent(db, school.id)
    student = create_test_student(db, school.id, ay.id, sc.id, sec.id, parent.id)
    exam, schedule = create_test_exam_and_schedule(db, school.id, ay.id, sc.id, sec.id)

    payload = StudentExamResultCreate(
        exam_schedule_id=schedule.id,
        student_id=student.id,
        marks_obtained=Decimal("75.00"),
    )
    result = student_exam_result_service.create_student_exam_result(
        db, payload, current_school_id=school.id
    )

    # Soft delete the ExamSchedule directly
    schedule.is_deleted = True
    db.commit()

    # Service get_student_exam_result must raise NotFoundException because schedule is soft-deleted
    with pytest.raises(NotFoundException):
        student_exam_result_service.get_student_exam_result(
            db, result.id, school_id=school.id
        )


def test_get_student_exam_results_without_school_id_fails(db_session):
    from app.schemas.exam.student_exam_result import StudentExamResultFilter
    db = db_session
    filters = StudentExamResultFilter()
    with pytest.raises(ValidationException, match="School ID is required for tenant isolation"):
        student_exam_result_service.get_student_exam_results(
            db, filters, school_id=None
        )


