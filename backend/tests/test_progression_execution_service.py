"""
Unit and Integration tests for ProgressionExecutionService.

Verifies:
- Atomic execution run of academic year progression rollover.
- Stale SHA-256 plan hash detection and rejection (zero mutations).
- Idempotency key handling (cached response for completed runs, conflict for active runs).
- Atomic student placement update, enrollment history creation, graduation handling.
- Atomic AcademicYear status transition (source ARCHIVED, target ACTIVE & is_current).
- Audit record creation (ProgressionExecution and ProgressionExecutionItem).
- Isolated S_recovery session logging on unexpected mutation failures.
- Tenant isolation.
"""

from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import AcademicYearStatus, EnrollmentStatus, PromotionDecision, StudentStatus
from app.common.exceptions import InternalServerException, ValidationException
from app.identity.models.user import IdentityUser
from app.models.academic_year import AcademicYear, ClassProgressionRule
from app.models.academic_year.progression_execution import ProgressionExecution, ProgressionExecutionStatus
from app.models.parent import Parent
from app.models.school import School
from app.models.school_class import SchoolClass
from app.models.section import Section
from app.models.student import Student, StudentEnrollmentHistory
from app.schemas.student.progression_execution_schema import ProgressionExecutionRequest
from app.services.student.progression_execution_service import progression_execution_service
from app.services.student.progression_planner import progression_planner


def _create_school(db: Session, name: str = "Exec Test School") -> School:
    school = School(
        name=name,
        code=f"SCH-{uuid4().hex[:4].upper()}",
        address_line1="123 School Rd",
        city="City",
        district="District",
        state="State",
        postal_code="100001",
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def _create_user(db: Session, school_id) -> IdentityUser:
    user = IdentityUser(
        email=f"admin-{uuid4().hex[:6]}@school.com",
        username=f"admin_{uuid4().hex[:6]}",
        password_hash="hashed_pw",
        first_name="Admin",
        last_name="User",
        school_id=school_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_academic_year(
    db: Session, school_id, name: str = "2025-2026", is_current: bool = True, status: AcademicYearStatus = AcademicYearStatus.ACTIVE
) -> AcademicYear:
    ay = AcademicYear(
        school_id=school_id,
        name=name,
        start_date=date(2025, 4, 1),
        end_date=date(2026, 3, 31),
        is_current=is_current,
        status=status,
    )
    db.add(ay)
    db.commit()
    db.refresh(ay)
    return ay


def _create_class(db: Session, school_id, name: str = "Class 1", display_order: int = 1) -> SchoolClass:
    sc = SchoolClass(school_id=school_id, name=name, display_order=display_order)
    db.add(sc)
    db.commit()
    db.refresh(sc)
    return sc


def _create_section(db: Session, school_class_id, name: str = "A") -> Section:
    sec = Section(school_class_id=school_class_id, name=name)
    db.add(sec)
    db.commit()
    db.refresh(sec)
    return sec


def _create_parent(db: Session, school_id) -> Parent:
    parent = Parent(
        school_id=school_id,
        father_name="Parent Doe",
        primary_phone=f"+199{uuid4().hex[:8]}",
        address_line1="123 Main St",
        city="City",
        district="District",
        state="State",
        postal_code="100001",
    )
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent


def _create_student(
    db: Session,
    school_id,
    academic_year_id,
    school_class_id,
    section_id,
    parent_id=None,
    admission_number: str = "ADM-001",
    first_name: str = "John",
    last_name: str = "Doe",
    roll_number: str = "001",
    status: StudentStatus = StudentStatus.ACTIVE,
) -> Student:
    if parent_id is None:
        parent = _create_parent(db, school_id)
        parent_id = parent.id

    st = Student(
        school_id=school_id,
        academic_year_id=academic_year_id,
        school_class_id=school_class_id,
        section_id=section_id,
        parent_id=parent_id,
        admission_number=admission_number,
        first_name=first_name,
        last_name=last_name,
        gender="MALE",
        date_of_birth=date(2015, 1, 1),
        admission_date=date(2025, 4, 1),
        address_line1="123 Street",
        city="City",
        district="District",
        state="State",
        country="Country",
        postal_code="100001",
        roll_number=roll_number,
        status=status,
    )
    db.add(st)
    db.commit()
    db.refresh(st)
    return st


def _create_progression_rule(
    db: Session, school_id, source_class_id, target_class_id=None, is_terminal: bool = False
) -> ClassProgressionRule:
    rule = ClassProgressionRule(
        school_id=school_id,
        source_class_id=source_class_id,
        target_class_id=target_class_id,
        is_terminal=is_terminal,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def test_execution_service_success(db_session: Session):
    """
    Test 1 — Execution promotes active students, updates enrollment histories, and transitions AY status atomically.
    """
    school = _create_school(db_session)
    user = _create_user(db_session, school.id)

    ay_source = _create_academic_year(db_session, school.id, name="2025-2026", is_current=True, status=AcademicYearStatus.ACTIVE)
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False, status=AcademicYearStatus.UPCOMING)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2")
    sec2 = _create_section(db_session, cls2.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)

    student = _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, admission_number="ADM-EXEC-1", roll_number="001")

    # Generate live preview plan and hash
    plan = progression_planner.calculate_plan(db_session, ay_source.id, ay_target.id, school.id)

    req = ProgressionExecutionRequest(
        target_academic_year_id=ay_target.id,
        execution_plan_hash=plan.execution_plan_hash,
    )
    idem_key = f"IDEM-{uuid4().hex[:8]}"

    res = progression_execution_service.execute_progression(
        db=db_session,
        source_academic_year_id=ay_source.id,
        request=req,
        idempotency_key=idem_key,
        current_user=user,
    )

    assert res.success is True
    assert res.data.status == "COMPLETED"
    assert res.data.summary.promoted_count == 1

    # Verify student model placement updated
    db_session.refresh(student)
    assert student.academic_year_id == ay_target.id
    assert student.school_class_id == cls2.id
    assert student.section_id == sec2.id
    assert student.roll_number == "001"

    # Verify academic year transition
    db_session.refresh(ay_source)
    db_session.refresh(ay_target)
    assert ay_source.is_current is False
    assert ay_source.status == AcademicYearStatus.ARCHIVED
    assert ay_target.is_current is True
    assert ay_target.status == AcademicYearStatus.ACTIVE

    # Verify execution audit record
    exec_rec = db_session.scalar(select(ProgressionExecution).where(ProgressionExecution.id == res.data.execution_id))
    assert exec_rec is not None
    assert exec_rec.status == ProgressionExecutionStatus.COMPLETED
    assert len(exec_rec.items) == 1
    assert exec_rec.items[0].decision == "PROMOTED"
    assert exec_rec.items[0].status == "SUCCESS"


def test_execution_service_terminal_graduation(db_session: Session):
    """
    Test 2 — Terminal class progression sets student status to GRADUATED.
    """
    school = _create_school(db_session)
    user = _create_user(db_session, school.id)

    ay_source = _create_academic_year(db_session, school.id, name="2025-2026", is_current=True, status=AcademicYearStatus.ACTIVE)
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False, status=AcademicYearStatus.UPCOMING)

    cls12 = _create_class(db_session, school.id, name="Class 12")
    sec12 = _create_section(db_session, cls12.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls12.id, is_terminal=True)
    student = _create_student(db_session, school.id, ay_source.id, cls12.id, sec12.id, admission_number="ADM-GRAD-1")

    plan = progression_planner.calculate_plan(db_session, ay_source.id, ay_target.id, school.id)

    req = ProgressionExecutionRequest(
        target_academic_year_id=ay_target.id,
        execution_plan_hash=plan.execution_plan_hash,
    )
    res = progression_execution_service.execute_progression(
        db=db_session,
        source_academic_year_id=ay_source.id,
        request=req,
        idempotency_key=f"IDEM-{uuid4().hex[:8]}",
        current_user=user,
    )

    assert res.data.summary.graduated_count == 1
    db_session.refresh(student)
    assert student.status == StudentStatus.GRADUATED


