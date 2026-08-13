"""
Tests for Phase 4C.3 Legacy Promotion & API Hardening:
- Matrix rule enforcement during ad-hoc promotion
- Terminal class promotion rejection
- Invalid target class matrix rejection
"""

from datetime import date
from uuid import uuid4
import pytest

from app.common.enums import Gender
from app.common.exceptions import ValidationException
from app.models.academic_year.academic_year import AcademicYear
from app.models.academic_year.class_progression_rule import ClassProgressionRule
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.schemas.student.promotion_schema import StudentPromotionRequest
from app.services.student.student_promotion_service import student_promotion_service


@pytest.fixture
def promotion_test_env(db_session):
    school = School(
        name="Legacy Hardening Academy",
        code=f"LHA-{uuid4().hex[:6]}",
        address_line1="1 Legacy St",
        city="Legcity",
        district="Legdist",
        state="Legstate",
        postal_code="123123",
        phone="+1888777666",
        email=f"admin-{uuid4().hex[:6]}@lha.com",
    )
    db_session.add(school)
    db_session.commit()

    ay1 = AcademicYear(
        school_id=school.id,
        name="2024-2025",
        start_date=date(2024, 6, 1),
        end_date=date(2025, 4, 30),
        is_current=True,
    )
    ay2 = AcademicYear(
        school_id=school.id,
        name="2025-2026",
        start_date=date(2025, 6, 1),
        end_date=date(2026, 4, 30),
        is_current=False,
    )
    db_session.add_all([ay1, ay2])
    db_session.commit()

    cls1 = SchoolClass(school_id=school.id, name="Class 9", display_order=9)
    cls2 = SchoolClass(school_id=school.id, name="Class 10", display_order=10)
    cls3 = SchoolClass(school_id=school.id, name="Class 11 Invalid", display_order=11)
    db_session.add_all([cls1, cls2, cls3])
    db_session.commit()

    sec1 = Section(school_class_id=cls1.id, name="A", capacity=30)
    sec2 = Section(school_class_id=cls2.id, name="A", capacity=30)
    sec3 = Section(school_class_id=cls3.id, name="A", capacity=30)
    db_session.add_all([sec1, sec2, sec3])
    db_session.commit()

    parent = Parent(
        school_id=school.id,
        father_name="Father Doe",
        primary_phone="+1234567890",
        address_line1="123 Main St",
        city="TestCity",
        district="TestDistrict",
        state="TestState",
        postal_code="123456",
    )
    db_session.add(parent)
    db_session.commit()

    student = Student(
        school_id=school.id,
        parent_id=parent.id,
        academic_year_id=ay1.id,
        school_class_id=cls1.id,
        section_id=sec1.id,
        admission_number=f"ADM-{uuid4().hex[:6]}",
        roll_number="101",
        first_name="Jane",
        last_name="Doe",
        gender=Gender.FEMALE,
        date_of_birth=date(2010, 1, 1),
        admission_date=date(2024, 6, 1),
        address_line1="123 Student St",
        city="TestCity",
        district="TestDistrict",
        state="TestState",
        postal_code="123456",
    )
    db_session.add(student)
    db_session.commit()

    return {
        "school": school,
        "ay1": ay1,
        "ay2": ay2,
        "cls1": cls1,
        "cls2": cls2,
        "cls3": cls3,
        "sec1": sec1,
        "sec2": sec2,
        "sec3": sec3,
        "student": student,
    }


def test_promotion_matrix_rule_enforced(db_session, promotion_test_env):
    """
    When a progression matrix rule requires Class 9 -> Class 10, attempting to promote to Class 11 is rejected.
    """
    env = promotion_test_env
    # Create rule: Class 9 -> Class 10
    rule = ClassProgressionRule(
        school_id=env["school"].id,
        source_class_id=env["cls1"].id,
        target_class_id=env["cls2"].id,
        is_terminal=False,
    )
    db_session.add(rule)
    db_session.commit()

    req_invalid = StudentPromotionRequest(
        target_academic_year_id=env["ay2"].id,
        target_class_id=env["cls3"].id,
        target_section_id=env["sec3"].id,
    )

    with pytest.raises(ValidationException) as exc_info:
        student_promotion_service.promote_student(
            db=db_session,
            student_id=env["student"].id,
            data=req_invalid,
            current_school_id=env["school"].id,
        )
    assert "violates the configured class progression rule matrix" in str(exc_info.value)

    # Valid promotion to Class 10 according to matrix must succeed
    req_valid = StudentPromotionRequest(
        target_academic_year_id=env["ay2"].id,
        target_class_id=env["cls2"].id,
        target_section_id=env["sec2"].id,
    )
    result = student_promotion_service.promote_student(
        db=db_session,
        student_id=env["student"].id,
        data=req_valid,
        current_school_id=env["school"].id,
    )
    assert result is not None
    assert result.school_class_id == env["cls2"].id


def test_terminal_class_promotion_rejected(db_session, promotion_test_env):
    """
    Attempting to promote a student from a terminal class raises ValidationException.
    """
    env = promotion_test_env
    # Set Class 9 as terminal
    rule = ClassProgressionRule(
        school_id=env["school"].id,
        source_class_id=env["cls1"].id,
        target_class_id=None,
        is_terminal=True,
    )
    db_session.add(rule)
    db_session.commit()

    req = StudentPromotionRequest(
        target_academic_year_id=env["ay2"].id,
        target_class_id=env["cls2"].id,
        target_section_id=env["sec2"].id,
    )

    with pytest.raises(ValidationException) as exc_info:
        student_promotion_service.promote_student(
            db=db_session,
            student_id=env["student"].id,
            data=req,
            current_school_id=env["school"].id,
        )
    assert "configured as terminal" in str(exc_info.value)
