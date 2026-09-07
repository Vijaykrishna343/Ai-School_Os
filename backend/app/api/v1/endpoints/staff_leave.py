from __future__ import annotations

from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.common.responses import ApiResponse
from app.dependencies import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.schemas.staff_leave import (
    StaffLeaveTypeCreate,
    StaffLeaveTypeUpdate,
    StaffLeaveTypeResponse,
    StaffLeaveBalanceResponse,
    StaffLeaveBalanceAllocate,
    StaffLeaveRequestCreate,
    StaffLeaveRequestUpdate,
    StaffLeaveApprovalAction,
    StaffLeaveRejectAction,
    StaffLeaveRequestResponse,
    StaffLeaveSummaryReport,
)
from app.services.staff_leave_service import staff_leave_service

router = APIRouter()


# ── LEAVE TYPES ─────────────────────────────────────────────────────────────

@router.get(
    "/types",
    summary="Get Staff Leave Types",
    response_model=dict[str, object],
)
def get_leave_types(
    current_user: IdentityUser = Depends(require_permission("staff_leave.view")),
    db: Session = Depends(get_db),
):
    types = staff_leave_service.get_leave_types(db, current_user.school_id)
    data = [StaffLeaveTypeResponse.model_validate(t).model_dump(mode="json") for t in types]
    return ApiResponse.success(data=data)


@router.post(
    "/types",
    summary="Create Custom Leave Type",
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, object],
)
def create_leave_type(
    payload: StaffLeaveTypeCreate,
    current_user: IdentityUser = Depends(require_permission("staff_leave.manage")),
    db: Session = Depends(get_db),
):
    lt = staff_leave_service.create_leave_type(db, current_user.school_id, payload)
    data = StaffLeaveTypeResponse.model_validate(lt).model_dump(mode="json")
    return ApiResponse.success(data=data, message="Leave type created successfully.")


@router.put(
    "/types/{type_id}",
    summary="Update Leave Type Policy",
    response_model=dict[str, object],
)
def update_leave_type(
    type_id: UUID,
    payload: StaffLeaveTypeUpdate,
    current_user: IdentityUser = Depends(require_permission("staff_leave.manage")),
    db: Session = Depends(get_db),
):
    lt = staff_leave_service.update_leave_type(db, current_user.school_id, type_id, payload)
    data = StaffLeaveTypeResponse.model_validate(lt).model_dump(mode="json")
    return ApiResponse.success(data=data, message="Leave type updated successfully.")


# ── LEAVE BALANCES ──────────────────────────────────────────────────────────

@router.get(
    "/balance",
    summary="Get Current User Leave Balances",
    response_model=dict[str, object],
)
def get_my_leave_balances(
    academic_year_id: UUID = Query(...),
    current_user: IdentityUser = Depends(require_permission("staff_leave.balance.view")),
    db: Session = Depends(get_db),
):
    teacher = staff_leave_service._resolve_teacher_for_user(db, current_user.school_id, current_user)
    balances = staff_leave_service.get_teacher_leave_balances(db, current_user.school_id, teacher.id, academic_year_id)
    data = [b.model_dump(mode="json") for b in balances]
    return ApiResponse.success(data=data)


@router.get(
    "/balance/{teacher_id}",
    summary="Get Teacher Leave Balances",
    response_model=dict[str, object],
)
def get_teacher_leave_balances(
    teacher_id: UUID,
    academic_year_id: UUID = Query(...),
    current_user: IdentityUser = Depends(require_permission("staff_leave.balance.view")),
    db: Session = Depends(get_db),
):
    balances = staff_leave_service.get_teacher_leave_balances(db, current_user.school_id, teacher_id, academic_year_id)
    data = [b.model_dump(mode="json") for b in balances]
    return ApiResponse.success(data=data)


@router.post(
    "/balances/allocate",
    summary="Allocate Teacher Leave Quota",
    response_model=dict[str, object],
)
def allocate_leave_balance(
    payload: StaffLeaveBalanceAllocate,
    current_user: IdentityUser = Depends(require_permission("staff_leave.manage")),
    db: Session = Depends(get_db),
):
    bal = staff_leave_service.allocate_leave_balance(db, current_user.school_id, payload)
    return ApiResponse.success(data=bal.model_dump(mode="json"), message="Leave quota allocated successfully.")


