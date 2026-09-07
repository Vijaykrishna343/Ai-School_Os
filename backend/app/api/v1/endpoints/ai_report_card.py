"""
AI Report Card Remarks API Endpoints for Phase 12.6.
Provides endpoints for AI qualitative student performance remarks synthesis and application.
"""

from __future__ import annotations

import uuid
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.identity.models.user import IdentityUser
from app.identity.dependencies.require_permission import require_permission
from app.ai.schemas.report_card import (
    GenerateReportCardRemarksRequest,
    ApplyReportCardRemarksRequest,
    ReportCardRemarksResponse,
)
from app.ai.services.ai_report_card_remarks_service import ai_report_card_remarks_service
from app.schemas.grading.report_card import ReportCardResponse

router = APIRouter(prefix="/ai/report-card", tags=["AI Subsystem - Report Card Remarks"])


@router.post(
    "/remarks/generate",
    response_model=ReportCardRemarksResponse,
    summary="Generate AI Qualitative Report Card Remarks",
)
def generate_report_card_remarks(
    request_data: GenerateReportCardRemarksRequest,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("report_card.edit_remarks")),
) -> ReportCardRemarksResponse:
    """
    Synthesize subject marks, attendance, and risk factors into qualitative draft remarks.
    Enforces RBAC ('report_card.edit_remarks'), tenant boundary, token quota limits, PII minimization, and audit logging.
    """
    remark = ai_report_card_remarks_service.generate_remarks(
        db=db,
        current_user=current_user,
        report_card_id=request_data.report_card_id,
        tone=request_data.tone,
        detail_level=request_data.detail_level,
    )
    return remark


@router.post(
    "/remarks/apply",
    response_model=ReportCardResponse,
    summary="Apply AI Generated Remarks to Report Card",
)
def apply_report_card_remarks(
    request_data: ApplyReportCardRemarksRequest,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("report_card.edit_remarks")),
) -> ReportCardResponse:
    """
    Apply generated or edited remarks into official ReportCard.teacher_remarks and principal_remarks.
    """
    report_card = ai_report_card_remarks_service.apply_remark_to_report_card(
        db=db,
        current_user=current_user,
        report_card_id=request_data.report_card_id,
        teacher_remarks=request_data.teacher_remarks,
        principal_remarks=request_data.principal_remarks,
    )
    return report_card


@router.get(
    "/remarks/{report_card_id}",
    response_model=ReportCardRemarksResponse,
    summary="Get AI Remarks Draft for Report Card",
)
def get_report_card_remarks(
    report_card_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("report_card.edit_remarks")),
) -> ReportCardRemarksResponse:
    """
    Retrieve the latest AI generated remarks draft for a specific report card.
    """
    remark = ai_report_card_remarks_service.get_remark(
        db=db,
        current_user=current_user,
        report_card_id=report_card_id,
    )
    return remark
