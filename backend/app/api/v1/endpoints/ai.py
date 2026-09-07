from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.identity.models.user import IdentityUser
from app.identity.security.current_user import get_current_user
from app.identity.dependencies.require_permission import require_permission
from app.ai.schemas.assistant import AssistantChatRequest, AssistantChatResponse
from app.ai.services.ai_assistant_service import ai_assistant_service
from app.ai.services.ai_usage_service import ai_usage_service

router = APIRouter(prefix="/ai", tags=["AI Subsystem"])


@router.post(
    "/assistant/chat",
    response_model=AssistantChatResponse,
    summary="Natural Language AI Assistant Chat",
)
def chat_with_assistant(
    request_data: AssistantChatRequest,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("ai.assistant")),
) -> AssistantChatResponse:
    """
    Process a natural language assistant chat prompt using MockAIProvider.
    Enforces RBAC ('ai.assistant'), tenant boundary, token quota limits, PII minimization, and audit logging.
    """
    return ai_assistant_service.process_chat(
        db=db,
        current_user=current_user,
        request_data=request_data,
    )


@router.get(
    "/assistant/tools",
    summary="Get Available Assistant Domain Tools",
)
def list_assistant_tools(
    current_user: IdentityUser = Depends(require_permission("ai.assistant")),
) -> list[dict[str, Any]]:
    """
    Retrieve registered domain tools available to the authenticated user based on their permissions.
    """
    return ai_assistant_service.list_available_tools(current_user)


@router.get(
    "/usage/stats",
    summary="Get AI Usage & Quota Stats",
)
def get_ai_usage_stats(
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Retrieve monthly token quota usage statistics for the current school.
    """
    usage = ai_usage_service.get_or_create_usage_limit(db, current_user.school_id)
    return {
        "school_id": str(usage.school_id),
        "monthly_token_quota": usage.monthly_token_quota,
        "used_tokens_current_month": usage.used_tokens_current_month,
        "quota_remaining": max(0, usage.monthly_token_quota - usage.used_tokens_current_month),
        "quota_reset_date": str(usage.quota_reset_date),
        "is_enabled": usage.is_enabled,
    }


# ============================================================================
# PHASE 12.8 — AI SUBSYSTEM ADMINISTRATION ENDPOINTS
# ============================================================================

from app.ai.schemas.admin import (
    AIProviderConfigResponse,
    AIProviderConfigUpdate,
    AIUsageLimitUpdate,
    AIAuditLogQueryResponse,
)
from app.ai.services.ai_admin_service import ai_admin_service


@router.get(
    "/admin/provider-config",
    response_model=AIProviderConfigResponse,
    summary="Get AI Provider Configuration",
)
def get_provider_config(
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("system.settings")),
) -> AIProviderConfigResponse:
    """
    Retrieve tenant AI provider configuration.
    Requires 'system.settings' permission.
    """
    return ai_admin_service.get_provider_config(db, current_user.school_id)


@router.put(
    "/admin/provider-config",
    response_model=AIProviderConfigResponse,
    summary="Update AI Provider Configuration",
)
def update_provider_config(
    data: AIProviderConfigUpdate,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("system.settings")),
) -> AIProviderConfigResponse:
    """
    Update tenant AI provider configuration parameters.
    Requires 'system.settings' permission.
    """
    return ai_admin_service.update_provider_config(db, current_user.school_id, data)


@router.put(
    "/admin/usage-limit",
    summary="Update AI Monthly Token Quota & Subsystem Status",
)
def update_usage_limit(
    data: AIUsageLimitUpdate,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("system.settings")),
) -> dict[str, Any]:
    """
    Update tenant monthly AI token quota and enable/disable AI subsystem.
    Requires 'system.settings' permission.
    """
    return ai_admin_service.update_usage_limit(db, current_user.school_id, data)


@router.get(
    "/admin/audit-logs",
    response_model=AIAuditLogQueryResponse,
    summary="Query System AI Audit Logs",
)
def query_audit_logs(
    capability: str | None = None,
    status: str | None = None,
    provider_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("system.settings")),
) -> AIAuditLogQueryResponse:
    """
    Query system-wide AI audit logs with filtering and token/cost aggregations.
    Requires 'system.settings' permission.
    """
    return ai_admin_service.query_audit_logs(
        db=db,
        school_id=current_user.school_id,
        capability=capability,
        status=status,
        provider_type=provider_type,
        limit=limit,
        offset=offset,
    )