# ── LEAVE REPORTS & SUMMARY ───────────────────────────────────────────────────

@router.get(
    "/reports/summary",
    summary="Get Staff Leave Analytics & Summary Report",
    response_model=dict[str, object],
)
def get_leave_summary_report(
    academic_year_id: UUID = Query(...),
    current_user: IdentityUser = Depends(require_permission("staff_leave.report.view")),
    db: Session = Depends(get_db),
):
    report = staff_leave_service.get_leave_summary_report(db, current_user.school_id, academic_year_id)
    return ApiResponse.success(data=report.model_dump(mode="json"))


# ── LEAVE REQUEST WORKFLOW ──────────────────────────────────────────────────

@router.post(
    "",
    summary="Submit Staff Leave Request",
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, object],
)
def create_leave_request(
    payload: StaffLeaveRequestCreate,
    current_user: IdentityUser = Depends(require_permission("staff_leave.create")),
    db: Session = Depends(get_db),
):
    req_res = staff_leave_service.create_leave_request(db, current_user.school_id, current_user, payload)
    return ApiResponse.success(data=req_res.model_dump(mode="json"), message="Leave request submitted successfully.")


@router.get(
    "",
    summary="List Staff Leave Requests",
    response_model=dict[str, object],
)
def get_leave_requests(
    teacher_id: UUID | None = Query(None),
    status: str | None = Query(None),
    leave_type_id: UUID | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    academic_year_id: UUID | None = Query(None),
    current_user: IdentityUser = Depends(require_permission("staff_leave.view")),
    db: Session = Depends(get_db),
):
    reqs = staff_leave_service.get_leave_requests(
        db=db,
        school_id=current_user.school_id,
        current_user=current_user,
        teacher_id=teacher_id,
        status=status,
        leave_type_id=leave_type_id,
        start_date=start_date,
        end_date=end_date,
        academic_year_id=academic_year_id,
    )
    data = [r.model_dump(mode="json") for r in reqs]
    return ApiResponse.success(data=data)


@router.get(
    "/{id}",
    summary="Get Leave Request Details",
    response_model=dict[str, object],
)
def get_leave_request_by_id(
    id: UUID,
    current_user: IdentityUser = Depends(require_permission("staff_leave.view")),
    db: Session = Depends(get_db),
):
    req_res = staff_leave_service.get_leave_request_by_id(db, current_user.school_id, id, current_user)
    return ApiResponse.success(data=req_res.model_dump(mode="json"))


@router.post(
    "/{id}/approve",
    summary="Approve Staff Leave Request",
    response_model=dict[str, object],
)
def approve_leave_request(
    id: UUID,
    payload: StaffLeaveApprovalAction = StaffLeaveApprovalAction(),
    current_user: IdentityUser = Depends(require_permission("staff_leave.approve")),
    db: Session = Depends(get_db),
):
    req_res = staff_leave_service.approve_leave_request(db, current_user.school_id, current_user, id, payload.remarks)
    return ApiResponse.success(data=req_res.model_dump(mode="json"), message="Leave request approved successfully.")


@router.post(
    "/{id}/reject",
    summary="Reject Staff Leave Request",
    response_model=dict[str, object],
)
def reject_leave_request(
    id: UUID,
    payload: StaffLeaveRejectAction,
    current_user: IdentityUser = Depends(require_permission("staff_leave.reject")),
    db: Session = Depends(get_db),
):
    req_res = staff_leave_service.reject_leave_request(db, current_user.school_id, current_user, id, payload.rejection_reason)
    return ApiResponse.success(data=req_res.model_dump(mode="json"), message="Leave request rejected successfully.")


@router.post(
    "/{id}/cancel",
    summary="Cancel Staff Leave Request",
    response_model=dict[str, object],
)
def cancel_leave_request(
    id: UUID,
    payload: StaffLeaveApprovalAction = StaffLeaveApprovalAction(),
    current_user: IdentityUser = Depends(require_permission("staff_leave.cancel")),
    db: Session = Depends(get_db),
):
    req_res = staff_leave_service.cancel_leave_request(db, current_user.school_id, current_user, id, payload.remarks)
    return ApiResponse.success(data=req_res.model_dump(mode="json"), message="Leave request cancelled successfully.")
