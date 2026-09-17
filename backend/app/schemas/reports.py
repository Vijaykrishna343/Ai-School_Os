"""
Executive Reports & BI Analytics Schemas — Phase 30.2
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReportFilterParams(BaseModel):
    """Common filter parameters for executive reports."""
    model_config = ConfigDict(from_attributes=True)

    academic_year_id: Optional[UUID] = None
    academic_term_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    section_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ---------------------------------------------------------------------------
# Executive Summary
# ---------------------------------------------------------------------------

class ExecutiveKpiCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    value: str
    numeric_value: float
    unit: Optional[str] = None
    subtext: Optional[str] = None
    trend_direction: Optional[str] = None  # "up", "down", "neutral"
    trend_label: Optional[str] = None
    status: Optional[str] = None  # "success", "warning", "info", "danger"


class ExecutiveSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    school_id: UUID
    school_name: str
    generated_at: datetime
    active_students: int
    active_teachers: int
    active_classes: int
    overall_attendance_pct: float
    total_fees_assigned: float
    total_fees_collected: float
    total_fees_outstanding: float
    fee_collection_rate_pct: float
    admissions_inquiries: int
    admissions_applicants: int
    admissions_enrolled: int
    admissions_conversion_pct: float
    published_report_cards_pct: float
    kpi_cards: List[ExecutiveKpiCard]
    operations_highlights: Dict[str, Any]


# ---------------------------------------------------------------------------
# Student & Enrollment Report
# ---------------------------------------------------------------------------

class ClassEnrollmentItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    class_id: UUID
    class_name: str
    section_id: Optional[UUID] = None
    section_name: Optional[str] = None
    student_count: int
    male_count: int
    female_count: int
    other_count: int
    capacity: Optional[int] = None
    occupancy_pct: Optional[float] = None


class EnrollmentTrendItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period: str
    active_count: int
    new_admissions: int


class StudentEnrollmentReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_active_students: int
    total_inactive_students: int
    total_students: int
    gender_distribution: Dict[str, int]
    by_class_section: List[ClassEnrollmentItem]
    enrollment_trends: List[EnrollmentTrendItem]
    total_items: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Attendance Report
# ---------------------------------------------------------------------------

class ClassAttendanceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    class_id: UUID
    class_name: str
    section_id: Optional[UUID] = None
    section_name: Optional[str] = None
    total_students: int
    present_count: int
    absent_count: int
    late_count: int
    excused_count: int
    attendance_pct: float


class ChronicAbsenteeItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: UUID
    admission_number: str
    student_name: str
    class_name: str
    section_name: str
    total_days: int
    present_days: int
    absent_days: int
    attendance_pct: float


class AttendanceReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date_evaluated: date
    overall_attendance_pct: float
    total_expected_students: int
    total_present: int
    total_absent: int
    total_late: int
    total_excused: int
    by_class_section: List[ClassAttendanceItem]
    chronic_absentee_count: int
    chronic_absentees: List[ChronicAbsenteeItem]
    total_items: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Finance Report
# ---------------------------------------------------------------------------

class PaymentMethodItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    method: str
    total_amount: float
    transaction_count: int
    percentage_of_total: float


class AgingBucketSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bucket_0_30_days: float
    bucket_31_60_days: float
    bucket_61_90_days: float
    bucket_90_plus_days: float


class RecentCollectionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_id: UUID
    payment_reference: str
    student_name: str
    admission_number: str
    amount: float
    payment_method: str
    payment_date: datetime
    fee_type: str


class FinanceReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_fees_assigned: float
    total_fees_collected: float
    total_fees_outstanding: float
    collection_rate_pct: float
    hostel_fees_collected: float
    transport_fees_collected: float
    academic_fees_collected: float
    payment_methods_breakdown: List[PaymentMethodItem]
    aging_buckets: AgingBucketSummary
    recent_collections: List[RecentCollectionItem]
    total_collections_count: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Admissions Report
# ---------------------------------------------------------------------------

class AdmissionsStageItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stage: str
    stage_label: str
    count: int
    percentage: float


class AdmissionsReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_inquiries: int
    total_applications: int
    total_under_review: int
    total_admitted: int
    total_enrolled: int
    total_rejected: int
    inquiry_to_app_conversion_pct: float
    app_to_enroll_conversion_pct: float
    stages_breakdown: List[AdmissionsStageItem]
    pending_followups_count: int


# ---------------------------------------------------------------------------
# Academic Report
# ---------------------------------------------------------------------------

class ClassPerformanceSummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    class_id: UUID
    class_name: str
    section_id: Optional[UUID] = None
    section_name: Optional[str] = None
    total_report_cards: int
    published_count: int
    draft_count: int
    average_score_pct: float
    average_gpa: Optional[float] = None
    pass_rate_pct: float


class AcademicReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_report_cards: int
    total_published: int
    total_draft: int
    overall_publication_pct: float
    overall_average_score_pct: float
    overall_pass_rate_pct: float
    by_class_section: List[ClassPerformanceSummaryItem]
    total_items: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Operations Report
# ---------------------------------------------------------------------------

class TransportOperationsSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_vehicles: int
    total_routes: int
    total_assigned_students: int
    active_vehicles_count: int


class LibraryOperationsSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_books: int
    active_loans_count: int
    overdue_loans_count: int
    available_copies_count: int


class InventoryOperationsSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_items: int
    low_stock_items_count: int
    out_of_stock_items_count: int
    total_inventory_valuation: float


class HostelOperationsSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_rooms: int
    total_bed_capacity: int
    occupied_beds_count: int
    available_beds_count: int
    occupancy_rate_pct: float


class NotificationOperationsSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_notifications_sent: int
    delivered_count: int
    pending_count: int
    failed_count: int
    delivery_success_rate_pct: float


class OperationsReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transport: TransportOperationsSummary
    library: LibraryOperationsSummary
    inventory: InventoryOperationsSummary
    hostel: HostelOperationsSummary
    notifications: NotificationOperationsSummary
