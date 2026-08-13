from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.common.enums import PromotionDecision, StudentStatus
from app.common.exceptions import NotFoundException, ValidationException
from app.models.academic_year import AcademicYear, ClassProgressionRule
from app.models.parent import Parent
from app.models.school import School
from app.models.school_class import SchoolClass
from app.models.section import Section
from app.models.student import Student, StudentEnrollmentHistory
from app.schemas.student.progression_preview_schema import ProgressionPreviewRequest
from app.services.student.progression_preview_service import progression_preview_service


def _create_school(db: Session, name="Preview Test School") -> School:
    school = School(
        id=uuid4(),
        name=name,
        code=f"SCH-{uuid4().hex[:6]}",
        address_line1="100 Academic Way",
        city="TestCity",
        district="Central",
        state="TestState",
        country="India",
        postal_code="110001",
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def _create_parent(db: Session, school_id) -> Parent:
    parent = Parent(
        school_id=school_id,
        father_name="John Doe",
        primary_phone=f"+199{uuid4().hex[:8]}",
        address_line1="123 Main St",
        city="TestCity",
        district="Central",
        state="TestState",
        postal_code="110001",
    )
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent


def _create_academic_year(db: Session, school_id, name="2025-2026", is_current=True) -> AcademicYear:
    ay = AcademicYear(
        school_id=school_id,
        name=name,
        start_date=date(2025, 4, 1),
        end_date=date(2026, 3, 31),
        is_current=is_current,
    )
    db.add(ay)
    db.commit()
    db.refresh(ay)
    return ay


def _create_class(db: Session, school_id, name="Class 1", display_order=1) -> SchoolClass:
    sc = SchoolClass(
        school_id=school_id,
        name=name,
        display_order=display_order,
    )
    db.add(sc)
    db.commit()
    db.refresh(sc)
    return sc


def _create_section(db: Session, school_class_id, name="A") -> Section:
    sec = Section(
        school_class_id=school_class_id,
        name=name,
    )
    db.add(sec)
    db.commit()
    db.refresh(sec)
    return sec


def _create_student(
    db: Session,
    school_id,
    academic_year_id,
    school_class_id,
    section_id,
    parent_id=None,
    admission_number="ADM-001",
    first_name="John",
    last_name="Doe",
    status=StudentStatus.ACTIVE,
    roll_number="001",
) -> Student:
    if parent_id is None:
        parent = _create_parent(db, school_id)
        parent_id = parent.id

    student = Student(
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
        address_line1="123 Student St",
        city="TestCity",
        district="Central",
        state="TestState",
        postal_code="110001",
        status=status,
        roll_number=roll_number,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def _create_progression_rule(
    db: Session,
    school_id,
    source_class_id,
    target_class_id=None,
    is_terminal=False,
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


def test_preview_normal_promotion_success(db_session: Session):
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1", display_order=1)
    sec1 = _create_section(db_session, cls1.id, name="A")

    cls2 = _create_class(db_session, school.id, name="Class 2", display_order=2)
    sec2 = _create_section(db_session, cls2.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    student = _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id)

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    assert res.summary.total_students_evaluated == 1
    assert res.summary.promoted_count == 1
    assert res.summary.graduated_count == 0
    assert res.summary.blocked_count == 0
    assert res.summary.excluded_count == 0

    item = res.items[0]
    assert item.student_id == student.id
    assert item.decision == PromotionDecision.PROMOTED
    assert item.target_class_id == cls2.id
    assert item.target_class_name == "Class 2"
    assert item.target_section_id == sec2.id
    assert item.target_section_name == "A"
    assert item.proposed_roll_number == "001"
    assert item.allocation_status == "PROPOSED"


def test_preview_terminal_class_graduation(db_session: Session):
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls12 = _create_class(db_session, school.id, name="Class 12", display_order=12)
    sec12 = _create_section(db_session, cls12.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls12.id, is_terminal=True)
    student = _create_student(db_session, school.id, ay_source.id, cls12.id, sec12.id)

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    assert res.summary.graduated_count == 1
    assert res.summary.promoted_count == 0

    item = res.items[0]
    assert item.decision == PromotionDecision.GRADUATED
    assert item.target_class_id is None
    assert item.target_section_id is None
    assert item.proposed_roll_number is None
    assert item.allocation_status == "READY"


def test_preview_missing_progression_rule_blocked(db_session: Session):
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    student = _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id)

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    assert res.summary.blocked_count == 1
    item = res.items[0]
    assert item.allocation_status == "BLOCKED"
    assert "No active class progression rule" in item.reason


def test_preview_missing_target_class_blocked(db_session: Session):
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")

    cls2 = _create_class(db_session, school.id, name="Class 2")
    rule = _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)

    # Soft delete target class
    cls2.is_deleted = True
    db_session.commit()

    student = _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id)

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    assert res.summary.blocked_count == 1
    item = res.items[0]
    assert item.allocation_status == "BLOCKED"
    assert "does not exist or was deleted" in item.reason


