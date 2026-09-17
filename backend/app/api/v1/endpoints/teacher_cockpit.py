"""
Teacher Classroom Command Cockpit Endpoints — Phase 30.3
GET /api/v1/teacher-cockpit
GET /api/v1/teacher-cockpit/summary
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.responses import ApiResponse
from app.dependencies import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.permission import IdentityPermission
from app.identity.models.role_permission import IdentityRolePermission
from app.identity.models.user import IdentityUser
from app.identity.models.user_role import IdentityUserRole
from app.schemas.teacher_cockpit import TeacherCockpitResponse
from app.services.teacher_cockpit_service import teacher_cockpit_service

router = APIRouter()


def _get_user_permission_names(db: Session, user_id: UUID) -> set[str]:
    stmt = (
        select(IdentityPermission.name)
        .join(IdentityRolePermission, IdentityPermission.id == IdentityRolePermission.permission_id)
        .join(IdentityUserRole, IdentityRolePermission.role_id == IdentityUserRole.role_id)
        .where(
            IdentityUserRole.user_id == user_id,
            IdentityPermission.is_deleted.is_(False),
        )
    )
    return set(db.scalars(stmt).all())


@router.get(
    "",
    summary="Get Teacher Classroom Command Cockpit Consolidated Workspace",
    response_model=dict,
)
def get_teacher_cockpit(
    target_date: Optional[date] = Query(None, description="Optional target evaluation date (YYYY-MM-DD)"),
    current_user: IdentityUser = Depends(require_permission("teacher_cockpit.view")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Returns full consolidated operational data for teacher classroom command cockpit:
    - Teacher profile and school context
    - Today's period timetable schedule with status and substitution indicators
    - Current class in session and immediate next upcoming class
    - Class/section attendance status for today's roster
    - Active homework and submission reviews pending
    - Upcoming exams within teacher's scope
    - Actionable operational alerts
    - Role-aware quick action capabilities
    """
    perm_names = _get_user_permission_names(db, current_user.id)

    full_name = f"{current_user.first_name} {current_user.last_name or ''}".strip()
    cockpit_data = teacher_cockpit_service.get_cockpit_data(
        db=db,
        school_id=current_user.school_id,
        current_user_id=current_user.id,
        current_user_email=current_user.email,
        current_user_name=full_name,
        user_permissions=perm_names,
        target_date=target_date,
    )

    return ApiResponse.success(
        message="Teacher cockpit data retrieved successfully.",
        data=cockpit_data.model_dump(mode="json"),
    )


@router.get(
    "/summary",
    summary="Get Lightweight Teacher Cockpit Metrics Summary",
    response_model=dict,
)
def get_teacher_cockpit_summary(
    target_date: Optional[date] = Query(None, description="Optional target evaluation date (YYYY-MM-DD)"),
    current_user: IdentityUser = Depends(require_permission("teacher_cockpit.view")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Returns high-level summary KPIs and active alerts for quick cockpit polling.
    """
    perm_names = _get_user_permission_names(db, current_user.id)
    full_name = f"{current_user.first_name} {current_user.last_name or ''}".strip()

    cockpit_data = teacher_cockpit_service.get_cockpit_data(
        db=db,
        school_id=current_user.school_id,
        current_user_id=current_user.id,
        current_user_email=current_user.email,
        current_user_name=full_name,
        user_permissions=perm_names,
        target_date=target_date,
    )

    return ApiResponse.success(
        message="Teacher cockpit summary retrieved successfully.",
        data={
            "today_date": cockpit_data.today_date,
            "day_of_week": cockpit_data.day_of_week,
            "teacher": cockpit_data.teacher.model_dump(mode="json"),
            "summary": cockpit_data.summary.model_dump(mode="json"),
            "current_and_next": cockpit_data.current_and_next.model_dump(mode="json"),
            "alerts": [a.model_dump(mode="json") for a in cockpit_data.alerts],
        },
    )
