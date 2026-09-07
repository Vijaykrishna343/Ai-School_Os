"""
AI Communication Draft API Endpoints for Phase 12.5.
Provides endpoints for AI multi-channel announcement and notice draft generation.
"""

from __future__ import annotations

import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.identity.models.user import IdentityUser
from app.identity.dependencies.require_permission import require_permission
from app.ai.schemas.communication import (
    GenerateCommunicationDraftRequest,
    CommunicationDraftResponse,
    CommunicationDraftListResponse,
)
from app.ai.services.ai_communication_draft_service import ai_communication_draft_service

router = APIRouter(prefix="/ai/communication", tags=["AI Subsystem - Communication Drafting"])


@router.post(
    "/draft",
    response_model=CommunicationDraftResponse,
    summary="Generate Multi-Channel AI Communication Draft",
)
def generate_communication_draft(
    request_data: GenerateCommunicationDraftRequest,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("ai.communication.draft")),
) -> CommunicationDraftResponse:
    """
    Generate an AI multi-channel communication draft proposal.
    Enforces RBAC ('ai.communication.draft'), tenant boundary, token quota limits, PII minimization, and audit logging.
    """
    draft = ai_communication_draft_service.generate_draft(
        db=db,
        current_user=current_user,
        category=request_data.category,
        target_audience=request_data.target_audience,
        tone=request_data.tone,
        key_details=request_data.key_details,
        requested_channels=request_data.requested_channels,
    )
    return draft


@router.get(
    "/drafts",
    response_model=CommunicationDraftListResponse,
    summary="List AI Communication Drafts",
)
def list_communication_drafts(
    category: Optional[str] = Query(None, description="Optional category filter"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("ai.communication.draft")),
) -> CommunicationDraftListResponse:
    """
    List recent AI communication drafts for the current school.
    """
    drafts = ai_communication_draft_service.list_drafts(
        db=db,
        current_user=current_user,
        category=category,
        limit=limit,
        offset=offset,
    )
    return CommunicationDraftListResponse(
        total=len(drafts),
        drafts=drafts,
    )


@router.get(
    "/draft/{draft_id}",
    response_model=CommunicationDraftResponse,
    summary="Get Specific AI Communication Draft",
)
def get_communication_draft(
    draft_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("ai.communication.draft")),
) -> CommunicationDraftResponse:
    """
    Retrieve a specific AI communication draft by ID.
    """
    draft = ai_communication_draft_service.get_draft(
        db=db,
        current_user=current_user,
        draft_id=draft_id,
    )
    return draft
