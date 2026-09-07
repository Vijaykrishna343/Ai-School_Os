from __future__ import annotations

from abc import ABC, abstractmethod
from app.ai.schemas.provider import AIRequest, AIResponse
from app.common.exceptions import InternalServerException, BadRequestException


class AIProviderException(InternalServerException):
    """Controlled exception for AI Provider errors."""

    def __init__(self, message: str = "AI Provider error occurred"):
        super().__init__(message=message)


class AIProviderTimeoutException(BadRequestException):
    """Controlled exception for AI Provider timeouts."""

    def __init__(self, message: str = "AI Provider request timed out"):
        super().__init__(message=message)


class BaseAIProvider(ABC):
    """
    Abstract Base Class for all AI capabilities and vendor integrations.
    """

    @property
    @abstractmethod
    def provider_type(self) -> str:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @abstractmethod
    def execute(self, request: AIRequest) -> AIResponse:
        """
        Execute an AI request and return a structured AIResponse.
        Must raise controlled AIProviderException / AIProviderTimeoutException on failure.
        """
        pass
