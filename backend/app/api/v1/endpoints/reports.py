"""
Executive Reports & BI Analytics Endpoints — Phase 30.2
GET /api/v1/reports/*
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.common.responses import ApiResponse
from app.dependencies import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.schemas.reports import (
    AcademicReportResponse,
    AdmissionsReportResponse,
    AttendanceReportResponse,
    ExecutiveSummaryResponse,
    FinanceReportResponse,
    OperationsReportResponse,
    ReportFilterParams,
    StudentEnrollmentReportResponse,
)
from app.services.report_service import report_service

router = APIRouter()


@router.get(
    "/executive-summary",
    summary="Get Executive Overview Summary & KPIs",
    response_model=dict,
)
def get_executive_summary(
    academic_year_id: Optional[UUID] = Query(None, description="Academic year ID filter"),
    academic_term_id: Optional[UUID] = Query(None, description="Academic term ID filter"),
    class_id: Optional[UUID] = Query(None, description="Class ID filter"),
    section_id: Optional[UUID] = Query(None, description="Section ID filter"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    current_user: IdentityUser = Depends(require_permission("reports.view")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    filters = ReportFilterParams(
        academic_year_id=academic_year_id,
        academic_term_id=academic_term_id,
        class_id=class_id,
        section_id=section_id,
        start_date=start_date,
        end_date=end_date,
    )
    summary = report_service.get_executive_summary(
        db=db,
        school_id=current_user.school_id,
        filters=filters,
    )
    return ApiResponse.success(
        message="Executive summary retrieved successfully.",
        data=summary.model_dump(mode="json"),
    )


@router.get(
    "/students",
    summary="Get Student Enrollment & Demographic Report",
    response_model=dict,
)
def get_student_enrollment_report(
    class_id: Optional[UUID] = Query(None, description="Class ID filter"),
    section_id: Optional[UUID] = Query(None, description="Section ID filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: IdentityUser = Depends(require_permission("reports.view")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    filters = ReportFilterParams(
        class_id=class_id,
        section_id=section_id,
        page=page,
        page_size=page_size,
    )
    report = report_service.get_student_enrollment_report(
        db=db,
        school_id=current_user.school_id,
        filters=filters,
    )
    return ApiResponse.success(
        message="Student enrollment report retrieved successfully.",
        data=report.model_dump(mode="json"),
    )


@router.get(
    "/attendance",
    summary="Get Attendance & Absenteeism Analytics Report",
    response_model=dict,
)
def get_attendance_report(
    academic_year_id: Optional[UUID] = Query(None, description="Academic year ID filter"),
    class_id: Optional[UUID] = Query(None, description="Class ID filter"),
    section_id: Optional[UUID] = Query(None, description="Section ID filter"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: IdentityUser = Depends(require_permission("reports.view")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    filters = ReportFilterParams(
        academic_year_id=academic_year_id,
        class_id=class_id,
        section_id=section_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    report = report_service.get_attendance_report(
        db=db,
        school_id=current_user.school_id,
        filters=filters,
    )
    return ApiResponse.success(
        message="Attendance report retrieved successfully.",
        data=report.model_dump(mode="json"),
    )


@router.get(
    "/finance",
    summary="Get Financial & Collections Intelligence Report",
    response_model=dict,
)
def get_finance_report(
    academic_year_id: Optional[UUID] = Query(None, description="Academic year ID filter"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: IdentityUser = Depends(require_permission("reports.view")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    filters = ReportFilterParams(
        academic_year_id=academic_year_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    report = report_service.get_finance_report(
        db=db,
        school_id=current_user.school_id,
        filters=filters,
    )
    return ApiResponse.success(
        message="Finance report retrieved successfully.",
        data=report.model_dump(mode="json"),
    )


@router.get(
    "/admissions",
    summary="Get Admissions Funnel & Pipeline Analytics Report",
    response_model=dict,
)
def get_admissions_report(
    current_user: IdentityUser = Depends(require_permission("reports.view")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    report = report_service.get_admissions_report(
        db=db,
        school_id=current_user.school_id,
    )
    return ApiResponse.success(
        message="Admissions report retrieved successfully.",
        data=report.model_dump(mode="json"),
    )


@router.get(
    "/academic",
    summary="Get Academic Performance & Report Card Status Report",
    response_model=dict,
)
def get_academic_report(
    academic_year_id: Optional[UUID] = Query(None, description="Academic year ID filter"),
    academic_term_id: Optional[UUID] = Query(None, description="Academic term ID filter"),
    class_id: Optional[UUID] = Query(None, description="Class ID filter"),
    section_id: Optional[UUID] = Query(None, description="Section ID filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: IdentityUser = Depends(require_permission("reports.view")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    filters = ReportFilterParams(
        academic_year_id=academic_year_id,
        academic_term_id=academic_term_id,
        class_id=class_id,
        section_id=section_id,
        page=page,
        page_size=page_size,
    )
    report = report_service.get_academic_report(
        db=db,
        school_id=current_user.school_id,
        filters=filters,
    )
    return ApiResponse.success(
        message="Academic report retrieved successfully.",
        data=report.model_dump(mode="json"),
    )


@router.get(
    "/operations",
    summary="Get Operational Domains Health Overview",
    response_model=dict,
)
def get_operations_report(
    current_user: IdentityUser = Depends(require_permission("reports.view")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    report = report_service.get_operations_report(
        db=db,
        school_id=current_user.school_id,
    )
    return ApiResponse.success(
        message="Operations report retrieved successfully.",
        data=report.model_dump(mode="json"),
    )


@router.get(
    "/export/csv",
    summary="Export Domain Report as CSV",
)
def export_report_csv(
    category: str = Query(..., description="Report category (students, attendance, finance, academic, admissions, executive)"),
    academic_year_id: Optional[UUID] = Query(None),
    academic_term_id: Optional[UUID] = Query(None),
    class_id: Optional[UUID] = Query(None),
    section_id: Optional[UUID] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: IdentityUser = Depends(require_permission("reports.export")),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    filters = ReportFilterParams(
        academic_year_id=academic_year_id,
        academic_term_id=academic_term_id,
        class_id=class_id,
        section_id=section_id,
        start_date=start_date,
        end_date=end_date,
    )
    csv_content, filename = report_service.export_report_csv(
        db=db,
        school_id=current_user.school_id,
        category=category.lower(),
        filters=filters,
    )
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
