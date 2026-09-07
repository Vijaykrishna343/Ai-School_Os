from __future__ import annotations

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.identity.models.user import IdentityUser
from app.identity.security.current_user import get_current_user
from app.identity.dependencies.require_permission import require_permission
from app.ai.schemas.timetable_draft import (
    TimetableGenerateRequest,
    AITimetableDraftResponse,
)
from app.ai.services.ai_timetable_service import ai_timetable_service

router = APIRouter(prefix="/ai/timetable", tags=["AI Timetable Generator"])


@router.post(
    "/generate",
    response_model=AITimetableDraftResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI Timetable Draft with CP-SAT Solver",
)
def generate_timetable_draft(
    request_data: TimetableGenerateRequest,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("ai.timetable.generate")),
) -> AITimetableDraftResponse:
    """
    Constructs an AI timetable draft using Google OR-Tools CP-SAT constraint optimization.
    Returns a draft schedule and deterministic validation report. Does not publish directly.
    """
    draft = ai_timetable_service.generate_draft(
        db=db,
        current_user=current_user,
        academic_year_id=request_data.academic_year_id,
        name=request_data.name,
        timeout_seconds=request_data.timeout_seconds,
        class_section_ids=request_data.class_section_ids,
    )
    return draft


@router.get(
    "/drafts",
    response_model=list[AITimetableDraftResponse],
    summary="List AI Timetable Drafts",
)
def list_timetable_drafts(
    academic_year_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("ai.timetable.generate")),
) -> list[AITimetableDraftResponse]:
    """
    List AI timetable drafts for the current tenant school.
    """
    drafts = ai_timetable_service.list_drafts(
        db=db,
        current_user=current_user,
        academic_year_id=academic_year_id,
    )
    return drafts


@router.get(
    "/drafts/{draft_id}",
    response_model=AITimetableDraftResponse,
    summary="Get AI Timetable Draft Details & Validation Report",
)
def get_timetable_draft(
    draft_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("ai.timetable.generate")),
) -> AITimetableDraftResponse:
    """
    Retrieve specific AI timetable draft with entries and validation summary.
    """
    return ai_timetable_service.get_draft(db, current_user, draft_id)


@router.post(
    "/drafts/{draft_id}/approve",
    response_model=AITimetableDraftResponse,
    summary="Approve AI Timetable Draft",
)
def approve_timetable_draft(
    draft_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("ai.timetable.generate")),
) -> AITimetableDraftResponse:
    """
    Human approval step for a valid AI timetable draft. Transitions status SOLVED -> APPROVED.
    """
    return ai_timetable_service.approve_draft(db, current_user, draft_id)


@router.post(
    "/drafts/{draft_id}/publish",
    response_model=AITimetableDraftResponse,
    summary="Publish Approved AI Timetable",
)
def publish_timetable_draft(
    draft_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.publish")),
) -> AITimetableDraftResponse:
    """
    Publish approved AI timetable draft to production Timetable and TimetableEntry records.
    Requires explicit 'timetable.publish' authorization. Transitions status APPROVED -> PUBLISHED.
    """
    return ai_timetable_service.publish_draft(db, current_user, draft_id)