def test_preview_fallback_section_matching(db_session: Session):
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec_c = _create_section(db_session, cls1.id, name="C")

    cls2 = _create_class(db_session, school.id, name="Class 2")
    sec_a = _create_section(db_session, cls2.id, name="A")  # Target only has Section A

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    student = _create_student(db_session, school.id, ay_source.id, cls1.id, sec_c.id)

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    assert res.summary.promoted_count == 1
    assert res.summary.warning_count == 1
    item = res.items[0]
    assert item.target_section_id == sec_a.id
    assert len(item.warnings) == 1
    assert "Fallback to section 'A'" in item.warnings[0]


def test_preview_target_class_no_sections_blocked(db_session: Session):
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")

    cls2 = _create_class(db_session, school.id, name="Class 2")  # No sections created

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    student = _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id)

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    assert res.summary.blocked_count == 1
    item = res.items[0]
    assert item.allocation_status == "BLOCKED"
    assert "has no active sections" in item.reason


def test_preview_inactive_student_exclusion(db_session: Session):
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")

    cls2 = _create_class(db_session, school.id, name="Class 2")
    _create_section(db_session, cls2.id, name="A")
    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)

    parent = _create_parent(db_session, school.id)
    s_active = _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, parent_id=parent.id, admission_number="ADM-001", status=StudentStatus.ACTIVE, roll_number="001")
    s_inactive = _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, parent_id=parent.id, admission_number="ADM-002", status=StudentStatus.INACTIVE, roll_number="002")
    s_transferred = _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, parent_id=parent.id, admission_number="ADM-003", status=StudentStatus.TRANSFERRED, roll_number="003")
    s_withdrawn = _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, parent_id=parent.id, admission_number="ADM-004", status=StudentStatus.WITHDRAWN, roll_number="004")

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    assert res.summary.total_students_evaluated == 4
    assert res.summary.promoted_count == 1
    assert res.summary.excluded_count == 3


def test_preview_tenant_isolation(db_session: Session):
    school_a = _create_school(db_session, "School A")
    school_b = _create_school(db_session, "School B")

    ay_source_a = _create_academic_year(db_session, school_a.id, name="2025-2026")
    ay_target_b = _create_academic_year(db_session, school_b.id, name="2026-2027")

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target_b.id)

    # Attempting to preview across schools must raise NotFoundException
    with pytest.raises(NotFoundException):
        progression_preview_service.generate_preview(db_session, ay_source_a.id, req, school_a.id)


def test_preview_same_source_and_target_year_rejected(db_session: Session):
    school = _create_school(db_session)
    ay = _create_academic_year(db_session, school.id, name="2025-2026")

    req = ProgressionPreviewRequest(target_academic_year_id=ay.id)
    with pytest.raises(ValidationException, match="cannot be the same"):
        progression_preview_service.generate_preview(db_session, ay.id, req, school.id)


def test_preview_db_immutability(db_session: Session):
    """
    MANDATORY DB IMMUTABILITY TEST: Assert DB state before == DB state after preview execution.
    """
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2")
    sec2 = _create_section(db_session, cls2.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    student = _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, roll_number="001")

    # Capture BEFORE snapshot
    student_before = (student.academic_year_id, student.school_class_id, student.section_id, student.roll_number, student.status)
    history_count_before = db_session.query(StudentEnrollmentHistory).count()
    ay_source_status_before = (ay_source.status, ay_source.is_current)
    ay_target_status_before = (ay_target.status, ay_target.is_current)

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    db_session.refresh(student)
    db_session.refresh(ay_source)
    db_session.refresh(ay_target)

    # Capture AFTER snapshot
    student_after = (student.academic_year_id, student.school_class_id, student.section_id, student.roll_number, student.status)
    history_count_after = db_session.query(StudentEnrollmentHistory).count()
    ay_source_status_after = (ay_source.status, ay_source.is_current)
    ay_target_status_after = (ay_target.status, ay_target.is_current)

    # ASSERT ZERO MUTATIONS
    assert student_before == student_after
    assert history_count_before == history_count_after
    assert ay_source_status_before == ay_source_status_after
    assert ay_target_status_before == ay_target_status_after


