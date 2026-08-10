from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StudentExamResultCreate(BaseModel):
    """
    Request payload for creating a StudentExamResult.
    """

    exam_schedule_id: UUID
    student_id: UUID
    marks_obtained: Decimal = Field(..., ge=0, decimal_places=2, max_digits=5)
    remarks: str | None = None


class StudentExamResultUpdate(BaseModel):
    """
    Request payload for updating a StudentExamResult.
    """

    marks_obtained: Decimal | None = Field(
        default=None, ge=0, decimal_places=2, max_digits=5
    )
    remarks: str | None = None


class StudentExamResultResponse(BaseModel):
    """
    Response schema for a StudentExamResult.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exam_schedule_id: UUID
    student_id: UUID
    marks_obtained: Decimal
    remarks: str | None
    created_at: datetime
    updated_at: datetime


class StudentExamResultListResponse(BaseModel):
    """
    Paginated response schema for StudentExamResult list.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[StudentExamResultResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class StudentExamResultFilter(BaseModel):
    """
    Filter parameters for listing StudentExamResults.
    """

    exam_schedule_id: UUID | None = None
    student_id: UUID | None = None
    school_id: UUID | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
