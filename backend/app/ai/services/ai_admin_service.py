from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import func, select, desc
from sqlalchemy.orm import Session

from app.models.ai.ai_provider_config import AIProviderConfig
from app.models.ai.ai_usage_limit import AIUsageLimit
from app.models.ai.ai_audit_log import AIAuditLog
from app.identity.models.user import IdentityUser
from app.common.exceptions import NotFoundException, BadRequestException
from app.ai.schemas.admin import (
    AIProviderConfigResponse,
    AIProviderConfigUpdate,
    AIUsageLimitUpdate,
    AIAuditLogQueryResponse,
    AIAuditLogItemResponse,
)

VALID_PROVIDERS = {"MOCK", "GEMINI", "OPENAI", "ANTHROPIC", "LOCAL_ORTOOLS"}


class AIAdminService:
    """
    Service layer for AI Subsystem Administration, Provider Management, System Audit & Quota Control.
    """

    def get_provider_config(self, db: Session, school_id: uuid.UUID) -> AIProviderConfigResponse:
        config = db.scalar(
            select(AIProviderConfig).where(AIProviderConfig.school_id == school_id)
        )
        if not config:
            # Create default config for school
            config = AIProviderConfig(
                id=uuid.uuid4(),
                school_id=school_id,
                provider_type="MOCK",
                model_name="mock-default-v1",
                is_enabled=True,
                allow_external_ai=False,
                notes="Default system initialization",
            )
            db.add(config)
            db.commit()
            db.refresh(config)

        return AIProviderConfigResponse.model_validate(config)

    def update_provider_config(
        self, db: Session, school_id: uuid.UUID, data: AIProviderConfigUpdate
    ) -> AIProviderConfigResponse:
        provider_type = data.provider_type.upper()
        if provider_type not in VALID_PROVIDERS:
            raise BadRequestException(
                f"Invalid provider_type '{data.provider_type}'. Allowed: {', '.join(sorted(VALID_PROVIDERS))}"
            )

        config = db.scalar(
            select(AIProviderConfig).where(AIProviderConfig.school_id == school_id)
        )
        if not config:
            config = AIProviderConfig(
                id=uuid.uuid4(),
                school_id=school_id,
                provider_type=provider_type,
                model_name=data.model_name or "mock-default-v1",
                is_enabled=data.is_enabled,
                allow_external_ai=data.allow_external_ai,
                notes=data.notes,
            )
            db.add(config)
        else:
            config.provider_type = provider_type
            if data.model_name is not None:
                config.model_name = data.model_name
            config.is_enabled = data.is_enabled
            config.allow_external_ai = data.allow_external_ai
            if data.notes is not None:
                config.notes = data.notes

        db.commit()
        db.refresh(config)
        return AIProviderConfigResponse.model_validate(config)

    def update_usage_limit(
        self, db: Session, school_id: uuid.UUID, data: AIUsageLimitUpdate
    ) -> dict[str, Any]:
        if data.monthly_token_quota < 0:
            raise BadRequestException("monthly_token_quota must be a non-negative integer.")

        limit = db.scalar(
            select(AIUsageLimit).where(AIUsageLimit.school_id == school_id)
        )
        if not limit:
            from datetime import date, timedelta
            limit = AIUsageLimit(
                id=uuid.uuid4(),
                school_id=school_id,
                monthly_token_quota=data.monthly_token_quota,
                used_tokens_current_month=0,
                quota_reset_date=date.today() + timedelta(days=30),
                is_enabled=data.is_enabled,
            )
            db.add(limit)
        else:
            limit.monthly_token_quota = data.monthly_token_quota
            limit.is_enabled = data.is_enabled

        db.commit()
        db.refresh(limit)

        return {
            "school_id": str(limit.school_id),
            "monthly_token_quota": limit.monthly_token_quota,
            "used_tokens_current_month": limit.used_tokens_current_month,
            "quota_remaining": max(0, limit.monthly_token_quota - limit.used_tokens_current_month),
            "quota_reset_date": str(limit.quota_reset_date),
            "is_enabled": limit.is_enabled,
        }

    def query_audit_logs(
        self,
        db: Session,
        school_id: uuid.UUID,
        capability: str | None = None,
        status: str | None = None,
        provider_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AIAuditLogQueryResponse:
        if limit < 1 or limit > 200:
            raise BadRequestException("limit parameter must be between 1 and 200.")
        if offset < 0:
            raise BadRequestException("offset parameter must be non-negative.")

        # Base query filtered strictly by tenant
        base_query = select(AIAuditLog, IdentityUser).join(
            IdentityUser, AIAuditLog.user_id == IdentityUser.id
        ).where(AIAuditLog.school_id == school_id)

        if capability:
            base_query = base_query.where(AIAuditLog.capability == capability.upper())
        if status:
            base_query = base_query.where(AIAuditLog.status == status.upper())
        if provider_type:
            base_query = base_query.where(AIAuditLog.provider_type == provider_type.upper())

        # Count & aggregation query
        count_stmt = select(
            func.count(AIAuditLog.id),
            func.coalesce(func.sum(AIAuditLog.prompt_tokens), 0),
            func.coalesce(func.sum(AIAuditLog.completion_tokens), 0),
            func.coalesce(func.sum(AIAuditLog.estimated_cost_usd), 0.0),
        ).where(AIAuditLog.school_id == school_id)

        if capability:
            count_stmt = count_stmt.where(AIAuditLog.capability == capability.upper())
        if status:
            count_stmt = count_stmt.where(AIAuditLog.status == status.upper())
        if provider_type:
            count_stmt = count_stmt.where(AIAuditLog.provider_type == provider_type.upper())

        count_res = db.execute(count_stmt).first()
        total_count = count_res[0] if count_res else 0
        total_prompt = int(count_res[1]) if count_res else 0
        total_comp = int(count_res[2]) if count_res else 0
        total_cost = float(count_res[3]) if count_res else 0.0

        # Execute paginated data query
        query = base_query.order_by(desc(AIAuditLog.created_at)).offset(offset).limit(limit)
        results = db.execute(query).all()

        items: list[AIAuditLogItemResponse] = []
        for log_entry, user_entry in results:
            items.append(
                AIAuditLogItemResponse(
                    id=log_entry.id,
                    school_id=log_entry.school_id,
                    user_id=log_entry.user_id,
                    user_full_name=f"{user_entry.first_name} {user_entry.last_name}".strip(),
                    capability=log_entry.capability,
                    provider_type=log_entry.provider_type,
                    model_name=log_entry.model_name,
                    prompt_tokens=log_entry.prompt_tokens,
                    completion_tokens=log_entry.completion_tokens,
                    total_tokens=log_entry.prompt_tokens + log_entry.completion_tokens,
                    estimated_cost_usd=float(log_entry.estimated_cost_usd),
                    latency_ms=log_entry.latency_ms,
                    status=log_entry.status,
                    error_message=log_entry.error_message,
                    created_at=log_entry.created_at,
                )
            )

        return AIAuditLogQueryResponse(
            total_count=total_count,
            total_prompt_tokens=total_prompt,
            total_completion_tokens=total_comp,
            total_cost_usd=round(total_cost, 6),
            items=items,
        )


ai_admin_service = AIAdminService()
