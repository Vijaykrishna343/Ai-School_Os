from datetime import date, timedelta
import uuid

import pytest

from app.common.enums.exam import AssessmentType, AttemptType
from app.common.exceptions import (
    AlreadyExistsException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.academic_term.academic_term import AcademicTerm
from app.models.academic_year.academic_year import AcademicYear
from app.models.school.school import School
from app.schemas.academic_term.academic_term import (
    AcademicTermCreate,
    AcademicTermFilter,
    AcademicTermUpdate,
)
from app.schemas.exam.exam import ExamCreate
from app.services.academic_term_service import AcademicTermService
from app.services.exam_service import ExamService


def make_school(name: str, code: str) -> School:
    return School(
        id=uuid.uuid4(),
        name=name,
        code=f"{code}_{uuid.uuid4().hex[:4]}",
        address_line1="100 Term Way",
        city="New Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )


@pytest.fixture
def term_setup_data(db_session):
    school_1 = make_school(f"Term School 1 {uuid.uuid4().hex[:6]}", "TS1")
    school_2 = make_school(f"Term School 2 {uuid.uuid4().hex[:6]}", "TS2")
    db_session.add_all([school_1, school_2])
    db_session.commit()

    ay_1 = AcademicYear(
        school_id=school_1.id,
        name="2026-2027",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    ay_2 = AcademicYear(
        school_id=school_2.id,
        name="2026-2027",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    db_session.add_all([ay_1, ay_2])
    db_session.commit()

    return {
        "school_1": school_1,
        "school_2": school_2,
        "ay_1": ay_1,
        "ay_2": ay_2,
    }


def test_01_create_academic_term_success(db_session, term_setup_data):
    service = AcademicTermService()
    school = term_setup_data["school_1"]
    ay = term_setup_data["ay_1"]

    payload = AcademicTermCreate(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Term 1",
        code="TERM1",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 9, 30),
        display_order=1,
        is_active=True,
    )

    created = service.create_academic_term(db_session, payload, current_school_id=school.id)
    assert created.id is not None
    assert created.name == "Term 1"
    assert created.code == "TERM1"
    assert created.school_id == school.id
    assert created.academic_year_id == ay.id


def test_02_create_academic_term_cross_school_rejection(db_session, term_setup_data):
    service = AcademicTermService()
    school_1 = term_setup_data["school_1"]
    school_2 = term_setup_data["school_2"]
    ay_1 = term_setup_data["ay_1"]

    payload = AcademicTermCreate(
        school_id=school_1.id,
        academic_year_id=ay_1.id,
        name="Term 1",
        code="TERM1",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 9, 30),
    )

    with pytest.raises(ForbiddenException, match="Cannot create academic term for another school"):
        service.create_academic_term(db_session, payload, current_school_id=school_2.id)


def test_03_create_academic_term_academic_year_school_mismatch(db_session, term_setup_data):
    service = AcademicTermService()
    school_1 = term_setup_data["school_1"]
    ay_2 = term_setup_data["ay_2"]  # Belongs to school_2

    payload = AcademicTermCreate(
        school_id=school_1.id,
        academic_year_id=ay_2.id,
        name="Term 1",
        code="TERM1",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 9, 30),
    )

    with pytest.raises(ValidationException, match="Academic year must belong to the same school"):
        service.create_academic_term(db_session, payload, current_school_id=school_1.id)


def test_04_create_academic_term_start_after_end(db_session, term_setup_data):
    service = AcademicTermService()
    school = term_setup_data["school_1"]
    ay = term_setup_data["ay_1"]

    payload = AcademicTermCreate(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Term Invalid",
        code="INVALID",
        start_date=date(2026, 9, 30),
        end_date=date(2026, 4, 1),
    )

    with pytest.raises(ValidationException, match="start_date must be before or equal to end_date"):
        service.create_academic_term(db_session, payload, current_school_id=school.id)


def test_05_create_academic_term_outside_academic_year_bounds(db_session, term_setup_data):
    service = AcademicTermService()
    school = term_setup_data["school_1"]
    ay = term_setup_data["ay_1"]  # 2026-04-01 to 2027-03-31

    # Start date before AY start date
    payload_1 = AcademicTermCreate(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Term Out",
        code="OUT1",
        start_date=date(2026, 3, 1),
        end_date=date(2026, 9, 30),
    )
    with pytest.raises(ValidationException, match="must fall within academic year boundaries"):
        service.create_academic_term(db_session, payload_1, current_school_id=school.id)

    # End date after AY end date
    payload_2 = AcademicTermCreate(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Term Out 2",
        code="OUT2",
        start_date=date(2026, 10, 1),
        end_date=date(2027, 4, 15),
    )
    with pytest.raises(ValidationException, match="must fall within academic year boundaries"):
        service.create_academic_term(db_session, payload_2, current_school_id=school.id)


def test_06_create_academic_term_duplicate_name_rejection(db_session, term_setup_data):
    service = AcademicTermService()
    school = term_setup_data["school_1"]
    ay = term_setup_data["ay_1"]

    payload = AcademicTermCreate(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Semester 1",
        code="SEM1",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 9, 30),
    )
    service.create_academic_term(db_session, payload, current_school_id=school.id)

    # Duplicate name
    dup_payload = AcademicTermCreate(
        school_id=school.id,
        academic_year_id=ay.id,
        name="semester 1",  # Case insensitive match
        code="SEM1_ALT",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 9, 30),
    )
    with pytest.raises(AlreadyExistsException, match="AcademicTerm name"):
        service.create_academic_term(db_session, dup_payload, current_school_id=school.id)


