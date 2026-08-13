"""
Tests for Phase 4C.2 Database Hardening:
- Partial unique indexes (WHERE is_deleted = FALSE)
- Soft-deletion re-creation semantics
"""

from datetime import date
from uuid import uuid4
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.school.school import School
from app.models.academic_year.academic_year import AcademicYear
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student


@pytest.fixture
def db_school(db_session):
    school = School(
        name="DB Hardening Academy",
        code=f"DBH-{uuid4().hex[:6]}",
        address_line1="1 DB Way",
        city="DBVille",
        district="DBDistrict",
        state="DBState",
        postal_code="112233",
        phone="+1999888777",
        email=f"admin-{uuid4().hex[:6]}@dbh.com",
    )
    db_session.add(school)
    db_session.commit()
    db_session.refresh(school)
    return school


def test_academic_year_soft_delete_recreation(db_session, db_school):
    """
    Active duplicates are rejected, but soft-deleted academic years allow re-creation of the same name.
    """
    ay1 = AcademicYear(
        school_id=db_school.id,
        name="2027-2028",
        start_date=date(2027, 6, 1),
        end_date=date(2028, 4, 30),
    )
    db_session.add(ay1)
    db_session.commit()

    # Active duplicate must fail
    ay_dup = AcademicYear(
        school_id=db_school.id,
        name="2027-2028",
        start_date=date(2027, 6, 1),
        end_date=date(2028, 4, 30),
    )
    db_session.add(ay_dup)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Soft-delete ay1
    ay1.is_deleted = True
    db_session.commit()

    # New active academic year with same name must succeed
    ay2 = AcademicYear(
        school_id=db_school.id,
        name="2027-2028",
        start_date=date(2027, 6, 1),
        end_date=date(2028, 4, 30),
    )
    db_session.add(ay2)
    db_session.commit()
    assert ay2.id is not None
    assert ay2.is_deleted is False


def test_school_class_soft_delete_recreation(db_session, db_school):
    """
    Soft-deleted school class names can be re-created without unique constraint violation.
    """
    cls1 = SchoolClass(
        school_id=db_school.id,
        name="Class 10 Special",
        display_order=10,
    )
    db_session.add(cls1)
    db_session.commit()

    # Active duplicate must fail
    cls_dup = SchoolClass(
        school_id=db_school.id,
        name="Class 10 Special",
        display_order=10,
    )
    db_session.add(cls_dup)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Soft-delete cls1
    cls1.is_deleted = True
    db_session.commit()

    # Re-create active class with same name
    cls2 = SchoolClass(
        school_id=db_school.id,
        name="Class 10 Special",
        display_order=10,
    )
    db_session.add(cls2)
    db_session.commit()
    assert cls2.id is not None


def test_section_soft_delete_recreation(db_session, db_school):
    """
    Soft-deleted section names can be re-created under the same class.
    """
    cls = SchoolClass(
        school_id=db_school.id,
        name="Class 11",
        display_order=11,
    )
    db_session.add(cls)
    db_session.commit()

    sec1 = Section(
        school_class_id=cls.id,
        name="Z",
        capacity=30,
    )
    db_session.add(sec1)
    db_session.commit()

    # Soft-delete section
    sec1.is_deleted = True
    db_session.commit()

    # Re-create section with same name
    sec2 = Section(
        school_class_id=cls.id,
        name="Z",
        capacity=30,
    )
    db_session.add(sec2)
    db_session.commit()
    assert sec2.id is not None
