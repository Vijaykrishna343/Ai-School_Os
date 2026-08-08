"""
Attendance Management Endpoints.

Provides HTTP routes for creating, bulk creating, retrieving, updating, and soft-deleting Attendance entities.
"""

from datetime import date
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.enums import AttendanceStatus
from app.common.responses import ApiResponse
from app.dependencies import get_attendance_service, get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.schemas.attendance import (
    AttendanceBulkCreate,
    AttendanceCreate,
    AttendanceListResponse,
    AttendanceResponse,
    AttendanceUpdate,
)
from app.services.attendance_service import AttendanceService

router = APIRouter()


@router.post(
    "/",
    response_model=dict,
    status_code=HTTPStatus.CREATED,
    summary="Create Attendance Record",
)
def create_attendance(
    attendance_in: AttendanceCreate,
    current_user: IdentityUser = Depends(require_permission("attendance.create")),
    db: Session = Depends(get_db),
    service: AttendanceService = Depends(get_attendance_service),
) -> dict[str, object]:
    """
    Create an individual daily attendance record for a student.
    """
    created = service.create_attendance(
        db,
        current_user=current_user,
        attendance_in=attendance_in,
    )

    return ApiResponse.success(
        message="Attendance record created successfully.",
        data=AttendanceResponse.model_validate(created).model_dump(),
    )


@router.post(
    "/bulk",
    response_model=dict,
    status_code=HTTPStatus.CREATED,
    summary="Bulk Create Section Attendance",
)
def create_bulk_attendance(
    bulk_in: AttendanceBulkCreate,
    current_user: IdentityUser = Depends(require_permission("attendance.create")),
    db: Session = Depends(get_db),
    service: AttendanceService = Depends(get_attendance_service),
) -> dict[str, object]:
    """
    Mark daily attendance for an entire class/section in a single atomic transaction.
    """
    created_list = service.create_bulk_attendance(
        db,
        current_user=current_user,
        bulk_in=bulk_in,
    )

    items = [AttendanceResponse.model_validate(item).model_dump() for item in created_list]
    return ApiResponse.success(
        message=f"Successfully marked attendance for {len(items)} student(s).",
        data={"items": items, "count": len(items)},
    )


@router.get(
    "/",
    response_model=dict,
    summary="List Attendance Records",
)
def list_attendance(
    section_id: UUID | None = Query(default=None, description="Filter by Section ID"),
    school_class_id: UUID | None = Query(default=None, description="Filter by Class ID"),
    student_id: UUID | None = Query(default=None, description="Filter by Student ID"),
    attendance_date: date | None = Query(default=None, description="Filter by Date"),
    status: AttendanceStatus | None = Query(default=None, description="Filter by Attendance Status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Page size"),
    current_user: IdentityUser = Depends(require_permission("attendance.view")),
    db: Session = Depends(get_db),
    service: AttendanceService = Depends(get_attendance_service),
) -> dict[str, object]:
    """
    Retrieve paginated attendance records filtered by section, class, student, date, or status.
    """
    items, total, total_pages = service.list_attendance(
        db,
        current_user=current_user,
        section_id=section_id,
        school_class_id=school_class_id,
        student_id=student_id,
        attendance_date=attendance_date,
        status=status,
        page=page,
        page_size=page_size,
    )

    response_data = AttendanceListResponse(
        items=[AttendanceResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

    return ApiResponse.success(
        message="Attendance records retrieved successfully.",
        data=response_data.model_dump(),
    )


@router.get(
    "/{attendance_id}",
    response_model=dict,
    summary="Get Attendance Record",
)
def get_attendance(
    attendance_id: UUID,
    current_user: IdentityUser = Depends(require_permission("attendance.view")),
    db: Session = Depends(get_db),
    service: AttendanceService = Depends(get_attendance_service),
) -> dict[str, object]:
    """
    Retrieve details of a specific attendance record by ID.
    """
    attendance = service.get_attendance(
        db,
        current_user=current_user,
        attendance_id=attendance_id,
    )

    return ApiResponse.success(
        message="Attendance record retrieved successfully.",
        data=AttendanceResponse.model_validate(attendance).model_dump(),
    )


@router.put(
    "/{attendance_id}",
    response_model=dict,
    summary="Update Attendance Record",
)
def update_attendance(
    attendance_id: UUID,
    update_in: AttendanceUpdate,
    current_user: IdentityUser = Depends(require_permission("attendance.update")),
    db: Session = Depends(get_db),
    service: AttendanceService = Depends(get_attendance_service),
) -> dict[str, object]:
    """
    Update an existing attendance record.
    """
    updated = service.update_attendance(
        db,
        current_user=current_user,
        attendance_id=attendance_id,
        update_in=update_in,
    )

    return ApiResponse.success(
        message="Attendance record updated successfully.",
        data=AttendanceResponse.model_validate(updated).model_dump(),
    )


@router.delete(
    "/{attendance_id}",
    response_model=dict,
    summary="Delete Attendance Record",
)
def delete_attendance(
    attendance_id: UUID,
    current_user: IdentityUser = Depends(require_permission("attendance.delete")),
    db: Session = Depends(get_db),
    service: AttendanceService = Depends(get_attendance_service),
) -> dict[str, object]:
    """
    Soft-delete an existing attendance record.
    """
    service.delete_attendance(
        db,
        current_user=current_user,
        attendance_id=attendance_id,
    )

    return ApiResponse.success(
        message="Attendance record deleted successfully.",
    )
