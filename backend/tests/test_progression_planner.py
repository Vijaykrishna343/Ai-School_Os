"""
Unit tests for ProgressionPlanner domain component.

Verifies:
- Class-level roll number uniqueness across sections within the same class.
- Deterministic plan calculation & identical hash for identical DB state.
- Hash sensitivity to student data changes, rule changes, target occupancy changes.
- STRICT READ-ONLY constraint: zero DB mutations performed during plan calculation.
- Equivalent output between ProgressionPlanner and ProgressionPreviewService wrapper.
"""

from datetime import date
from uuid import uuid4
import pytest
from sqlalchemy.orm import Session

from app.common.enums import PromotionDecision, StudentStatus
from app.models.academic_year import AcademicYear, ClassProgressionRule
from app.models.parent import Parent
from app.models.school import School
from app.models.school_class import SchoolClass
from app.models.section import Section
from app.models.student import Student
from app.schemas.student.progression_preview_schema import ProgressionPreviewRequest
from app.services.student.progression_planner import ProgressionPlan, ProgressionPlanner, progression_planner
from app.services.student.progression_preview_service import progression_preview_service


def _create_school(db: Session, name: str = "Planner Test School") -> School:
    school = School(
        name=name,
        code=f"SCH-{name[:3].upper()}",
        address_line1="123 School Lane",
        city="SchoolCity",
        district="SchoolDistrict",
        state="SchoolState",
        postal_code="123456",
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def _create_academic_year(
    db: Session, school_id, name: str = "2025-2026", is_current: bool = True
) -> AcademicYear:
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


def test_planner_zero_db_mutations(db_session: Session):
    """
    Test 11 — ProgressionPlanner performs zero DB mutations (db session remains clean).
    """
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2")
    sec2 = _create_section(db_session, cls2.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, admission_number="ADM-P1", roll_number="001")

    # Clear pending state
    db_session.flush()

    plan = progression_planner.calculate_plan(db_session, ay_source.id, ay_target.id, school.id)

    # Verify session is strictly clean
    assert len(db_session.dirty) == 0
    assert len(db_session.new) == 0
    assert len(db_session.deleted) == 0
    assert plan.summary.promoted_count == 1


def test_planner_and_preview_service_equivalence(db_session: Session):
    """
    Test 10 — Preview response via ProgressionPreviewService matches ProgressionPlanner output.
    """
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2")
    sec2 = _create_section(db_session, cls2.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, admission_number="ADM-EQ", roll_number="001")

    plan = progression_planner.calculate_plan(db_session, ay_source.id, ay_target.id, school.id)

    req = ProgressionPreviewRequest(target_academic_year_id=ay_target.id)
    res = progression_preview_service.generate_preview(db_session, ay_source.id, req, school.id)

    assert res.execution_plan_hash == plan.execution_plan_hash
    assert res.summary == plan.summary
    assert len(res.items) == len(plan.evaluated_items)
    assert res.items[0].proposed_roll_number == plan.evaluated_items[0].proposed_roll_number


def test_planner_roll_numbers_class_level_unique(db_session: Session):
    """
    Test 3 — Roll numbers are unique across sections in the same class (class-level pool).
    """
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1_a = _create_section(db_session, cls1.id, name="A")
    sec1_b = _create_section(db_session, cls1.id, name="B")

    cls2 = _create_class(db_session, school.id, name="Class 2")
    sec2_a = _create_section(db_session, cls2.id, name="A")
    sec2_b = _create_section(db_session, cls2.id, name="B")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)

    # Student 1 in Sec A (Roll 001), Student 2 in Sec B (Roll 002)
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1_a.id, admission_number="ADM-P-A", roll_number="001")
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1_b.id, admission_number="ADM-P-B", roll_number="002")

    plan = progression_planner.calculate_plan(db_session, ay_source.id, ay_target.id, school.id)

    assert plan.summary.promoted_count == 2
    rolls = [item.proposed_roll_number for item in plan.evaluated_items]
    assert len(rolls) == 2
    assert len(set(rolls)) == 2
    assert rolls == ["001", "002"]


def test_planner_hash_sensitivity_student_change(db_session: Session):
    """
    Test 7 — Modifying student data alters the plan hash.
    """
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2")
    _create_section(db_session, cls2.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    student = _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, roll_number="001")

    plan1 = progression_planner.calculate_plan(db_session, ay_source.id, ay_target.id, school.id)

    student.roll_number = "099"
    db_session.commit()

    plan2 = progression_planner.calculate_plan(db_session, ay_source.id, ay_target.id, school.id)
    assert plan1.execution_plan_hash != plan2.execution_plan_hash


def test_planner_hash_sensitivity_rule_change(db_session: Session):
    """
    Test 8 — Modifying progression rule alters the plan hash.
    """
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2")
    _create_section(db_session, cls2.id, name="A")
    cls3 = _create_class(db_session, school.id, name="Class 3")
    _create_section(db_session, cls3.id, name="A")

    rule = _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, roll_number="001")

    plan1 = progression_planner.calculate_plan(db_session, ay_source.id, ay_target.id, school.id)

    rule.target_class_id = cls3.id
    db_session.commit()

    plan2 = progression_planner.calculate_plan(db_session, ay_source.id, ay_target.id, school.id)
    assert plan1.execution_plan_hash != plan2.execution_plan_hash


def test_planner_hash_sensitivity_target_occupancy_change(db_session: Session):
    """
    Test 9 — Adding target AY student occupancy alters the plan hash.
    """
    school = _create_school(db_session)
    ay_source = _create_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 1")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 2")
    sec2 = _create_section(db_session, cls2.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, admission_number="ADM-SRC", roll_number="001")

    plan1 = progression_planner.calculate_plan(db_session, ay_source.id, ay_target.id, school.id)

    _create_student(db_session, school.id, ay_target.id, cls2.id, sec2.id, admission_number="ADM-TGT", roll_number="001")

    plan2 = progression_planner.calculate_plan(db_session, ay_source.id, ay_target.id, school.id)
    assert plan1.execution_plan_hash != plan2.execution_plan_hash
