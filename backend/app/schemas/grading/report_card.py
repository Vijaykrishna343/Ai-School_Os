from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums.report_card import ReportCardStatus


class ReportCardItemSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    report_card_id: UUID
    subject_id: UUID
    subject_name: str
    subject_code: str
    max_marks: Decimal
    obtained_marks: Decimal
    percentage: Decimal
    grade_code: str
    grade_point: Decimal
    is_pass: bool
    remarks: str | None = None


class ReportCardGenerateRequest(BaseModel):
    school_id: UUID
    academic_year_id: UUID
    academic_term_id: UUID | None = None
    student_id: UUID | None = None
    section_id: UUID | None = None
    school_class_id: UUID | None = None
    grade_scale_id: UUID | None = None
    evaluation_config_id: UUID | None = None


class ReportCardRemarksUpdate(BaseModel):
    teacher_remarks: str | None = None
    principal_remarks: str | None = None


class ReportCardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    academic_year_id: UUID
    academic_term_id: UUID | None = None
    student_id: UUID
    school_class_id: UUID
    section_id: UUID
    grade_scale_id: UUID
    evaluation_config_id: UUID
    status: ReportCardStatus
    total_max_marks: Decimal
    total_obtained_marks: Decimal
    percentage: Decimal
    overall_grade: str
    overall_grade_point: Decimal
    gpa: Decimal | None = None
    is_passed: bool
    total_working_days: int
    present_days: int
    attendance_percentage: Decimal
    teacher_remarks: str | None = None
    principal_remarks: str | None = None
    finalized_at: datetime | None = None
    published_at: datetime | None = None
    items: list[ReportCardItemSnapshotResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ReportCardListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[ReportCardResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ReportCardFilter(BaseModel):
    school_id: UUID | None = None
    academic_year_id: UUID | None = None
    academic_term_id: UUID | None = None
    school_class_id: UUID | None = None
    section_id: UUID | None = None
    student_id: UUID | None = None
    status: ReportCardStatus | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
