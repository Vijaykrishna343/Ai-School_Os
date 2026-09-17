"""AI Provider Factory.

Factory for resolving active AIProvider instances based on tenant configuration,
secure encrypted credentials, and isolation policies.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.providers.base_provider import BaseAIProvider, AIProviderException
from app.ai.providers.mock_provider import MockAIProvider
from app.ai.providers.gemini_provider import GeminiAIProvider
from app.ai.providers.openai_provider import OpenAIAIProvider
from app.ai.schemas.provider import AIProviderType
from app.common.security.encryption import decrypt_credential

if TYPE_CHECKING:
    from app.models.ai.ai_provider_config import AIProviderConfig


class AIProviderFactory:
    """
    Factory for resolving active AIProvider instances based on configuration or tenant settings.
    """

    @staticmethod
    def get_provider(
        provider_type: str = "MOCK",
        model_name: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> BaseAIProvider:
        """
        Directly instantiates a provider by type with supplied parameters.
        """
        prov_type_upper = (provider_type or "MOCK").upper()

        if prov_type_upper == AIProviderType.MOCK.value or prov_type_upper == "MOCK":
            return MockAIProvider(model_name=model_name or "mock-default-v1")

        if prov_type_upper == AIProviderType.GEMINI.value or prov_type_upper == "GEMINI":
            if not api_key:
                raise AIProviderException("Gemini live provider requires an API key.")
            return GeminiAIProvider(
                api_key=api_key,
                model_name=model_name,
                base_url=base_url,
            )

        if prov_type_upper == AIProviderType.OPENAI.value or prov_type_upper == "OPENAI":
            if not api_key:
                raise AIProviderException("OpenAI live provider requires an API key.")
            return OpenAIAIProvider(
                api_key=api_key,
                model_name=model_name,
                base_url=base_url,
            )

        raise AIProviderException(
            f"External AI Provider '{provider_type}' is not supported or recognized."
        )

    @staticmethod
    def resolve_for_school(db: Session, school_id: uuid.UUID) -> BaseAIProvider:
        """
        Resolves the configured AI provider for a specific school tenant.
        Decrypts credentials and enforces tenant isolation.
        """
        from app.models.ai.ai_provider_config import AIProviderConfig

        config = db.scalar(
            select(AIProviderConfig).where(AIProviderConfig.school_id == school_id)
        )

        if not config:
            from app.core.config import settings
            if settings.ENVIRONMENT.lower() in ("production", "prod"):
                raise AIProviderException(
                    "No AI provider is configured for this school. Production environment requires explicit provider configuration."
                )
            return MockAIProvider(model_name="mock-default-v1")

        if not config.is_enabled:
            raise AIProviderException("AI subsystem is disabled for this school.")

        prov_type = (config.provider_type or "MOCK").upper()

        if prov_type == "MOCK":
            return MockAIProvider(model_name=config.model_name or "mock-default-v1")

        if not config.allow_external_ai:
            raise AIProviderException(
                f"External AI provider '{prov_type}' is configured, but 'allow_external_ai' is not enabled for this school."
            )

        decrypted_key = decrypt_credential(config.encrypted_api_key)
        if not decrypted_key:
            raise AIProviderException(
                f"Live AI provider '{prov_type}' is enabled, but no valid API key is configured. Fail-closed."
            )

        return AIProviderFactory.get_provider(
            provider_type=prov_type,
            model_name=config.model_name,
            api_key=decrypted_key,
            base_url=config.api_base_url,
        )
