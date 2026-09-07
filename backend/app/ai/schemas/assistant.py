from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class AssistantChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4096, description="User natural language prompt")
    context: dict[str, Any] | None = Field(default=None, description="Optional caller UI context")


class AssistantChatResponse(BaseModel):
    reply: str
    tool_invoked: str | None = None
    tool_args: dict[str, Any] | None = None
    tokens_used: int = 0
    latency_ms: int = 0
    redacted_fields: list[str] = Field(default_factory=list)