def test_preview_proposed_roll_number_sequential_allocation(db_session: Session):
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2")
    sec2 = _create_section(db_session, cls2.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)

    parent = _create_parent(db_session, school.id)
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, parent_id=parent.id, admission_number="ADM-001", first_name="Alice", last_name="Brown", roll_number="001")
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, parent_id=parent.id, admission_number="ADM-002", first_name="Bob", last_name="Smith", roll_number="002")
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, parent_id=parent.id, admission_number="ADM-003", first_name="Charlie", last_name="Zane", roll_number="003")

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    assert res.summary.promoted_count == 3
    rolls = [item.proposed_roll_number for item in res.items]
    assert rolls == ["001", "002", "003"]


def test_preview_target_year_existing_rolls_offset(db_session: Session):
    """
    Test 1 — Existing target rolls: 001, 002, 003 in target AY.
    New preview students should receive 004, 005.
    """
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2")
    sec2 = _create_section(db_session, cls2.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)

    parent = _create_parent(db_session, school.id)

    # Existing students ALREADY in target academic year (Class 2 / Section A)
    _create_student(db_session, school.id, ay_target.id, cls2.id, sec2.id, parent_id=parent.id, admission_number="ADM-TGT-001", first_name="Target1", roll_number="001")
    _create_student(db_session, school.id, ay_target.id, cls2.id, sec2.id, parent_id=parent.id, admission_number="ADM-TGT-002", first_name="Target2", roll_number="002")
    _create_student(db_session, school.id, ay_target.id, cls2.id, sec2.id, parent_id=parent.id, admission_number="ADM-TGT-003", first_name="Target3", roll_number="003")

    # Source year students waiting to be promoted
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, parent_id=parent.id, admission_number="ADM-SRC-001", first_name="Alice", last_name="Brown", roll_number="001")
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, parent_id=parent.id, admission_number="ADM-SRC-002", first_name="Bob", last_name="Smith", roll_number="002")

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    assert res.summary.promoted_count == 2
    rolls = [item.proposed_roll_number for item in res.items]
    assert rolls == ["004", "005"]


def test_preview_target_year_roll_gaps_filling(db_session: Session):
    """
    Test 2 — Target rolls have gaps: 001, 003, 007.
    Proposed numbers should fill available gaps: 002, 004.
    """
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2")
    sec2 = _create_section(db_session, cls2.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    parent = _create_parent(db_session, school.id)

    # Existing target students with roll number gaps
    _create_student(db_session, school.id, ay_target.id, cls2.id, sec2.id, parent_id=parent.id, admission_number="ADM-TGT-001", roll_number="001")
    _create_student(db_session, school.id, ay_target.id, cls2.id, sec2.id, parent_id=parent.id, admission_number="ADM-TGT-003", roll_number="003")
    _create_student(db_session, school.id, ay_target.id, cls2.id, sec2.id, parent_id=parent.id, admission_number="ADM-TGT-007", roll_number="007")

    # Source year students
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, parent_id=parent.id, admission_number="ADM-SRC-001", first_name="Alice", last_name="Brown", roll_number="001")
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, parent_id=parent.id, admission_number="ADM-SRC-002", first_name="Bob", last_name="Smith", roll_number="002")

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    assert res.summary.promoted_count == 2
    rolls = [item.proposed_roll_number for item in res.items]
    assert rolls == ["002", "004"]


