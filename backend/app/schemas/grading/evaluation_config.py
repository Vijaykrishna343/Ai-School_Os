from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums.exam import AssessmentType
from app.common.enums.report_card import (
    CalculationMode,
    RetestPolicy,
    RoundingMode,
)


class AssessmentTypeWeightageBase(BaseModel):
    assessment_type: AssessmentType
    weightage_percentage: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("100.00"))


class AssessmentTypeWeightageCreate(AssessmentTypeWeightageBase):
    pass


class AssessmentTypeWeightageResponse(AssessmentTypeWeightageBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    evaluation_config_id: UUID


class EvaluationConfigBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    calculation_mode: CalculationMode = CalculationMode.SIMPLE_TOTAL
    retest_policy: RetestPolicy = RetestPolicy.REPLACE_ORIGINAL
    rounding_mode: RoundingMode = RoundingMode.ROUND_HALF_UP
    gpa_enabled: bool = False
    is_default: bool = True


class EvaluationConfigCreate(EvaluationConfigBase):
    school_id: UUID
    academic_year_id: UUID
    weightages: list[AssessmentTypeWeightageCreate] = Field(default_factory=list)


class EvaluationConfigUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    calculation_mode: CalculationMode | None = None
    retest_policy: RetestPolicy | None = None
    rounding_mode: RoundingMode | None = None
    gpa_enabled: bool | None = None
    is_default: bool | None = None
    weightages: list[AssessmentTypeWeightageCreate] | None = None


class EvaluationConfigResponse(EvaluationConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    academic_year_id: UUID
    weightages: list[AssessmentTypeWeightageResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class EvaluationConfigListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[EvaluationConfigResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
