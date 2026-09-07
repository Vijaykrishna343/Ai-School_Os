"""
API Endpoints for Phase 12.4 Explainable Student Academic Risk & Attendance Analytics.
"""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.ai.schemas.risk_analytics import (
    StudentRiskAssessmentResponse,
    SectionRiskSummaryResponse,
    SchoolRiskSummaryResponse,
)
from app.ai.services.ai_risk_analytics_service import ai_risk_analytics_service
from app.dependencies.database import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser

router = APIRouter(prefix="/ai/risk", tags=["AI Academic Risk Analytics"])


@router.post(
    "/assess/student/{student_id}",
    response_model=StudentRiskAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("ai.risk.view"))],
)
def assess_student_risk(
    student_id: uuid.UUID,
    academic_year_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("ai.risk.view")),
) -> Any:
    """
    Calculates and returns an explainable academic risk assessment for an individual student.
    """
    return ai_risk_analytics_service.calculate_student_risk(
        db=db,
        current_user=current_user,
        student_id=student_id,
        academic_year_id=academic_year_id,
    )


@router.post(
    "/assess/section/{section_id}",
    response_model=List[StudentRiskAssessmentResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("ai.risk.view"))],
)
def assess_section_risk(
    section_id: uuid.UUID,
    academic_year_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("ai.risk.view")),
) -> Any:
    """
    Batch calculates academic risk assessments for all active students in a section.
    """
    return ai_risk_analytics_service.calculate_section_risk(
        db=db,
        current_user=current_user,
        section_id=section_id,
        academic_year_id=academic_year_id,
    )


@router.get(
    "/student/{student_id}",
    response_model=StudentRiskAssessmentResponse,
    dependencies=[Depends(require_permission("ai.risk.view"))],
)
def get_student_risk(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("ai.risk.view")),
) -> Any:
    """
    Retrieves the latest stored risk assessment for a student (calculating on-the-fly if missing).
    """
    return ai_risk_analytics_service.get_student_latest_risk(
        db=db,
        current_user=current_user,
        student_id=student_id,
    )


@router.get(
    "/section/{section_id}",
    response_model=SectionRiskSummaryResponse,
    dependencies=[Depends(require_permission("ai.risk.view"))],
)
def get_section_risk_summary(
    section_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("ai.risk.view")),
) -> Any:
    """
    Retrieves section academic risk distribution summary.
    """
    return ai_risk_analytics_service.get_section_risk_summary(
        db=db,
        current_user=current_user,
        section_id=section_id,
    )


@router.get(
    "/summary",
    response_model=SchoolRiskSummaryResponse,
    dependencies=[Depends(require_permission("ai.risk.view"))],
)
def get_school_risk_summary(
    academic_year_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("ai.risk.view")),
) -> Any:
    """
    Retrieves school-wide academic risk distribution summary.
    """
    return ai_risk_analytics_service.get_school_risk_summary(
        db=db,
        current_user=current_user,
        academic_year_id=academic_year_id,
    )
