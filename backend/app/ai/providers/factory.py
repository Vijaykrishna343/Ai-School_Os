from __future__ import annotations

from app.ai.providers.base_provider import BaseAIProvider, AIProviderException
from app.ai.providers.mock_provider import MockAIProvider
from app.ai.schemas.provider import AIProviderType


class AIProviderFactory:
    """
    Factory for resolving active AIProvider instances based on configuration or tenant settings.
    """

    @staticmethod
    def get_provider(provider_type: str = "MOCK", model_name: str | None = None) -> BaseAIProvider:
        prov_type_upper = provider_type.upper()

        if prov_type_upper == AIProviderType.MOCK.value or not prov_type_upper:
            return MockAIProvider(model_name=model_name or "mock-default-v1")

        # In Phase 12.2, external AI APIs (OpenAI, Gemini, Anthropic) are not implemented.
        # Fallback cleanly to MockAIProvider or reject if external AI is requested.
        raise AIProviderException(
            f"External AI Provider '{provider_type}' is not configured or enabled in this phase. Fallback to MOCK provider."
        )
