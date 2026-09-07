from __future__ import annotations

import time
from app.ai.providers.base_provider import BaseAIProvider, AIProviderException, AIProviderTimeoutException
from app.ai.schemas.provider import AIRequest, AIResponse, AIProviderType


class MockAIProvider(BaseAIProvider):
    """
    Deterministic, offline, zero-network Mock AI Provider for testing and default development.
    """

    def __init__(self, model_name: str = "mock-default-v1"):
        self._model_name = model_name

    @property
    def provider_type(self) -> str:
        return AIProviderType.MOCK.value

    @property
    def model_name(self) -> str:
        return self._model_name

    def execute(self, request: AIRequest) -> AIResponse:
        t0 = time.perf_counter()

        if request.simulate_timeout:
            raise AIProviderTimeoutException("Simulated AI Provider timeout")

        if request.simulate_failure:
            raise AIProviderException("Simulated AI Provider failure")

        prompt_lower = request.prompt.lower()
        tool_calls = None
        content = f"Mock response for prompt: '{request.prompt[:100]}'"

        # Deterministic tool resolution for tool registry testing
        if ("summary" in prompt_lower or "school" in prompt_lower) and request.tools:
            for tool in request.tools:
                if tool.get("name") == "get_school_summary":
                    tool_calls = [
                        {
                            "name": "get_school_summary",
                            "arguments": {},
                        }
                    ]
                    content = "Invoking tool 'get_school_summary' to fetch school details."
                    break

        prompt_tokens = max(1, len(request.prompt.split()))
        completion_tokens = max(1, len(content.split()))
        total_tokens = prompt_tokens + completion_tokens
        latency_ms = int((time.perf_counter() - t0) * 1000)

        return AIResponse(
            provider_type=self.provider_type,
            model_name=self.model_name,
            content=content,
            tool_calls=tool_calls,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=round(total_tokens * 0.000002, 6),
            latency_ms=max(1, latency_ms),
            raw_metadata={"mock_execution": True},
        )
