from __future__ import annotations

import time
import json
from typing import Any
from sqlalchemy.orm import Session

from app.identity.models.user import IdentityUser
from app.ai.schemas.assistant import AssistantChatRequest, AssistantChatResponse
from app.ai.schemas.provider import AIRequest, AICapability
from app.ai.providers import AIProviderFactory, BaseAIProvider, AIProviderException, AIProviderTimeoutException
from app.ai.security import AITenantBoundaryService, AIDataMinimizer
from app.ai.services.ai_usage_service import ai_usage_service
from app.ai.services.ai_audit_service import ai_audit_service
from app.ai.tools.registry import ai_tool_registry
from app.common.exceptions import BadRequestException


class AIAssistantService:
    """
    Orchestration service for the Natural Language AI Assistant.
    Enforces auth, tenant boundary, usage quota, PII sanitization, tool execution, and audit logging.
    """

    def process_chat(
        self,
        db: Session,
        current_user: IdentityUser,
        request_data: AssistantChatRequest,
        provider_override: BaseAIProvider | None = None,
    ) -> AssistantChatResponse:
        t0 = time.perf_counter()

        # 1. Tenant boundary validation
        school_id = AITenantBoundaryService.validate_and_get_school_id(current_user)

        # 2. Check and reserve monthly quota
        ai_usage_service.check_and_reserve_quota(db, school_id, estimated_tokens=150)

        # 3. Data minimization & PII scrubbing
        sanitized_message, message_redactions = AIDataMinimizer.sanitize_text(request_data.message)
        sanitized_context, context_redactions = ({}, [])
        if request_data.context:
            sanitized_context, context_redactions = AIDataMinimizer.sanitize_dict(request_data.context)

        all_redactions = sorted(set(message_redactions + context_redactions))

        # 4. Resolve AI Provider
        provider = provider_override or AIProviderFactory.get_provider("MOCK")

        # 5. Build AI Request with permission-filtered whitelisted tools
        permitted_tools = ai_tool_registry.list_tools_for_user(current_user)
        ai_request = AIRequest(
            capability=AICapability.ASSISTANT,
            prompt=sanitized_message,
            tools=permitted_tools,
            context=sanitized_context,
        )

        tool_invoked = None
        tool_args = None
        status = "SUCCESS"
        error_msg = None

        try:
            # 6. Execute Provider Request
            ai_response = provider.execute(ai_request)
            final_reply = ai_response.content

            # 7. Check for tool calls returned by AI model
            if ai_response.tool_calls:
                first_call = ai_response.tool_calls[0]
                tool_name = first_call.get("name")
                raw_args = first_call.get("arguments", {})

                tool_invoked = tool_name
                tool_args = raw_args

                # Execute authorized tool through registry
                tool_result = ai_tool_registry.execute_tool(
                    tool_name=tool_name,
                    db=db,
                    current_user=current_user,
                    tool_args=raw_args,
                )

                final_reply = f"{ai_response.content}\n\n[Tool Data Result]: {json.dumps(tool_result)}"

        except (AIProviderException, AIProviderTimeoutException, BadRequestException) as err:
            status = "ERROR"
            error_msg = str(err)
            raise
        except Exception as err:
            status = "ERROR"
            error_msg = str(err)
            raise BadRequestException(f"AI Assistant execution failed: {str(err)}") from err
        finally:
            latency_ms = int((time.perf_counter() - t0) * 1000)
            tokens_used = ai_response.total_tokens if "ai_response" in locals() else 0

            # 8. Record audit log
            ai_audit_service.log_ai_event(
                db=db,
                school_id=school_id,
                user_id=current_user.id,
                capability="ASSISTANT",
                provider_type=provider.provider_type,
                model_name=provider.model_name,
                prompt_tokens=ai_response.prompt_tokens if "ai_response" in locals() else 0,
                completion_tokens=ai_response.completion_tokens if "ai_response" in locals() else 0,
                estimated_cost_usd=ai_response.estimated_cost_usd if "ai_response" in locals() else 0.0,
                latency_ms=latency_ms,
                status=status,
                error_message=error_msg,
            )

            # 9. Record actual usage
            if tokens_used > 0:
                ai_usage_service.record_usage(db, school_id, tokens_used)

        return AssistantChatResponse(
            reply=final_reply,
            tool_invoked=tool_invoked,
            tool_args=tool_args,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            redacted_fields=all_redactions,
        )

    def list_available_tools(self, current_user: IdentityUser) -> list[dict[str, Any]]:
        """
        List all registered tools available to the specified user based on their permissions.
        """
        return ai_tool_registry.list_tools_for_user(current_user)


ai_assistant_service = AIAssistantService()
