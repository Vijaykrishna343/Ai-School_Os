from __future__ import annotations

from typing import Any

from app.common.enums.payment import PaymentProvider
from app.common.exceptions.payment import PaymentUnsupportedProviderError
from app.services.payment_gateways.base import BasePaymentGateway
from app.services.payment_gateways.razorpay_adapter import RazorpayGatewayAdapter
from app.services.payment_gateways.stripe_adapter import StripeGatewayAdapter


class PaymentGatewayFactory:
    """
    Factory for resolving and instantiating payment gateway adapters.
    Supports tenant-isolated credentials without global mutable state leakage.
    """

    @staticmethod
    def get_gateway(
        provider: PaymentProvider | str,
        key_id: str | None = None,
        key_secret: str | None = None,
        webhook_secret: str | None = None,
        extra_config: dict[str, Any] | None = None,
    ) -> BasePaymentGateway:
        """
        Resolves a provider-specific gateway adapter instance.

        Args:
            provider: PaymentProvider enum or string identifier (RAZORPAY, STRIPE).
            key_id: Optional tenant-specific API key ID / publishable key.
            key_secret: Optional tenant-specific secret key.
            webhook_secret: Optional tenant-specific webhook secret.
            extra_config: Additional provider configurations.

        Returns:
            Configured instance of BasePaymentGateway.

        Raises:
            PaymentUnsupportedProviderError: If the provider is unsupported or invalid.
        """
        if isinstance(provider, str):
            try:
                provider = PaymentProvider(provider.upper())
            except ValueError:
                raise PaymentUnsupportedProviderError(
                    f"Unsupported payment provider: '{provider}'", provider=str(provider)
                )

        if provider == PaymentProvider.RAZORPAY:
            return RazorpayGatewayAdapter(
                key_id=key_id,
                key_secret=key_secret,
                webhook_secret=webhook_secret,
            )

        if provider == PaymentProvider.STRIPE:
            return StripeGatewayAdapter(
                publishable_key=key_id,
                secret_key=key_secret,
                webhook_secret=webhook_secret,
            )

        raise PaymentUnsupportedProviderError(
            f"No gateway adapter available for provider '{provider}'", provider=str(provider)
        )


class PaymentGatewayService:
    """
    Service wrapper delegating operations to resolved gateway adapters.
    """

    def __init__(self, factory: type[PaymentGatewayFactory] = PaymentGatewayFactory):
        self.factory = factory

    def get_gateway(
        self,
        provider: PaymentProvider | str,
        key_id: str | None = None,
        key_secret: str | None = None,
        webhook_secret: str | None = None,
    ) -> BasePaymentGateway:
        return self.factory.get_gateway(
            provider=provider,
            key_id=key_id,
            key_secret=key_secret,
            webhook_secret=webhook_secret,
        )


payment_gateway_service = PaymentGatewayService()
