from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums.exam import ExamStatus, ExamType


class ExamCreate(BaseModel):
    """
    Request payload for creating an Exam.
    """

    school_id: UUID
    academic_year_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    exam_type: ExamType
    start_date: date
    end_date: date
    status: ExamStatus = Field(default=ExamStatus.DRAFT)


class ExamUpdate(BaseModel):
    """
    Request payload for updating an Exam.
    """

    name: str | None = Field(default=None, min_length=1, max_length=100)
    exam_type: ExamType | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: ExamStatus | None = None


class ExamResponse(BaseModel):
    """
    Response schema for an Exam.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    academic_year_id: UUID
    name: str
    exam_type: ExamType
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
    exam_type: ExamType | None = None
    status: ExamStatus | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