def test_07_create_academic_term_duplicate_code_rejection(db_session, term_setup_data):
    service = AcademicTermService()
    school = term_setup_data["school_1"]
    ay = term_setup_data["ay_1"]

    payload = AcademicTermCreate(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Trimester 1",
        code="TRI1",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 7, 31),
    )
    service.create_academic_term(db_session, payload, current_school_id=school.id)

    # Duplicate code
    dup_payload = AcademicTermCreate(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Trimester One",
        code="tri1",  # Case insensitive match
        start_date=date(2026, 4, 1),
        end_date=date(2026, 7, 31),
    )
    with pytest.raises(AlreadyExistsException, match="AcademicTerm code"):
        service.create_academic_term(db_session, dup_payload, current_school_id=school.id)


def test_08_get_academic_term_success_and_not_found(db_session, term_setup_data):
    service = AcademicTermService()
    school = term_setup_data["school_1"]
    ay = term_setup_data["ay_1"]

    payload = AcademicTermCreate(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Term Test Get",
        code="TGET",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 9, 30),
    )
    created = service.create_academic_term(db_session, payload, current_school_id=school.id)

    retrieved = service.get_academic_term(db_session, created.id, current_school_id=school.id)
    assert retrieved.id == created.id

    with pytest.raises(NotFoundException):
        service.get_academic_term(db_session, uuid.uuid4(), current_school_id=school.id)


def test_09_update_academic_term_success(db_session, term_setup_data):
    service = AcademicTermService()
    school = term_setup_data["school_1"]
    ay = term_setup_data["ay_1"]

    payload = AcademicTermCreate(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Term Original",
        code="TORIG",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 9, 30),
        display_order=1,
    )
    created = service.create_academic_term(db_session, payload, current_school_id=school.id)

    update_payload = AcademicTermUpdate(
        name="Term Updated",
        code="TUPD",
        display_order=2,
    )
    updated = service.update_academic_term(db_session, created.id, update_payload, current_school_id=school.id)
    assert updated.name == "Term Updated"
    assert updated.code == "TUPD"
    assert updated.display_order == 2


def test_10_update_academic_term_duplicate_rejection(db_session, term_setup_data):
    service = AcademicTermService()
    school = term_setup_data["school_1"]
    ay = term_setup_data["ay_1"]

    t1 = service.create_academic_term(
        db_session,
        AcademicTermCreate(
            school_id=school.id,
            academic_year_id=ay.id,
            name="Term A",
            code="TA",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 9, 30),
        ),
        current_school_id=school.id,
    )
    t2 = service.create_academic_term(
        db_session,
        AcademicTermCreate(
            school_id=school.id,
            academic_year_id=ay.id,
            name="Term B",
            code="TB",
            start_date=date(2026, 10, 1),
            end_date=date(2027, 3, 31),
        ),
        current_school_id=school.id,
    )

    # Attempt to update t2's name to t1's name
    with pytest.raises(AlreadyExistsException, match="AcademicTerm name"):
        service.update_academic_term(
            db_session,
            t2.id,
            AcademicTermUpdate(name="Term A"),
            current_school_id=school.id,
        )


def test_11_delete_academic_term_soft_delete(db_session, term_setup_data):
    service = AcademicTermService()
    school = term_setup_data["school_1"]
    ay = term_setup_data["ay_1"]

    created = service.create_academic_term(
        db_session,
        AcademicTermCreate(
            school_id=school.id,
            academic_year_id=ay.id,
            name="Term Delete",
            code="TDEL",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 9, 30),
        ),
        current_school_id=school.id,
    )

    service.delete_academic_term(db_session, created.id, current_school_id=school.id)

    # Soft deleted item should not be found
    with pytest.raises(NotFoundException):
        service.get_academic_term(db_session, created.id, current_school_id=school.id)

    # Verify soft delete flags
    raw_term = db_session.get(AcademicTerm, created.id)
    assert raw_term.is_deleted is True


def test_12_exam_with_academic_term_validation(db_session, term_setup_data):
    term_service = AcademicTermService()
    exam_service = ExamService()
    school_1 = term_setup_data["school_1"]
    school_2 = term_setup_data["school_2"]
    ay_1 = term_setup_data["ay_1"]
    ay_2 = term_setup_data["ay_2"]

    term = term_service.create_academic_term(
        db_session,
        AcademicTermCreate(
            school_id=school_1.id,
            academic_year_id=ay_1.id,
            name="Term Mid",
            code="TMID",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 9, 30),
        ),
        current_school_id=school_1.id,
    )

    # Valid exam creation with term_id
    exam_payload = ExamCreate(
        school_id=school_1.id,
        academic_year_id=ay_1.id,
        academic_term_id=term.id,
        name="Midterm Exam 2026",
        assessment_type=AssessmentType.TERM,
        attempt_type=AttemptType.REGULAR,
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 10),
    )
    exam = exam_service.create_exam(db_session, exam_payload, current_school_id=school_1.id)
    assert exam.academic_term_id == term.id

    # Invalid: cross-academic-year term assignment
    invalid_exam_payload = ExamCreate(
        school_id=school_2.id,
        academic_year_id=ay_2.id,
        academic_term_id=term.id,  # Belongs to school_1 / ay_1
        name="Cross Term Exam",
        assessment_type=AssessmentType.TERM,
        attempt_type=AttemptType.REGULAR,
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 10),
    )
    with pytest.raises(ValidationException):
        exam_service.create_exam(db_session, invalid_exam_payload, current_school_id=school_2.id)
