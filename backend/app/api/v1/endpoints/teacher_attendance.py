from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.common.enums import AttendanceStatus
from app.common.responses import ApiResponse
from app.dependencies import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.security.current_user import get_current_user
from app.identity.models.user import IdentityUser
from app.schemas.teacher.teacher_attendance import (
    TeacherAttendanceUpdate,
    BulkTeacherAttendanceRequest,
)
from app.services.teacher_attendance_service import teacher_attendance_service

router = APIRouter()


@router.get("", summary="List Teacher Attendance")
def list_teacher_attendance(
    attendance_date: date = Query(default_factory=date.today),
    status_filter: AttendanceStatus | None = Query(default=None, alias="status"),
    current_user: IdentityUser = Depends(require_permission("teacher_attendance.view")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    results = teacher_attendance_service.list_attendance(
        db,
        school_id=current_user.school_id,
        attendance_date=attendance_date,
        status=status_filter,
    )
    return ApiResponse.success(
        message="Teacher attendance retrieved successfully.",
        data=[r.model_dump(mode="json") for r in results],
    )


@router.get("/summary", summary="Get Teacher Attendance Summary")
def get_teacher_attendance_summary(
    attendance_date: date = Query(default_factory=date.today),
    current_user: IdentityUser = Depends(require_permission("teacher_attendance.view")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    summary = teacher_attendance_service.get_summary(
        db,
        school_id=current_user.school_id,
        attendance_date=attendance_date,
    )
    return ApiResponse.success(
        message="Teacher attendance summary retrieved successfully.",
        data=summary.model_dump(mode="json"),
    )


@router.post("/bulk", summary="Bulk Mark Teacher Attendance", status_code=status.HTTP_200_OK)
def bulk_mark_teacher_attendance(
    body: BulkTeacherAttendanceRequest,
    current_user: IdentityUser = Depends(require_permission("teacher_attendance.create")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    results = teacher_attendance_service.bulk_mark_attendance(
        db,
        school_id=current_user.school_id,
        data=body,
    )
    return ApiResponse.success(
        message="Bulk teacher attendance marked successfully.",
        data=[r.model_dump(mode="json") for r in results],
    )


@router.put("/{attendance_id}", summary="Update Teacher Attendance")
def update_teacher_attendance(
    attendance_id: UUID,
    body: TeacherAttendanceUpdate,
    current_user: IdentityUser = Depends(require_permission("teacher_attendance.update")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    result = teacher_attendance_service.update_attendance(
        db,
        school_id=current_user.school_id,
        attendance_id=attendance_id,
        data=body,
    )
    return ApiResponse.success(
        message="Teacher attendance updated successfully.",
        data=result.model_dump(mode="json"),
    )


@router.post("/check-in", summary="Teacher Self Check-In")
def teacher_check_in(
    current_user: IdentityUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    result = teacher_attendance_service.teacher_check_in(
        db,
        user=current_user,
    )
    return ApiResponse.success(
        message="Staff check-in recorded successfully.",
        data=result.model_dump(mode="json"),
    )


@router.post("/check-out", summary="Teacher Self Check-Out")
def teacher_check_out(
    current_user: IdentityUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    result = teacher_attendance_service.teacher_check_out(
        db,
        user=current_user,
    )
    return ApiResponse.success(
        message="Staff check-out recorded successfully.",
        data=result.model_dump(mode="json"),
    )
