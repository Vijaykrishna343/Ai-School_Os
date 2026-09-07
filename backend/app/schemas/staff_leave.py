from __future__ import annotations

from decimal import Decimal
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# ── Staff Leave Type Schemas ───────────────────────────────────────────────────

class StaffLeaveTypeBase(BaseModel):
    code: str = Field(..., max_length=30)
    name: str = Field(..., max_length=100)
    description: str | None = None
    max_days_per_year: Decimal = Field(default=Decimal("12.00"), ge=0)
    requires_attachment: bool = False
    is_paid: bool = True
    is_active: bool = True


class StaffLeaveTypeCreate(StaffLeaveTypeBase):
    pass


class StaffLeaveTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    max_days_per_year: Decimal | None = None
    requires_attachment: bool | None = None
    is_paid: bool | None = None
    is_active: bool | None = None


class StaffLeaveTypeResponse(StaffLeaveTypeBase):
    id: UUID
    school_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Staff Leave Balance Schemas ────────────────────────────────────────────────

class StaffLeaveBalanceResponse(BaseModel):
    id: UUID
    school_id: UUID
    teacher_id: UUID
    academic_year_id: UUID
    leave_type_id: UUID
    leave_type_code: str
    leave_type_name: str
    allocated_days: Decimal
    used_days: Decimal
    pending_days: Decimal
    remaining_days: Decimal

    model_config = ConfigDict(from_attributes=True)


class StaffLeaveBalanceAllocate(BaseModel):
    teacher_id: UUID
    academic_year_id: UUID
    leave_type_id: UUID
    allocated_days: Decimal = Field(..., ge=0)


# ── Staff Leave Request Schemas ────────────────────────────────────────────────

class StaffLeaveRequestCreate(BaseModel):
    academic_year_id: UUID
    leave_type_id: UUID
    start_date: date
    end_date: date
    half_day_type: str = Field(default="FULL_DAY")  # FULL_DAY, FIRST_HALF, SECOND_HALF
    reason: str = Field(..., min_length=3)
    attachment_url: str | None = None


class StaffLeaveRequestUpdate(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    half_day_type: str | None = None
    reason: str | None = None
    attachment_url: str | None = None


class StaffLeaveApprovalAction(BaseModel):
    remarks: str | None = None


class StaffLeaveRejectAction(BaseModel):
    rejection_reason: str = Field(..., min_length=2)


class StaffLeaveApprovalHistoryResponse(BaseModel):
    id: UUID
    action_by_user_id: UUID
    action_by_name: str | None = None
    action: str
    from_status: str | None = None
    to_status: str
    remarks: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StaffLeaveRequestResponse(BaseModel):
    id: UUID
    school_id: UUID
    teacher_id: UUID
    teacher_name: str | None = None
    employee_id: str | None = None
    academic_year_id: UUID
    academic_year_name: str | None = None
    leave_type_id: UUID
    leave_type_code: str | None = None
    leave_type_name: str | None = None
    start_date: date
    end_date: date
    requested_days: Decimal
    half_day_type: str
    reason: str
    attachment_url: str | None = None
    status: str
    requested_by_user_id: UUID | None = None
    requested_by_name: str | None = None
    approved_by_user_id: UUID | None = None
    approved_by_name: str | None = None
    rejected_by_user_id: UUID | None = None
    rejected_by_name: str | None = None
    cancelled_by_user_id: UUID | None = None
    approval_remarks: str | None = None
    rejection_reason: str | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    approval_history: list[StaffLeaveApprovalHistoryResponse] = []

    model_config = ConfigDict(from_attributes=True)


class StaffLeaveSummaryReport(BaseModel):
    academic_year_id: UUID
    total_requests: int
    pending_requests: int
    approved_today: int
    currently_on_leave: int
    by_leave_type: dict[str, int]
    by_status: dict[str, int]