def test_preview_multiple_target_sections_occupancy_independence(db_session: Session):
    """
    Test 3 — Multiple target placements have independent roll number occupancy counters.
    """
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1_a = _create_class(db_session, school.id, name="Class 1", display_order=1)
    sec1_a = _create_section(db_session, cls1_a.id, name="A")

    cls1_b = _create_class(db_session, school.id, name="Class 2", display_order=2)
    sec1_b = _create_section(db_session, cls1_b.id, name="A")

    cls2_a = _create_class(db_session, school.id, name="Target Class 1", display_order=3)
    sec2_a = _create_section(db_session, cls2_a.id, name="A")

    cls2_b = _create_class(db_session, school.id, name="Target Class 2", display_order=4)
    sec2_b = _create_section(db_session, cls2_b.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1_a.id, target_class_id=cls2_a.id)
    _create_progression_rule(db_session, school.id, source_class_id=cls1_b.id, target_class_id=cls2_b.id)
    parent = _create_parent(db_session, school.id)

    # Target Placement A existing target rolls: 001, 002
    _create_student(db_session, school.id, ay_target.id, cls2_a.id, sec2_a.id, parent_id=parent.id, admission_number="ADM-TA1", roll_number="001")
    _create_student(db_session, school.id, ay_target.id, cls2_a.id, sec2_a.id, parent_id=parent.id, admission_number="ADM-TA2", roll_number="002")

    # Target Placement B existing target rolls: 001, 002, 003
    _create_student(db_session, school.id, ay_target.id, cls2_b.id, sec2_b.id, parent_id=parent.id, admission_number="ADM-TB1", roll_number="001")
    _create_student(db_session, school.id, ay_target.id, cls2_b.id, sec2_b.id, parent_id=parent.id, admission_number="ADM-TB2", roll_number="002")
    _create_student(db_session, school.id, ay_target.id, cls2_b.id, sec2_b.id, parent_id=parent.id, admission_number="ADM-TB3", roll_number="003")

    # Source students
    s_a = _create_student(db_session, school.id, ay_source.id, cls1_a.id, sec1_a.id, parent_id=parent.id, admission_number="ADM-SA1", first_name="StudentA", roll_number="001")
    s_b = _create_student(db_session, school.id, ay_source.id, cls1_b.id, sec1_b.id, parent_id=parent.id, admission_number="ADM-SB1", first_name="StudentB", roll_number="001")

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    assert res.summary.promoted_count == 2
    item_a = next(i for i in res.items if i.student_id == s_a.id)
    item_b = next(i for i in res.items if i.student_id == s_b.id)

    assert item_a.proposed_roll_number == "003"  # 001, 002 existing in Target Class 1
    assert item_b.proposed_roll_number == "004"  # 001, 002, 003 existing in Target Class 2


def test_preview_cross_class_rolls_no_interference(db_session: Session):
    """
    Test 5 — Existing students in Target Class 3 do NOT block Target Class 2 roll numbers.
    """
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1", display_order=1)
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2", display_order=2)
    sec2 = _create_section(db_session, cls2.id, name="A")
    cls3 = _create_class(db_session, school.id, name="Class 3", display_order=3)
    sec3 = _create_section(db_session, cls3.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    parent = _create_parent(db_session, school.id)

    # Class 3 has 001 in Target AY
    _create_student(db_session, school.id, ay_target.id, cls3.id, sec3.id, parent_id=parent.id, admission_number="ADM-C3-01", roll_number="001")

    # Class 1 student promoting to Class 2
    student = _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, parent_id=parent.id, admission_number="ADM-C1-01", roll_number="001")

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    assert res.items[0].proposed_roll_number == "001"


def test_preview_cross_school_rolls_no_interference(db_session: Session):
    """
    Test 6 — Existing students in School B do NOT affect roll allocation in School A.
    """
    school_a = _create_school(db_session, "School A")
    school_b = _create_school(db_session, "School B")

    ay_source_a = _create_academic_year(db_session, school_a.id, name="2025-2026")
    ay_target_a = _create_academic_year(db_session, school_a.id, name="2026-2027", is_current=False)

    cls1_a = _create_class(db_session, school_a.id, name="Class 1")
    sec1_a = _create_section(db_session, cls1_a.id, name="A")
    cls2_a = _create_class(db_session, school_a.id, name="Class 2")
    sec2_a = _create_section(db_session, cls2_a.id, name="A")
    _create_progression_rule(db_session, school_a.id, source_class_id=cls1_a.id, target_class_id=cls2_a.id)

    ay_target_b = _create_academic_year(db_session, school_b.id, name="2026-2027", is_current=False)
    cls2_b = _create_class(db_session, school_b.id, name="Class 2")
    sec2_b = _create_section(db_session, cls2_b.id, name="A")

    parent_a = _create_parent(db_session, school_a.id)
    parent_b = _create_parent(db_session, school_b.id)

    # School B has roll 001 in Class 2 / Sec A
    _create_student(db_session, school_b.id, ay_target_b.id, cls2_b.id, sec2_b.id, parent_id=parent_b.id, admission_number="ADM-SCHB-01", roll_number="001")

    # School A student
    _create_student(db_session, school_a.id, ay_source_a.id, cls1_a.id, sec1_a.id, parent_id=parent_a.id, admission_number="ADM-SCHA-01", roll_number="001")

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target_a.id)
    res = progression_preview_service.generate_preview(db_session, ay_source_a.id, req, school_a.id)

    assert res.items[0].proposed_roll_number == "001"


