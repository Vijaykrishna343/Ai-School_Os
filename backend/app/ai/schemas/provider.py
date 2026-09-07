from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class AICapability(str, Enum):
    ASSISTANT = "ASSISTANT"
    EMBEDDING = "EMBEDDING"
    OPTIMIZATION = "OPTIMIZATION"
    PREDICTION = "PREDICTION"
    COMMUNICATION = "COMMUNICATION"


class AIProviderType(str, Enum):
    MOCK = "MOCK"
    OPENAI = "OPENAI"
    GEMINI = "GEMINI"
    ANTHROPIC = "ANTHROPIC"
    LOCAL_ORTOOLS = "LOCAL_ORTOOLS"


class AIRequest(BaseModel):
    capability: AICapability
    prompt: str = Field(..., min_length=1, max_length=10000)
    system_prompt: str | None = None
    max_tokens: int = Field(default=1000, ge=1, le=8000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    tools: list[dict[str, Any]] | None = None
    context: dict[str, Any] | None = None
    simulate_failure: bool = False
    simulate_timeout: bool = False


class AIResponse(BaseModel):
    provider_type: str = "MOCK"
    model_name: str = "mock-default-v1"
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    latency_ms: int = 0
    raw_metadata: dict[str, Any] | None = None
