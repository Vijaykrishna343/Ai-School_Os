from __future__ import annotations

import abc

from app.common.enums.payment import PaymentProvider
from app.schemas.payment import (
    GatewayOrderRequest,
    GatewayOrderResponse,
    GatewayPaymentVerificationRequest,
    GatewayPaymentVerificationResult,
    GatewayWebhookEvent,
)


class BasePaymentGateway(abc.ABC):
    """
    Abstract interface for payment gateway provider adapters.
    """

    @property
    @abc.abstractmethod
    def provider(self) -> PaymentProvider:
        """Returns the PaymentProvider enum handled by this gateway adapter."""
        ...

    @abc.abstractmethod
    def create_order(self, request: GatewayOrderRequest) -> GatewayOrderResponse:
        """
        Creates an online checkout order with the external payment gateway.
        """
        ...

    @abc.abstractmethod
    def verify_payment_signature(
        self, request: GatewayPaymentVerificationRequest
    ) -> GatewayPaymentVerificationResult:
        """
        Cryptographically verifies frontend client callback signature.
        """
        ...

    @abc.abstractmethod
    def verify_webhook_signature(
        self, payload: str | bytes, signature: str, secret: str | None = None
    ) -> bool:
        """
        Cryptographically verifies an incoming webhook payload signature.
        """
        ...

    @abc.abstractmethod
    def parse_webhook_event(
        self, payload: str | bytes, signature: str | None = None, secret: str | None = None
    ) -> GatewayWebhookEvent:
        """
        Normalizes a raw provider webhook payload into a GatewayWebhookEvent DTO.
        """
        ...
