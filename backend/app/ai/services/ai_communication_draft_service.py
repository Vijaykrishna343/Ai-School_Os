"""
AI Communication Draft Service for Phase 12.5.
Handles multi-channel communication drafting, PII sanitization, tenant isolation,
quota deduction, database persistence, and audit logging.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.ai.communication.engine import (
    AICommunicationDraftEngine,
    CommunicationDraftInput,
    CommunicationDraftOutput,
    ai_communication_draft_engine,
)
from app.ai.security.data_minimizer import AIDataMinimizer
from app.ai.security.tenant_boundary import AITenantBoundaryService
from app.ai.services.ai_audit_service import ai_audit_service
from app.ai.services.ai_usage_service import ai_usage_service
from app.common.exceptions import ForbiddenException, NotFoundException, BadRequestException
from app.identity.models import IdentityUser
from app.models.ai import AICommunicationDraft
from app.models.school import School


class AICommunicationDraftService:
    """
    Service orchestrating multi-channel AI announcement & notice draft generation.
    """

    AUTHORIZED_ROLES = {
        "Super Admin",
        "School Admin",
        "Principal",
        "Vice Principal",
        "Teacher",
    }

    def __init__(self, engine: AICommunicationDraftEngine = ai_communication_draft_engine):
        self.engine = engine

    def _verify_user_role_scope(self, current_user: IdentityUser) -> None:
        """
        Verifies authorized role for drafting school communications.
        """
        role_names = {r.name for r in current_user.roles}
        if not role_names.intersection(self.AUTHORIZED_ROLES):
            raise ForbiddenException("User role is not authorized to draft school communications using AI.")

    def generate_draft(
        self,
        db: Session,
        current_user: IdentityUser,
        category: str,
        target_audience: str,
        tone: str,
        key_details: str,
        requested_channels: Optional[List[str]] = None,
    ) -> AICommunicationDraft:
        """
        Generates and persists a multi-channel communication draft proposal.
        """
        school_id = AITenantBoundaryService.validate_and_get_school_id(current_user)
        self._verify_user_role_scope(current_user)

        if not key_details or not key_details.strip():
            raise BadRequestException("Key details or topic context is required for draft generation.")

        # 1. PII Minimization & Sanitization
        sanitized_details, redact_log = AIDataMinimizer.sanitize_text(key_details)

        # 2. Check Monthly Token Quota
        ai_usage_service.check_and_reserve_quota(db, school_id)

        # 3. Retrieve School Name for Context
        school = db.query(School).filter(School.id == school_id, School.is_deleted == False).first()
        school_name = school.name if school else "School"

        channels = requested_channels if requested_channels else ["SMS", "EMAIL", "WHATSAPP", "IN_APP"]

        # 4. Engine Generation
        input_data = CommunicationDraftInput(
            category=category,
            target_audience=target_audience,
            tone=tone,
            key_details=sanitized_details,
            school_name=school_name,
            requested_channels=channels,
        )

        output: CommunicationDraftOutput = self.engine.generate(input_data)

        # Serialize channel variants into JSON dictionary
        channel_variants_json = {
            channel: {
                "title": variant.title,
                "body": variant.body,
            }
            for channel, variant in output.variants.items()
        }

        # 5. Persist Draft Entity in DB
        draft = AICommunicationDraft(
            school_id=school_id,
            created_by_user_id=current_user.id,
            category=output.category,
            target_audience=output.target_audience,
            tone=output.tone,
            prompt_summary=sanitized_details,
            channel_variants=channel_variants_json,
            pii_redact_log=redact_log,
            token_count=output.token_count,
            status="DRAFT",
            assessed_at=datetime.now(timezone.utc),
        )

        db.add(draft)
        db.commit()
        db.refresh(draft)

        # 6. Deduct Token Quota & Record Audit Log
        ai_usage_service.record_usage(db, school_id, output.token_count)
        ai_audit_service.log_ai_event(
            db=db,
            school_id=school_id,
            user_id=current_user.id,
            capability="COMMUNICATION_DRAFT",
            provider_type="MOCK",
            model_name="deterministic-draft-v1",
            prompt_tokens=max(10, output.token_count // 2),
            completion_tokens=max(10, output.token_count // 2),
            estimated_cost_usd=0.0000,
            latency_ms=15,
            status="SUCCESS",
        )

        return draft

    def get_draft(
        self,
        db: Session,
        current_user: IdentityUser,
        draft_id: uuid.UUID,
    ) -> AICommunicationDraft:
        """
        Retrieves a specific communication draft by ID with multi-tenant boundary check.
        """
        school_id = AITenantBoundaryService.validate_and_get_school_id(current_user)
        self._verify_user_role_scope(current_user)

        draft = db.query(AICommunicationDraft).filter(
            AICommunicationDraft.id == draft_id,
            AICommunicationDraft.school_id == school_id,
            AICommunicationDraft.is_deleted == False,
        ).first()

        if not draft:
            raise NotFoundException("AI Communication draft record not found.")

        return draft

    def list_drafts(
        self,
        db: Session,
        current_user: IdentityUser,
        category: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[AICommunicationDraft]:
        """
        Lists recent communication drafts for the current school.
        """
        school_id = AITenantBoundaryService.validate_and_get_school_id(current_user)
        self._verify_user_role_scope(current_user)

        query = db.query(AICommunicationDraft).filter(
            AICommunicationDraft.school_id == school_id,
            AICommunicationDraft.is_deleted == False,
        )

        if category:
            query = query.filter(AICommunicationDraft.category == category.upper())

        return query.order_by(desc(AICommunicationDraft.created_at)).offset(offset).limit(limit).all()


ai_communication_draft_service = AICommunicationDraftService()
