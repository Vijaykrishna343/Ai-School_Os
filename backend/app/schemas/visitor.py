from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums.visitor import (
    HostType,
    IdProofType,
    ReceptionInquiryStatus,
    VisitorStatus,
)


class VisitorCreate(BaseModel):
    """
    Request payload for creating/registering a visitor.
    """

    visitor_name: str = Field(..., min_length=1, max_length=150)
    phone: str = Field(..., min_length=5, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    id_proof_type: IdProofType | None = Field(default=None)
    id_proof_number: str | None = Field(default=None, max_length=100)
    purpose: str = Field(..., min_length=1, max_length=255)
    host_type: HostType | None = Field(default=None)
    host_id: UUID | None = Field(default=None)
    check_in_time: datetime | None = Field(default=None)
    status: VisitorStatus = Field(default=VisitorStatus.EXPECTED)
    pass_number: str | None = Field(default=None, max_length=50)
    remarks: str | None = Field(default=None, max_length=255)


class VisitorUpdate(BaseModel):
    """
    Request payload for updating visitor details.
    """

    visitor_name: str | None = Field(default=None, min_length=1, max_length=150)
    phone: str | None = Field(default=None, min_length=5, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    id_proof_type: IdProofType | None = Field(default=None)
    id_proof_number: str | None = Field(default=None, max_length=100)
    purpose: str | None = Field(default=None, min_length=1, max_length=255)
    host_type: HostType | None = Field(default=None)
    host_id: UUID | None = Field(default=None)
    check_in_time: datetime | None = Field(default=None)
    check_out_time: datetime | None = Field(default=None)
    status: VisitorStatus | None = Field(default=None)
    pass_number: str | None = Field(default=None, max_length=50)
    remarks: str | None = Field(default=None, max_length=255)


class VisitorCheckOut(BaseModel):
    """
    Request payload for checking out a visitor.
    """

    check_out_time: datetime | None = Field(default=None)
    remarks: str | None = Field(default=None, max_length=255)


class VisitorPreRegister(BaseModel):
    """
    Request payload for pre-registering an expected visitor.
    Server enforces status = EXPECTED.
    """

    visitor_name: str = Field(..., min_length=1, max_length=150)
    phone: str = Field(..., min_length=5, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    id_proof_type: IdProofType | None = Field(default=None)
    id_proof_number: str | None = Field(default=None, max_length=100)
    purpose: str = Field(..., min_length=1, max_length=255)
    host_type: HostType | None = Field(default=None)
    host_id: UUID | None = Field(default=None)
    remarks: str | None = Field(default=None, max_length=255)


class VisitorBadgeResponse(BaseModel):
    """
    Privacy-preserving visitor pass badge schema.
    Omits sensitive ID proof numbers for badge printing and pass visual rendering.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    visitor_name: str
    phone: str
    email: str | None
    purpose: str
    host_type: HostType | None
    host_id: UUID | None
    check_in_time: datetime | None
    check_out_time: datetime | None
    status: VisitorStatus
    pass_number: str | None
    created_at: datetime



class VisitorResponse(BaseModel):
    """
    Detailed response schema for a visitor record.
    Includes full operational identity details for authorized single-record views.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    visitor_name: str
    phone: str
    email: str | None
    id_proof_type: IdProofType | None
    id_proof_number: str | None
    purpose: str
    host_type: HostType | None
    host_id: UUID | None
    check_in_time: datetime | None
    check_out_time: datetime | None
    status: VisitorStatus
    pass_number: str | None
    remarks: str | None
    created_at: datetime
    updated_at: datetime


class VisitorSummaryResponse(BaseModel):
    """
    Privacy-preserving summary response schema for list views.
    Omits sensitive ID proof numbers for general list/summary rendering.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    visitor_name: str
    phone: str
    email: str | None
    id_proof_type: IdProofType | None
    purpose: str
    host_type: HostType | None
    host_id: UUID | None
    check_in_time: datetime | None
    check_out_time: datetime | None
    status: VisitorStatus
    pass_number: str | None
    created_at: datetime
    updated_at: datetime


class VisitorListResponse(BaseModel):
    """
    Paginated list response for visitor records.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[VisitorSummaryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ReceptionInquiryCreate(BaseModel):
    """
    Request payload for logging a front-desk reception inquiry or appointment.
    """

    visitor_id: UUID | None = Field(default=None)
    contact_name: str = Field(..., min_length=1, max_length=150)
    contact_phone: str = Field(..., min_length=5, max_length=20)
    contact_email: str | None = Field(default=None, max_length=255)
    subject: str = Field(..., min_length=1, max_length=255)
    details: str | None = Field(default=None)
    host_type: HostType | None = Field(default=None)
    host_id: UUID | None = Field(default=None)
    appointment_time: datetime | None = Field(default=None)
    status: ReceptionInquiryStatus = Field(default=ReceptionInquiryStatus.PENDING)
    notes: str | None = Field(default=None)


class ReceptionInquiryUpdate(BaseModel):
    """
    Request payload for updating a reception inquiry record.
    """

    visitor_id: UUID | None = Field(default=None)
    contact_name: str | None = Field(default=None, min_length=1, max_length=150)
    contact_phone: str | None = Field(default=None, min_length=5, max_length=20)
    contact_email: str | None = Field(default=None, max_length=255)
    subject: str | None = Field(default=None, min_length=1, max_length=255)
    details: str | None = Field(default=None)
    host_type: HostType | None = Field(default=None)
    host_id: UUID | None = Field(default=None)
    appointment_time: datetime | None = Field(default=None)
    status: ReceptionInquiryStatus | None = Field(default=None)
    notes: str | None = Field(default=None)


class ReceptionInquiryResponse(BaseModel):
    """
    Response schema for a reception inquiry record.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    visitor_id: UUID | None
    contact_name: str
    contact_phone: str
    contact_email: str | None
    subject: str
    details: str | None
    host_type: HostType | None
    host_id: UUID | None
    appointment_time: datetime | None
    status: ReceptionInquiryStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ReceptionInquiryListResponse(BaseModel):
    """
    Paginated list response for reception inquiry records.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[ReceptionInquiryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AnalyticsPeriod(BaseModel):
    start_date: date
    end_date: date


class VisitorAnalyticsMetrics(BaseModel):
    total: int
    checked_in: int
    checked_out: int
    currently_active: int


class InquiryAnalyticsMetrics(BaseModel):
    total: int
    pending: int
    in_progress: int
    resolved: int
    cancelled: int


class AppointmentAnalyticsMetrics(BaseModel):
    total: int
    upcoming: int
    completed: int


class PurposeCountItem(BaseModel):
    purpose: str
    count: int


class HostTypeCountItem(BaseModel):
    host_type: str
    count: int


class OperationalAnalyticsMetrics(BaseModel):
    avg_visitor_duration_minutes: float | None = None
    peak_checkin_hour: int | None = None
    visitors_by_purpose: list[PurposeCountItem] = Field(default_factory=list)
    visitors_by_host_type: list[HostTypeCountItem] = Field(default_factory=list)


class DailyTrendItem(BaseModel):
    date: date
    count: int


class ReceptionAnalyticsResponse(BaseModel):
    period: AnalyticsPeriod
    visitors: VisitorAnalyticsMetrics
    inquiries: InquiryAnalyticsMetrics
    appointments: AppointmentAnalyticsMetrics
    operational_metrics: OperationalAnalyticsMetrics
    visitor_trend: list[DailyTrendItem] = Field(default_factory=list)
    inquiry_trend: list[DailyTrendItem] = Field(default_factory=list)