def test_preview_repeated_call_idempotent(db_session: Session):
    """
    Test 10 — Running preview twice with unchanged database state produces 100% identical outputs.
    """
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2")
    sec2 = _create_section(db_session, cls2.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    parent = _create_parent(db_session, school.id)

    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, parent_id=parent.id, admission_number="ADM-001", first_name="Alice", last_name="Brown", roll_number="001")
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, parent_id=parent.id, admission_number="ADM-002", first_name="Bob", last_name="Smith", roll_number="002")

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res1 = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)
    res2 = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    assert res1.model_dump() == res2.model_dump()


def test_preview_execution_plan_hash_valid_sha256(db_session: Session):
    """
    Verify preview response contains a valid 64-character SHA-256 hash.
    """
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2")
    sec2 = _create_section(db_session, cls2.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, roll_number="001")

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    assert hasattr(res, "execution_plan_hash")
    assert isinstance(res.execution_plan_hash, str)
    assert len(res.execution_plan_hash) == 64
    assert all(c in "0123456789abcdef" for c in res.execution_plan_hash)


def test_preview_execution_plan_hash_identical_state(db_session: Session):
    """
    Verify identical preview state produces identical hash.
    """
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2")
    sec2 = _create_section(db_session, cls2.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, roll_number="001")

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res1 = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)
    res2 = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    assert res1.execution_plan_hash == res2.execution_plan_hash


def test_preview_execution_plan_hash_student_change(db_session: Session):
    """
    Verify changing relevant student data changes the execution plan hash.
    """
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2")
    sec2 = _create_section(db_session, cls2.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    student = _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, roll_number="001")

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res1 = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    # Mutate student
    student.roll_number = "099"
    db_session.commit()

    res2 = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)
    assert res1.execution_plan_hash != res2.execution_plan_hash


def test_preview_execution_plan_hash_rule_change(db_session: Session):
    """
    Verify changing progression rule data changes the execution plan hash.
    """
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2")
    sec2 = _create_section(db_session, cls2.id, name="A")
    cls3 = _create_class(db_session, school.id, name="Class 3")
    _create_section(db_session, cls3.id, name="A")

    rule = _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, roll_number="001")

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res1 = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    # Change progression rule target class
    rule.target_class_id = cls3.id
    db_session.commit()

    res2 = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)
    assert res1.execution_plan_hash != res2.execution_plan_hash


def test_preview_execution_plan_hash_target_occupancy_change(db_session: Session):
    """
    Verify changing target occupancy changes the execution plan hash.
    """
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2")
    sec2 = _create_section(db_session, cls2.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, admission_number="ADM-SRC-1", roll_number="001")

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res1 = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    # Add a target student in target AY
    _create_student(db_session, school.id, ay_target.id, cls2.id, sec2.id, admission_number="ADM-TGT-1", roll_number="001")

    res2 = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)
    assert res1.execution_plan_hash != res2.execution_plan_hash


def test_preview_roll_numbers_unique_across_sections_in_same_class(db_session: Session):
    """
    Verify roll numbers are allocated uniquely across sections in the same class
    to respect uq_student_roll_number (academic_year_id, school_class_id, roll_number).
    """
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1_a = _create_section(db_session, cls1.id, name="A")
    sec1_b = _create_section(db_session, cls1.id, name="B")

    cls2 = _create_class(db_session, school.id, name="Class 2")
    _create_section(db_session, cls2.id, name="A")
    _create_section(db_session, cls2.id, name="B")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)

    parent = _create_parent(db_session, school.id)
    # Student 1 in Section A (Roll 001)
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1_a.id, parent_id=parent.id, admission_number="ADM-SEC-A", first_name="Alice", roll_number="001")
    # Student 2 in Section B (Roll 002)
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1_b.id, parent_id=parent.id, admission_number="ADM-SEC-B", first_name="Bob", roll_number="002")

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    assert res.summary.promoted_count == 2
    rolls = [item.proposed_roll_number for item in res.items]
    # Rolls must be unique across all sections of Class 2: "001" and "002"
    assert len(rolls) == 2
    assert len(set(rolls)) == 2
    assert rolls == ["001", "002"]


