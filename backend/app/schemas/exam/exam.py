from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.common.enums.exam import (
    AssessmentType,
    AttemptType,
    ExamStatus,
    parse_legacy_exam_type,
)


class ExamCreate(BaseModel):
    """
    Request payload for creating an Exam.
    Supports assessment_type and attempt_type, with fallback for legacy exam_type.
    Optionally accepts academic_term_id.
    """

    school_id: UUID
    academic_year_id: UUID
    academic_term_id: UUID | None = None
    name: str = Field(..., min_length=1, max_length=100)
    assessment_type: AssessmentType = Field(default=AssessmentType.OTHER)
    attempt_type: AttemptType = Field(default=AttemptType.REGULAR)
    exam_type: str | None = Field(default=None, description="Deprecated legacy field")
    start_date: date
    end_date: date
    status: ExamStatus = Field(default=ExamStatus.DRAFT)

    @model_validator(mode="before")
    @classmethod
    def handle_legacy_exam_type(cls, data: Any) -> Any:
        if isinstance(data, dict):
            legacy_val = data.get("exam_type")
            if legacy_val is not None:
                parsed_assessment, parsed_attempt = parse_legacy_exam_type(
                    str(legacy_val)
                )
                if "assessment_type" not in data or data["assessment_type"] is None:
                    data["assessment_type"] = parsed_assessment
                if "attempt_type" not in data or data["attempt_type"] is None:
                    data["attempt_type"] = parsed_attempt
        return data


class ExamUpdate(BaseModel):
    """
    Request payload for updating an Exam.
    Supports updating assessment_type, attempt_type, academic_term_id, or legacy exam_type.
    Legacy exam_type updates ONLY attempt_type and preserves existing assessment_type.
    """

    academic_term_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    assessment_type: AssessmentType | None = None
    attempt_type: AttemptType | None = None
    exam_type: str | None = Field(default=None, description="Deprecated legacy field")
    start_date: date | None = None
    end_date: date | None = None
    status: ExamStatus | None = None

    @model_validator(mode="before")
    @classmethod
    def handle_legacy_exam_type(cls, data: Any) -> Any:
        if isinstance(data, dict):
            legacy_val = data.get("exam_type")
            if legacy_val is not None:
                _, parsed_attempt = parse_legacy_exam_type(str(legacy_val))
                if "attempt_type" not in data or data["attempt_type"] is None:
                    data["attempt_type"] = parsed_attempt
        return data


class ExamResponse(BaseModel):
    """
    Response schema for an Exam.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    academic_year_id: UUID
    academic_term_id: UUID | None = None
    name: str
    assessment_type: AssessmentType
    attempt_type: AttemptType
    start_date: date
    end_date: date
    status: ExamStatus
    created_at: datetime
    updated_at: datetime


class ExamListResponse(BaseModel):
    """
    Paginated response schema for Exam list.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[ExamResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ExamFilter(BaseModel):
    """
    Filter parameters for listing Exams.
    """

    school_id: UUID | None = None
    academic_year_id: UUID | None = None
    academic_term_id: UUID | None = None
    assessment_type: AssessmentType | None = None
    attempt_type: AttemptType | None = None
    exam_type: str | None = Field(default=None, description="Deprecated legacy filter")
    status: ExamStatus | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
