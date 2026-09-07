from __future__ import annotations

import uuid
from sqlalchemy.orm import Session

from app.models.ai.ai_audit_log import AIAuditLog
from app.common.logger.logger import get_logger

logger = get_logger(__name__)


class AIAuditService:
    """
    Service for recording immutable AI operational audit logs.
    """

    @classmethod
    def log_ai_event(
        cls,
        db: Session,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        capability: str,
        provider_type: str,
        model_name: str | None,
        prompt_tokens: int,
        completion_tokens: int,
        estimated_cost_usd: float,
        latency_ms: int,
        status: str = "SUCCESS",
        error_message: str | None = None,
    ) -> AIAuditLog:
        try:
            audit_entry = AIAuditLog(
                id=uuid.uuid4(),
                school_id=school_id,
                user_id=user_id,
                capability=capability,
                provider_type=provider_type,
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                estimated_cost_usd=estimated_cost_usd,
                latency_ms=latency_ms,
                status=status,
                error_message=error_message[:1000] if error_message else None,
            )
            db.add(audit_entry)
            db.commit()
            db.refresh(audit_entry)
            return audit_entry
        except Exception as exc:
            db.rollback()
            logger.error("Failed to record AI audit event for school %s: %s", school_id, str(exc))
            raise


ai_audit_service = AIAuditService()