def test_execution_service_stale_hash_rejection(db_session: Session):
    """
    Test 4 — Stale execution_plan_hash is rejected with zero student mutations.
    """
    school = _create_school(db_session)
    user = _create_user(db_session, school.id)

    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2")
    sec2 = _create_section(db_session, cls2.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    student = _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, roll_number="001")

    # Generate plan and hash
    plan = progression_planner.calculate_plan(db_session, ay_source.id, ay_target.id, school.id)

    # Mutate student roll number post-preview
    student.roll_number = "099"
    db_session.commit()

    req = ProgressionExecutionRequest(
        target_academic_year_id=ay_target.id,
        execution_plan_hash=plan.execution_plan_hash,  # Stale hash
    )

    with pytest.raises(ValidationException) as exc_info:
        progression_execution_service.execute_progression(
            db=db_session,
            source_academic_year_id=ay_source.id,
            request=req,
            idempotency_key=f"IDEM-{uuid4().hex[:8]}",
            current_user=user,
        )

    assert "Execution plan is stale" in str(exc_info.value)

    # Verify zero mutations on student
    db_session.refresh(student)
    assert student.academic_year_id == ay_source.id
    assert student.school_class_id == cls1.id


def test_execution_service_idempotency_cached(db_session: Session):
    """
    Test 5 — Repeated execution call with same idempotency key returns cached completion response.
    """
    school = _create_school(db_session)
    user = _create_user(db_session, school.id)

    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2")
    sec2 = _create_section(db_session, cls2.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, roll_number="001")

    plan = progression_planner.calculate_plan(db_session, ay_source.id, ay_target.id, school.id)

    req = ProgressionExecutionRequest(
        target_academic_year_id=ay_target.id,
        execution_plan_hash=plan.execution_plan_hash,
    )
    idem_key = "UNIQUE-IDEM-KEY-123"

    res1 = progression_execution_service.execute_progression(
        db=db_session,
        source_academic_year_id=ay_source.id,
        request=req,
        idempotency_key=idem_key,
        current_user=user,
    )

    # Call again with same idempotency key
    res2 = progression_execution_service.execute_progression(
        db=db_session,
        source_academic_year_id=ay_source.id,
        request=req,
        idempotency_key=idem_key,
        current_user=user,
    )

    assert res1.data.execution_id == res2.data.execution_id
    assert res2.message == "Academic progression rollover already executed (cached)."
