from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums.admissions import (
    AdmissionApplicationStatus,
    AdmissionCycleStatus,
    AdmissionDecisionType,
    ApplicantStatus,
)


# =============================================================================
# 1. ADMISSION CYCLE SCHEMAS
# =============================================================================

class AdmissionCycleCreate(BaseModel):
    academic_year_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    start_date: date
    end_date: date
    description: str | None = Field(default=None, max_length=255)
    status: AdmissionCycleStatus = Field(default=AdmissionCycleStatus.DRAFT)
    is_active: bool = Field(default=True)


class AdmissionCycleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = Field(default=None, max_length=255)
    status: AdmissionCycleStatus | None = None
    is_active: bool | None = None


class AdmissionCycleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    academic_year_id: UUID
    name: str
    code: str
    start_date: date
    end_date: date
    status: AdmissionCycleStatus
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdmissionCycleListResponse(BaseModel):
    items: list[AdmissionCycleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# 2. APPLICANT SCHEMAS
# =============================================================================

class ApplicantCreate(BaseModel):
    admission_cycle_id: UUID | None = None
    applicant_number: str | None = Field(default=None, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: str = Field(..., min_length=1, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)
    parent_name: str | None = Field(default=None, max_length=200)
    parent_phone: str | None = Field(default=None, max_length=50)
    parent_email: str | None = Field(default=None, max_length=255)
    source: str | None = Field(default=None, max_length=100)
    status: ApplicantStatus = Field(default=ApplicantStatus.PROSPECT)
    notes: str | None = Field(default=None, max_length=1000)


class ApplicantUpdate(BaseModel):
    admission_cycle_id: UUID | None = None
    applicant_number: str | None = Field(default=None, max_length=50)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, min_length=1, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)
    parent_name: str | None = Field(default=None, max_length=200)
    parent_phone: str | None = Field(default=None, max_length=50)
    parent_email: str | None = Field(default=None, max_length=255)
    source: str | None = Field(default=None, max_length=100)
    status: ApplicantStatus | None = None
    notes: str | None = Field(default=None, max_length=1000)


class ApplicantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    admission_cycle_id: UUID | None = None
    applicant_number: str
    first_name: str
    middle_name: str | None = None
    last_name: str
    date_of_birth: date
    gender: str
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    parent_name: str | None = None
    parent_phone: str | None = None
    parent_email: str | None = None
    source: str | None = None
    status: ApplicantStatus
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ApplicantListResponse(BaseModel):
    items: list[ApplicantResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# 3. ADMISSION APPLICATION SCHEMAS
# =============================================================================

class AdmissionApplicationCreate(BaseModel):
    applicant_id: UUID
    admission_cycle_id: UUID
    academic_year_id: UUID
    target_class_id: UUID
    target_section_id: UUID | None = None
    application_number: str | None = Field(default=None, max_length=50)
    application_date: date | None = None
    status: AdmissionApplicationStatus = Field(default=AdmissionApplicationStatus.DRAFT)
    remarks: str | None = Field(default=None, max_length=1000)


class AdmissionApplicationUpdate(BaseModel):
    target_class_id: UUID | None = None
    target_section_id: UUID | None = None
    application_date: date | None = None
    remarks: str | None = Field(default=None, max_length=1000)


class ApplicationSubmitRequest(BaseModel):
    remarks: str | None = Field(default=None, max_length=1000)


class ApplicationReviewRequest(BaseModel):
    remarks: str | None = Field(default=None, max_length=1000)


class ApplicationWithdrawRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)
    remarks: str | None = Field(default=None, max_length=1000)


class AdmissionApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    applicant_id: UUID
    admission_cycle_id: UUID
    academic_year_id: UUID
    target_class_id: UUID
    target_section_id: UUID | None = None
    application_number: str
    application_date: date
    status: AdmissionApplicationStatus
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    decision_at: datetime | None = None
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime


class AdmissionApplicationListResponse(BaseModel):
    items: list[AdmissionApplicationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# 4. APPLICATION STATUS HISTORY SCHEMAS
# =============================================================================

class ApplicationStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    application_id: UUID
    old_status: str | None = None
    new_status: str
    changed_by_user_id: UUID | None = None
    changed_at: datetime
    reason: str | None = None
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime


class ApplicationStatusHistoryListResponse(BaseModel):
    items: list[ApplicationStatusHistoryResponse]
    total: int


# =============================================================================
# 5. ADMISSION DECISION SCHEMAS
# =============================================================================

class AdmissionDecisionCreate(BaseModel):
    decision_type: AdmissionDecisionType
    comments: str | None = Field(default=None, max_length=1000)
    conditions: str | None = Field(default=None, max_length=1000)


class AdmissionDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    application_id: UUID
    decision_type: AdmissionDecisionType
    decided_by_user_id: UUID | None = None
    decided_at: datetime
    comments: str | None = None
    conditions: str | None = None
    created_at: datetime
    updated_at: datetime


class AdmissionDecisionListResponse(BaseModel):
    items: list[AdmissionDecisionResponse]
    total: int
