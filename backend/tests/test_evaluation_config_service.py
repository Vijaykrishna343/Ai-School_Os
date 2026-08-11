import uuid
from datetime import date
from decimal import Decimal

import pytest

from app.common.enums import (
    AcademicYearStatus,
    AssessmentType,
    CalculationMode,
    RetestPolicy,
    RoundingMode,
)
from app.common.exceptions import ForbiddenException, NotFoundException
from app.models.academic_year.academic_year import AcademicYear
from app.models.grading.evaluation_config import EvaluationConfig
from app.models.school.school import School
from app.schemas.grading.evaluation_config import (
    AssessmentTypeWeightageCreate,
    EvaluationConfigCreate,
)
from app.services.evaluation_config_service import evaluation_config_service


def test_create_evaluation_config_success(db_session):
    school = School(
        name="Eval School",
        code=f"SCH-{uuid.uuid4().hex[:6]}",
        address_line1="100 Eval St",
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

    config_data = EvaluationConfigCreate(
        school_id=school.id,
        academic_year_id=ay.id,
        name="CBSE 10-Point Scheme",
        calculation_mode=CalculationMode.WEIGHTED_ASSESSMENT_TYPE,
        retest_policy=RetestPolicy.BEST_ATTEMPT,
        rounding_mode=RoundingMode.ROUND_HALF_UP,
        gpa_enabled=True,
        is_default=True,
        weightages=[
            AssessmentTypeWeightageCreate(
                assessment_type=AssessmentType.FORMATIVE_ASSESSMENT,
                weightage_percentage=Decimal("20.00"),
            ),
            AssessmentTypeWeightageCreate(
                assessment_type=AssessmentType.SUMMATIVE_ASSESSMENT,
                weightage_percentage=Decimal("80.00"),
            ),
        ],
    )

    created = evaluation_config_service.create_evaluation_config(
        db_session, config_data, current_school_id=school.id
    )

    assert created.id is not None
    assert created.name == "CBSE 10-Point Scheme"
    assert created.gpa_enabled is True
    assert len(created.weightages) == 2


def test_create_evaluation_config_forbidden(db_session):
    school1_id = uuid.uuid4()
    school2_id = uuid.uuid4()
    ay_id = uuid.uuid4()

    config_data = EvaluationConfigCreate(
        school_id=school1_id,
        academic_year_id=ay_id,
        name="Forbidden Config",
    )

    with pytest.raises(ForbiddenException):
        evaluation_config_service.create_evaluation_config(
            db_session, config_data, current_school_id=school2_id
        )
