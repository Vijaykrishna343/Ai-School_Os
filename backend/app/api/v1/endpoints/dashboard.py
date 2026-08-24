"""
Admin Dashboard Summary Endpoints.

Provides HTTP routes for retrieving admin/principal dashboard summary metrics.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.responses import ApiResponse
from app.dependencies import (
    get_dashboard_service,
    get_db,
)
from app.identity.dependencies.require_permission import require_permission
from app.identity.security.current_user import get_current_user
from app.identity.models.user import IdentityUser
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get(
    "/admin/summary",
    response_model=dict,
    summary="Get Admin Dashboard Summary",
)
def get_admin_dashboard_summary(
    current_user: IdentityUser = Depends(require_permission("school.view")),
    db: Session = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict[str, object]:
    """
    Get aggregated summary metrics for the authenticated user's tenant school.
    """
    summary = service.get_admin_summary(
        db,
        school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="Admin dashboard summary retrieved successfully.",
        data=summary.model_dump(mode="json"),
    )


@router.get(
    "/teacher/summary",
    response_model=dict,
    summary="Get Teacher Dashboard Summary",
)
def get_teacher_dashboard_summary(
    current_user: IdentityUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict[str, object]:
    """
    Get operational teacher summary metrics for authenticated user.
    Does NOT require administrative school.view permission.
    """
    summary = service.get_teacher_summary(
        db,
        user=current_user,
    )

    return ApiResponse.success(
        message="Teacher dashboard summary retrieved successfully.",
        data=summary.model_dump(mode="json"),
    )


@router.get(
    "/parent/summary",
    response_model=dict,
    summary="Get Parent Dashboard Summary",
)
def get_parent_dashboard_summary(
    student_id: Optional[UUID] = Query(None, description="Optional target child student ID for multi-child switching"),
    current_user: IdentityUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict[str, object]:
    """
    Get aggregated portal summary for authenticated parent user.
    Strictly enforces relationship authorization for target student ID.
    Handles multi-child switching and zero-child states.
    """
    summary = service.get_parent_summary(
        db,
        user=current_user,
        requested_student_id=student_id,
    )

    return ApiResponse.success(
        message="Parent dashboard summary retrieved successfully.",
        data=summary.model_dump(mode="json"),
    )


@router.get(
    "/student/summary",
    response_model=dict,
    summary="Get Student Dashboard Summary",
)
def get_student_dashboard_summary(
    current_user: IdentityUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict[str, object]:
    """
    Get self-service portal summary for authenticated student user.
    Strictly enforces Student -> Self relationship authorization.
    """
    summary = service.get_student_summary(
        db,
        user=current_user,
    )

    return ApiResponse.success(
        message="Student dashboard summary retrieved successfully.",
        data=summary.model_dump(mode="json"),
    )

