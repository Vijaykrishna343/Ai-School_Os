from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import (
    EnrollmentStatus,
    PromotionDecision,
    TransferCertificateStatus,
)


class StudentPromotionRequest(BaseModel):
    """
    Request payload to promote a single student to a new academic year, class, and section.
    """

    target_academic_year_id: UUID = Field(
        ...,
        description="Target Academic Year ID for promotion",
    )
    target_class_id: UUID = Field(
        ...,
        description="Target Class ID",
    )
    target_section_id: UUID = Field(
        ...,
        description="Target Section ID",
    )
    roll_number: str | None = Field(
        None,
        max_length=20,
        description="Optional custom roll number. Auto-generated if omitted.",
    )
    remarks: str | None = Field(
        None,
        max_length=500,
        description="Optional administrative remarks",
    )


class StudentRetentionRequest(BaseModel):
    """
    Request payload to retain a student in the same/specified class for a new academic year.
    """

    target_academic_year_id: UUID = Field(
        ...,
        description="Target Academic Year ID for retention",
    )
    target_class_id: UUID | None = Field(
        None,
        description="Target Class ID (defaults to current class if omitted)",
    )
    target_section_id: UUID | None = Field(
        None,
        description="Target Section ID (defaults to current section if omitted)",
    )
    roll_number: str | None = Field(
        None,
        max_length=20,
        description="Optional custom roll number",
    )
    remarks: str | None = Field(
        None,
        max_length=500,
        description="Optional administrative remarks",
    )


class BulkStudentPromotionItem(BaseModel):
    student_id: UUID
    target_class_id: UUID
    target_section_id: UUID
    roll_number: str | None = Field(None, max_length=20)
    remarks: str | None = Field(None, max_length=500)


class BulkStudentPromotionRequest(BaseModel):
    source_academic_year_id: UUID
    target_academic_year_id: UUID
    promotions: list[BulkStudentPromotionItem] = Field(..., min_length=1)


class BulkStudentRetentionItem(BaseModel):
    student_id: UUID
    target_class_id: UUID | None = None
    target_section_id: UUID | None = None
    roll_number: str | None = Field(None, max_length=20)
    remarks: str | None = Field(None, max_length=500)


class BulkStudentRetentionRequest(BaseModel):
    source_academic_year_id: UUID
    target_academic_year_id: UUID
    retentions: list[BulkStudentRetentionItem] = Field(..., min_length=1)


class AcademicYearTransitionRequest(BaseModel):
    target_academic_year_id: UUID = Field(
        ...,
        description="Target Academic Year to activate and transition into",
    )
    remarks: str | None = Field(
        None,
        max_length=500,
        description="Optional remarks for transition log",
    )


class TransferCertificateCreate(BaseModel):
    academic_year_id: UUID = Field(
        ...,
        description="Academic year in which TC is issued",
    )
    tc_number: str | None = Field(
        None,
        max_length=50,
        description="Optional custom TC number. Auto-generated if omitted.",
    )
    issue_date: date = Field(..., description="TC Issue Date")
    leaving_date: date = Field(..., description="Date student left school")
    reason: str | None = Field(None, max_length=255, description="Reason for leaving")
    destination_school: str | None = Field(
        None, max_length=255, description="Destination school name"
    )
    remarks: str | None = Field(None, max_length=500, description="Remarks")


# ------------------------------------------------------------------
# Responses
# ------------------------------------------------------------------


class StudentEnrollmentHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    student_id: UUID
    academic_year_id: UUID
    school_class_id: UUID
    section_id: UUID
    roll_number: str
    enrollment_status: EnrollmentStatus
    promotion_decision: PromotionDecision
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime


class StudentEnrollmentHistoryListResponse(BaseModel):
    student_id: UUID
    enrollments: list[StudentEnrollmentHistoryResponse]
    total: int


class TransferCertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    student_id: UUID
    academic_year_id: UUID
    tc_number: str
    issue_date: date
    leaving_date: date
    reason: str | None = None
    destination_school: str | None = None
    remarks: str | None = None
    status: TransferCertificateStatus
    created_at: datetime
    updated_at: datetime


class TransferCertificateListResponse(BaseModel):
    student_id: UUID
    certificates: list[TransferCertificateResponse]
    total: int


class BulkPromotionResultResponse(BaseModel):
    total_processed: int
    promoted_count: int
    retained_count: int
    skipped_count: int
    errors: list[dict[str, str]] = []


class AcademicYearTransitionResponse(BaseModel):
    source_academic_year_id: UUID
    target_academic_year_id: UUID
    total_students_preserved: int
    message: str
