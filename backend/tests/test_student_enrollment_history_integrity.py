from datetime import date
import uuid

import pytest
from unittest.mock import MagicMock

from app.common.enums import EnrollmentStatus, PromotionDecision, StudentStatus, Gender
from app.models.academic_year.academic_year import AcademicYear
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.schemas.student.student_schema import StudentCreate
from app.services.student.student_service import StudentService
from app.repositories.student import student_repository, student_enrollment_history_repository
from app.repositories.school import school_repository
from app.repositories.parent import parent_repository
from app.repositories.academic_year import academic_year_repository
from app.repositories.school_class import school_class_repository
from app.repositories.section import section_repository


def make_school(name: str, code: str) -> School:
    return School(
        id=uuid.uuid4(),
        name=name,
        code=f"{code}_{uuid.uuid4().hex[:4]}",
        address_line1="100 History Way",
        city="New Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )


@pytest.fixture
def setup_enrollment_test(db_session):
    s1 = make_school("History School 1", "HS1")
    s2 = make_school("History School 2", "HS2")
    db_session.add_all([s1, s2])
    db_session.commit()

    ay1 = AcademicYear(school_id=s1.id, name="2026-2027", start_date=date(2026, 4, 1), end_date=date(2027, 3, 31), is_current=True)
    db_session.add(ay1)
    db_session.commit()

    sc1 = SchoolClass(school_id=s1.id, name="Class 1", display_order=1)
    db_session.add(sc1)
    db_session.commit()

    sec1 = Section(school_class_id=sc1.id, name="Section A")
    db_session.add(sec1)
    db_session.commit()

    p1 = Parent(
        school_id=s1.id,
        father_name="John Doe",
        primary_phone=f"98765{uuid.uuid4().hex[:5]}",
        address_line1="100 St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db_session.add(p1)
    db_session.commit()

    return {
        "s1": s1, "s2": s2, "ay1": ay1, "sc1": sc1, "sec1": sec1, "p1": p1,
    }


def test_create_student_generates_initial_enrollment_history(db_session, setup_enrollment_test):
    s1 = setup_enrollment_test["s1"]
    ay1 = setup_enrollment_test["ay1"]
    sc1 = setup_enrollment_test["sc1"]
    sec1 = setup_enrollment_test["sec1"]
    p1 = setup_enrollment_test["p1"]

    service = StudentService(
        repository=student_repository,
        school_repository=school_repository,
        parent_repository=parent_repository,
        academic_year_repository=academic_year_repository,
        school_class_repository=school_class_repository,
        section_repository=section_repository,
        enrollment_history_repository=student_enrollment_history_repository,
    )

    student_data = StudentCreate(
        school_id=s1.id,
        parent_id=p1.id,
        academic_year_id=ay1.id,
        school_class_id=sc1.id,
        section_id=sec1.id,
        first_name="Tommy",
        last_name="Hilfiger",
        gender=Gender.MALE,
        date_of_birth=date(2015, 5, 10),
        admission_date=date(2026, 4, 5),
        address_line1="123 Main St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )

    student_resp = service.create_student(db_session, student_data)
    assert student_resp.id is not None

    histories = student_enrollment_history_repository.get_by_student(db_session, s1.id, student_resp.id)
    assert len(histories) == 1

    h0 = histories[0]
    assert h0.school_id == s1.id
    assert h0.student_id == student_resp.id
    assert h0.academic_year_id == ay1.id
    assert h0.school_class_id == sc1.id
    assert h0.section_id == sec1.id
    assert h0.roll_number == student_resp.roll_number
    assert h0.enrollment_status == EnrollmentStatus.ENROLLED
    assert h0.promotion_decision == PromotionDecision.PENDING
    assert h0.start_date == date(2026, 4, 5)
    assert h0.end_date is None
    assert h0.reason == "Initial Admission"


def test_create_student_rollback_transaction_on_history_failure(db_session, setup_enrollment_test):
    s1 = setup_enrollment_test["s1"]
    ay1 = setup_enrollment_test["ay1"]
    sc1 = setup_enrollment_test["sc1"]
    sec1 = setup_enrollment_test["sec1"]
    p1 = setup_enrollment_test["p1"]

    mock_history_repo = MagicMock()
    mock_history_repo.create.side_effect = Exception("Simulated history insertion database crash")

    service = StudentService(
        repository=student_repository,
        school_repository=school_repository,
        parent_repository=parent_repository,
        academic_year_repository=academic_year_repository,
        school_class_repository=school_class_repository,
        section_repository=section_repository,
        enrollment_history_repository=mock_history_repo,
    )

    student_data = StudentCreate(
        school_id=s1.id,
        parent_id=p1.id,
        academic_year_id=ay1.id,
        school_class_id=sc1.id,
        section_id=sec1.id,
        first_name="Fail",
        last_name="Test",
        gender=Gender.FEMALE,
        date_of_birth=date(2016, 1, 1),
        admission_date=date(2026, 4, 5),
        address_line1="123 Main St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )

    with pytest.raises(Exception, match="Simulated history insertion database crash"):
        service.create_student(db_session, student_data)

    # Verify student record was rolled back and does not exist in DB
    student_in_db = student_repository.get_last_admission_number(db_session)
    if student_in_db:
        assert student_in_db.first_name != "Fail"
