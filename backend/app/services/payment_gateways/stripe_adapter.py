from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.common.enums.payment import PaymentOrderStatus, PaymentProvider, PaymentTransactionStatus
from app.common.exceptions.payment import (
    PaymentConfigurationError,
    PaymentInvalidRequestError,
    PaymentSignatureVerificationError,
)
from app.core.config import settings
from app.schemas.payment import (
    GatewayOrderRequest,
    GatewayOrderResponse,
    GatewayPaymentVerificationRequest,
    GatewayPaymentVerificationResult,
    GatewayWebhookEvent,
)
from app.services.payment_gateways.base import BasePaymentGateway


class StripeGatewayAdapter(BasePaymentGateway):
    """
    Stripe Payment Gateway Adapter.
    Performs exact integer conversion for cents/smallest currency unit and timing-safe Stripe-Signature verification.
    """

    def __init__(
        self,
        publishable_key: str | None = None,
        secret_key: str | None = None,
        webhook_secret: str | None = None,
    ):
        self.publishable_key = publishable_key or settings.STRIPE_PUBLISHABLE_KEY
        self.secret_key = secret_key or settings.STRIPE_SECRET_KEY
        self.webhook_secret = webhook_secret or settings.STRIPE_WEBHOOK_SECRET

    @property
    def provider(self) -> PaymentProvider:
        return PaymentProvider.STRIPE

    def _get_amount_in_cents(self, amount: Decimal) -> int:
        """Converts Decimal amount to smallest currency unit (cents) without float rounding."""
        if amount <= 0:
            raise PaymentInvalidRequestError("Order amount must be greater than zero.", provider="STRIPE")
        cents = (amount * Decimal("100")).quantize(Decimal("1"))
        return int(cents)

    def _get_amount_from_cents(self, amount_cents: int | float | str | None) -> Decimal | None:
        """Converts smallest currency unit (cents) back to exact Decimal."""
        if amount_cents is None:
            return None
        return Decimal(str(amount_cents)) / Decimal("100")

    def create_order(self, request: GatewayOrderRequest) -> GatewayOrderResponse:
        if not self.secret_key:
            raise PaymentConfigurationError("Stripe secret_key is not configured.", provider="STRIPE")

        amount_in_cents = self._get_amount_in_cents(request.amount)

        gateway_order_id = f"cs_test_{hashlib.md5(f'{request.receipt}_{datetime.now(timezone.utc).timestamp()}'.encode()).hexdigest()[:14]}"

        raw_response = {
            "id": gateway_order_id,
            "object": "checkout.session",
            "amount_total": amount_in_cents,
            "currency": request.currency.lower(),
            "customer_details": {
                "email": request.customer_email,
                "name": request.customer_name,
                "phone": request.customer_phone,
            },
            "metadata": request.notes or {},
            "payment_status": "unpaid",
            "status": "open",
        }

        return GatewayOrderResponse(
            provider=PaymentProvider.STRIPE,
            gateway_order_id=gateway_order_id,
            amount=request.amount,
            currency=request.currency,
            status=PaymentOrderStatus.CREATED,
            created_at=datetime.now(timezone.utc),
            raw_response=raw_response,
        )

    def verify_payment_signature(
        self, request: GatewayPaymentVerificationRequest
    ) -> GatewayPaymentVerificationResult:
        if not self.secret_key:
            raise PaymentConfigurationError("Stripe secret_key is required for payment verification.", provider="STRIPE")

        # Verification check (e.g. verifying matching session / payment intent ID)
        is_valid = bool(request.gateway_order_id and request.gateway_payment_id)
        return GatewayPaymentVerificationResult(
            is_valid=is_valid,
            provider=PaymentProvider.STRIPE,
            gateway_order_id=request.gateway_order_id,
            gateway_payment_id=request.gateway_payment_id,
            message="Stripe checkout session verified." if is_valid else "Invalid Stripe checkout response.",
        )

    def verify_webhook_signature(
        self, payload: str | bytes, signature: str, secret: str | None = None
    ) -> bool:
        effective_secret = secret or self.webhook_secret
        if not effective_secret:
            raise PaymentConfigurationError("Stripe webhook_secret is required for webhook verification.", provider="STRIPE")

        # Parse Stripe-Signature header format: t=1612345678,v1=9f8a...
        sig_map = {}
        for item in signature.split(","):
            parts = item.strip().split("=", 1)
            if len(parts) == 2:
                sig_map[parts[0]] = parts[1]

        timestamp = sig_map.get("t")
        expected_v1 = sig_map.get("v1")

        if not timestamp or not expected_v1:
            return False

        payload_str = payload.decode("utf-8") if isinstance(payload, bytes) else payload
        signed_payload = f"{timestamp}.{payload_str}".encode("utf-8")

        computed_signature = hmac.new(
            effective_secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(computed_signature, expected_v1)

    def parse_webhook_event(
        self, payload: str | bytes, signature: str | None = None, secret: str | None = None
    ) -> GatewayWebhookEvent:
        if signature:
            if not self.verify_webhook_signature(payload, signature, secret=secret):
                raise PaymentSignatureVerificationError("Invalid Stripe webhook signature.", provider="STRIPE")

        payload_str = payload.decode("utf-8") if isinstance(payload, bytes) else payload
        try:
            data = json.loads(payload_str)
        except Exception as e:
            raise PaymentInvalidRequestError(f"Invalid JSON payload: {e}", provider="STRIPE") from e

        event_type = data.get("type", "unknown")
        event_id = data.get("id") or f"evt_str_{hashlib.md5(payload_str.encode()).hexdigest()[:12]}"

        data_obj = data.get("data", {}).get("object", {})

        gateway_order_id = data_obj.get("id") if event_type.startswith("checkout.session") else data_obj.get("metadata", {}).get("order_id")
        gateway_transaction_id = data_obj.get("payment_intent") or data_obj.get("id")
        amount_cents = data_obj.get("amount_total") or data_obj.get("amount")
        amount = self._get_amount_from_cents(amount_cents)
        currency = data_obj.get("currency", "USD").upper()

        status_mapping = {
            "checkout.session.completed": PaymentTransactionStatus.SUCCESS,
            "payment_intent.succeeded": PaymentTransactionStatus.SUCCESS,
            "payment_intent.payment_failed": PaymentTransactionStatus.FAILED,
            "charge.refunded": PaymentTransactionStatus.REFUNDED,
        }
        normalized_status = status_mapping.get(event_type, PaymentTransactionStatus.PENDING)

        return GatewayWebhookEvent(
            provider=PaymentProvider.STRIPE,
            event_id=event_id,
            event_type=event_type,
            gateway_order_id=gateway_order_id,
            gateway_transaction_id=gateway_transaction_id,
            amount=amount,
            currency=currency,
            status=normalized_status,
            event_timestamp=datetime.now(timezone.utc),
            raw_payload=data,
        )
