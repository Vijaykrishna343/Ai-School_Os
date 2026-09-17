from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, ConfigDict


class AIProviderConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID | None
    provider_type: str
    model_name: str | None
    is_enabled: bool
    allow_external_ai: bool
    api_key_configured: bool = False
    masked_api_key: str | None = None
    api_base_url: str | None = None
    notes: str | None
    updated_at: datetime


class AIProviderConfigUpdate(BaseModel):
    provider_type: str = Field(..., description="Provider type e.g. MOCK, GEMINI, OPENAI, ANTHROPIC, LOCAL_ORTOOLS")
    model_name: str | None = Field(None, description="Model identifier string")
    is_enabled: bool = Field(True, description="Enable or disable AI provider")
    allow_external_ai: bool = Field(False, description="Allow cloud LLM dispatches for this tenant")
    api_key: str | None = Field(None, description="Plaintext API key to securely encrypt and store at rest")
    api_base_url: str | None = Field(None, description="Optional custom base URL for provider")
    notes: str | None = Field(None, description="Administrative notes")


class AIUsageLimitUpdate(BaseModel):
    monthly_token_quota: int = Field(..., ge=0, description="Monthly token quota limit")
    is_enabled: bool = Field(True, description="Subsystem enabled toggle")


class AIAuditLogItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    user_id: uuid.UUID
    user_full_name: str
    capability: str
    provider_type: str
    model_name: str | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    latency_ms: int
    status: str
    error_message: str | None
    created_at: datetime


class AIAuditLogQueryResponse(BaseModel):
    total_count: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost_usd: float
    items: list[AIAuditLogItemResponse]
