"""
Admin Dashboard Summary Endpoints.

Provides HTTP routes for retrieving admin/principal dashboard summary metrics.
"""

from fastapi import APIRouter, Depends
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
