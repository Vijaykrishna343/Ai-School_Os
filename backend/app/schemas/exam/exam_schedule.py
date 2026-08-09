from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExamScheduleCreate(BaseModel):
    """
    Request payload for creating an ExamSchedule.
    """

    exam_id: UUID
    school_id: UUID
    academic_year_id: UUID
    school_class_id: UUID
    section_id: UUID
    subject_id: UUID
    exam_date: date
    start_time: time
    end_time: time
    maximum_marks: Decimal = Field(..., gt=0, decimal_places=2, max_digits=5)
    passing_marks: Decimal = Field(..., ge=0, decimal_places=2, max_digits=5)


class ExamScheduleUpdate(BaseModel):
    """
    Request payload for updating an ExamSchedule.
    """

    exam_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    maximum_marks: Decimal | None = Field(default=None, gt=0, decimal_places=2, max_digits=5)
    passing_marks: Decimal | None = Field(default=None, ge=0, decimal_places=2, max_digits=5)


class ExamScheduleResponse(BaseModel):
    """
    Response schema for an ExamSchedule.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exam_id: UUID
    school_id: UUID
    academic_year_id: UUID
    school_class_id: UUID
    section_id: UUID
    subject_id: UUID
    exam_date: date
    start_time: time
    end_time: time
    maximum_marks: Decimal
    passing_marks: Decimal
    created_at: datetime
    updated_at: datetime


class ExamScheduleListResponse(BaseModel):
    """
    Paginated response schema for ExamSchedule list.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[ExamScheduleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ExamScheduleFilter(BaseModel):
    """
    Filter parameters for listing ExamSchedules.
    """

    exam_id: UUID | None = None
    school_id: UUID | None = None
    academic_year_id: UUID | None = None
    school_class_id: UUID | None = None
    section_id: UUID | None = None
    subject_id: UUID | None = None
    exam_date: date | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
