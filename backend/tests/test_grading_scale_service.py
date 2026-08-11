import uuid
from decimal import Decimal

import pytest

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from app.models.school.school import School
from app.schemas.grading.grade_scale import (
    GradeScaleCreate,
    GradeScaleEntryCreate,
    GradeScaleFilter,
    GradeScaleUpdate,
)
from app.services.grading_scale_service import grade_scale_service


def create_test_school(db, name="Grading School", code="GSCH"):
    school = School(
        id=uuid.uuid4(),
        name=name,
        code=f"{code}_{uuid.uuid4().hex[:4]}",
        address_line1="10 Grading St",
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


def test_01_create_grading_scale(db_session):
    school = create_test_school(db_session)
    data = GradeScaleCreate(
        name="CBSE Basic Scale",
        description="Standard 10 Point Scale",
        is_default=False,
        entries=[],
    )
    scale = grade_scale_service.create_grade_scale(
        db_session, data, current_school_id=school.id
    )
    assert scale.id is not None
    assert scale.name == "CBSE Basic Scale"
    assert scale.school_id == school.id
    assert scale.is_default is False


def test_02_create_grading_scale_with_entries(db_session):
    school = create_test_school(db_session)
    entries = [
        GradeScaleEntryCreate(
            grade_code="A",
            min_percentage=Decimal("90.00"),
            max_percentage=Decimal("100.00"),
            grade_point=Decimal("10.00"),
            description="Outstanding",
            is_pass=True,
        ),
        GradeScaleEntryCreate(
            grade_code="B",
            min_percentage=Decimal("75.00"),
            max_percentage=Decimal("89.99"),
            grade_point=Decimal("8.00"),
            description="Very Good",
            is_pass=True,
        ),
    ]
    data = GradeScaleCreate(
        name="Scale With Entries",
        description="Two Band Scale",
        is_default=True,
        entries=entries,
    )
    scale = grade_scale_service.create_grade_scale(
        db_session, data, current_school_id=school.id
    )
    assert len(scale.entries) == 2
    codes = {e.grade_code for e in scale.entries}
    assert codes == {"A", "B"}


def test_03_valid_grade_ranges(db_session):
    school = create_test_school(db_session)
    entries = [
        GradeScaleEntryCreate(
            grade_code="A",
            min_percentage=Decimal("90.00"),
            max_percentage=Decimal("100.00"),
            grade_point=Decimal("10.00"),
        ),
        GradeScaleEntryCreate(
            grade_code="B",
            min_percentage=Decimal("70.00"),
            max_percentage=Decimal("89.99"),
            grade_point=Decimal("8.00"),
        ),
        GradeScaleEntryCreate(
            grade_code="F",
            min_percentage=Decimal("0.00"),
            max_percentage=Decimal("69.99"),
            grade_point=Decimal("0.00"),
            is_pass=False,
        ),
    ]
    data = GradeScaleCreate(name="Valid Multi Band", entries=entries)
    scale = grade_scale_service.create_grade_scale(
        db_session, data, current_school_id=school.id
    )
    assert len(scale.entries) == 3


def test_04_invalid_percentage_below_0(db_session):
    school = create_test_school(db_session)
    with pytest.raises(Exception):
        GradeScaleEntryCreate(
            grade_code="F",
            min_percentage=Decimal("-5.00"),
            max_percentage=Decimal("50.00"),
        )


def test_05_invalid_percentage_above_100(db_session):
    school = create_test_school(db_session)
    with pytest.raises(Exception):
        GradeScaleEntryCreate(
            grade_code="A+",
            min_percentage=Decimal("90.00"),
            max_percentage=Decimal("105.00"),
        )



def test_06_min_greater_than_max_rejected(db_session):
    school = create_test_school(db_session)
    entries = [
        GradeScaleEntryCreate(
            grade_code="A",
            min_percentage=Decimal("95.00"),
            max_percentage=Decimal("80.00"),
        )
    ]
    data = GradeScaleCreate(name="Inverted Range", entries=entries)
    with pytest.raises(ValidationException, match="cannot exceed max_percentage"):
        grade_scale_service.create_grade_scale(
            db_session, data, current_school_id=school.id
        )


def test_07_duplicate_grade_code_rejected(db_session):
    school = create_test_school(db_session)
    entries = [
        GradeScaleEntryCreate(
            grade_code="A",
            min_percentage=Decimal("90.00"),
            max_percentage=Decimal("100.00"),
        ),
        GradeScaleEntryCreate(
            grade_code="A",
            min_percentage=Decimal("70.00"),
            max_percentage=Decimal("89.99"),
        ),
    ]
    data = GradeScaleCreate(name="Duplicate Code", entries=entries)
    with pytest.raises(ValidationException, match="Duplicate grade_code"):
        grade_scale_service.create_grade_scale(
            db_session, data, current_school_id=school.id
        )


def test_08_overlapping_grade_ranges_rejected(db_session):
    school = create_test_school(db_session)
    entries = [
        GradeScaleEntryCreate(
            grade_code="A",
            min_percentage=Decimal("80.00"),
            max_percentage=Decimal("100.00"),
        ),
        GradeScaleEntryCreate(
            grade_code="B",
            min_percentage=Decimal("70.00"),
            max_percentage=Decimal("85.00"),
        ),
    ]
    data = GradeScaleCreate(name="Overlapping Ranges", entries=entries)
    with pytest.raises(ValidationException, match="Overlapping grade bands detected"):
        grade_scale_service.create_grade_scale(
            db_session, data, current_school_id=school.id
        )


def test_09_adjacent_non_overlapping_ranges_accepted(db_session):
    school = create_test_school(db_session)
    entries = [
        GradeScaleEntryCreate(
            grade_code="A",
            min_percentage=Decimal("90.00"),
            max_percentage=Decimal("100.00"),
        ),
        GradeScaleEntryCreate(
            grade_code="B",
            min_percentage=Decimal("75.00"),
            max_percentage=Decimal("89.99"),
        ),
    ]
    data = GradeScaleCreate(name="Adjacent Ranges", entries=entries)
    scale = grade_scale_service.create_grade_scale(
        db_session, data, current_school_id=school.id
    )
    assert len(scale.entries) == 2


def test_10_exact_boundary_matching(db_session):
    school = create_test_school(db_session)
    entries = [
        GradeScaleEntryCreate(
            grade_code="A",
            min_percentage=Decimal("90.00"),
            max_percentage=Decimal("100.00"),
        ),
        GradeScaleEntryCreate(
            grade_code="B",
            min_percentage=Decimal("75.00"),
            max_percentage=Decimal("89.99"),
        ),
    ]
    scale = grade_scale_service.create_grade_scale(
        db_session,
        GradeScaleCreate(name="Boundary Scale", entries=entries),
        current_school_id=school.id,
    )

    match_90 = grade_scale_service.calculate_grade(
        db_session, Decimal("90.00"), scale_id=scale.id, current_school_id=school.id
    )
    assert match_90.matched_entry is not None
    assert match_90.matched_entry.grade_code == "A"

    match_89_99 = grade_scale_service.calculate_grade(
        db_session, Decimal("89.99"), scale_id=scale.id, current_school_id=school.id
    )
    assert match_89_99.matched_entry is not None
    assert match_89_99.matched_entry.grade_code == "B"


def test_11_zero_percent_matching(db_session):
    school = create_test_school(db_session)
    entries = [
        GradeScaleEntryCreate(
            grade_code="F",
            min_percentage=Decimal("0.00"),
            max_percentage=Decimal("49.99"),
            is_pass=False,
        )
    ]
    scale = grade_scale_service.create_grade_scale(
        db_session,
        GradeScaleCreate(name="Zero Match Scale", entries=entries),
        current_school_id=school.id,
    )
    match_0 = grade_scale_service.calculate_grade(
        db_session, Decimal("0.00"), scale_id=scale.id, current_school_id=school.id
    )
    assert match_0.matched_entry is not None
    assert match_0.matched_entry.grade_code == "F"


def test_12_hundred_percent_matching(db_session):
    school = create_test_school(db_session)
    entries = [
        GradeScaleEntryCreate(
            grade_code="A+",
            min_percentage=Decimal("90.00"),
            max_percentage=Decimal("100.00"),
        )
    ]
    scale = grade_scale_service.create_grade_scale(
        db_session,
        GradeScaleCreate(name="Hundred Match Scale", entries=entries),
        current_school_id=school.id,
    )
    match_100 = grade_scale_service.calculate_grade(
        db_session, Decimal("100.00"), scale_id=scale.id, current_school_id=school.id
    )
    assert match_100.matched_entry is not None
    assert match_100.matched_entry.grade_code == "A+"


def test_13_default_scale_creation(db_session):
    school = create_test_school(db_session)
    scale = grade_scale_service.create_grade_scale(
        db_session,
        GradeScaleCreate(name="First Default", is_default=True),
        current_school_id=school.id,
    )
    assert scale.is_default is True
    fetched_default = grade_scale_service.get_default_grade_scale(
        db_session, current_school_id=school.id
    )
    assert fetched_default.id == scale.id


def test_14_switching_default_scale(db_session):
    school = create_test_school(db_session)
    scale1 = grade_scale_service.create_grade_scale(
        db_session,
        GradeScaleCreate(name="Scale 1", is_default=True),
        current_school_id=school.id,
    )
    scale2 = grade_scale_service.create_grade_scale(
        db_session,
        GradeScaleCreate(name="Scale 2", is_default=True),
        current_school_id=school.id,
    )
    db_session.refresh(scale1)
    db_session.refresh(scale2)
    assert scale1.is_default is False
    assert scale2.is_default is True


def test_15_only_one_default_remains(db_session):
    school = create_test_school(db_session)
    grade_scale_service.create_grade_scale(
        db_session,
        GradeScaleCreate(name="S1", is_default=True),
        current_school_id=school.id,
    )
    grade_scale_service.create_grade_scale(
        db_session,
        GradeScaleCreate(name="S2", is_default=True),
        current_school_id=school.id,
    )
    response = grade_scale_service.list_grade_scales(
        db_session,
        GradeScaleFilter(is_default=True),
        current_school_id=school.id,
    )
    assert response.total == 1
    assert response.items[0].name == "S2"


def test_16_deleted_scale_cannot_become_default(db_session):
    school = create_test_school(db_session)
    scale = grade_scale_service.create_grade_scale(
        db_session,
        GradeScaleCreate(name="ToDeleteDefault", is_default=True),
        current_school_id=school.id,
    )
    grade_scale_service.delete_grade_scale(
        db_session, scale.id, current_school_id=school.id
    )
    with pytest.raises(NotFoundException):
        grade_scale_service.get_default_grade_scale(
            db_session, current_school_id=school.id
        )


def test_17_tenant_isolation(db_session):
    school1 = create_test_school(db_session, "School 1", "SCH1")
    school2 = create_test_school(db_session, "School 2", "SCH2")

    scale1 = grade_scale_service.create_grade_scale(
        db_session,
        GradeScaleCreate(name="School 1 Scale"),
        current_school_id=school1.id,
    )

    with pytest.raises(NotFoundException):
        grade_scale_service.get_grade_scale(
            db_session, scale1.id, current_school_id=school2.id
        )


def test_18_cross_school_update_rejected(db_session):
    school1 = create_test_school(db_session, "School A", "SCHA")
    school2 = create_test_school(db_session, "School B", "SCHB")

    scale = grade_scale_service.create_grade_scale(
        db_session,
        GradeScaleCreate(name="School A Scale"),
        current_school_id=school1.id,
    )

    with pytest.raises(NotFoundException):
        grade_scale_service.update_grade_scale(
            db_session,
            scale.id,
            GradeScaleUpdate(name="Hacked Scale"),
            current_school_id=school2.id,
        )


def test_19_cross_school_delete_rejected(db_session):
    school1 = create_test_school(db_session, "School X", "SCHX")
    school2 = create_test_school(db_session, "School Y", "SCHY")

    scale = grade_scale_service.create_grade_scale(
        db_session,
        GradeScaleCreate(name="School X Scale"),
        current_school_id=school1.id,
    )

    with pytest.raises(NotFoundException):
        grade_scale_service.delete_grade_scale(
            db_session, scale.id, current_school_id=school2.id
        )


def test_20_soft_delete_behavior(db_session):
    school = create_test_school(db_session)
    entries = [
        GradeScaleEntryCreate(
            grade_code="A",
            min_percentage=Decimal("90.00"),
            max_percentage=Decimal("100.00"),
        )
    ]
    scale = grade_scale_service.create_grade_scale(
        db_session,
        GradeScaleCreate(name="Soft Delete Test", entries=entries),
        current_school_id=school.id,
    )
    grade_scale_service.delete_grade_scale(
        db_session, scale.id, current_school_id=school.id
    )

    # Scale should be excluded from get
    with pytest.raises(NotFoundException):
        grade_scale_service.get_grade_scale(
            db_session, scale.id, current_school_id=school.id
        )

    # Scale should be excluded from list
    res = grade_scale_service.list_grade_scales(
        db_session, GradeScaleFilter(), current_school_id=school.id
    )
    assert res.total == 0
