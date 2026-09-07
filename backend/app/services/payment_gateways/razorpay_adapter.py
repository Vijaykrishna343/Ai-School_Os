from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.common.enums.payment import PaymentOrderStatus, PaymentProvider, PaymentTransactionStatus
from app.common.exceptions.payment import (
    PaymentAuthenticationError,
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


class RazorpayGatewayAdapter(BasePaymentGateway):
    """
    Razorpay Payment Gateway Adapter.
    Performs exact integer conversion for INR paise and timing-safe HMAC signature verification.
    """

    def __init__(
        self,
        key_id: str | None = None,
        key_secret: str | None = None,
        webhook_secret: str | None = None,
    ):
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = webhook_secret or settings.RAZORPAY_WEBHOOK_SECRET

    @property
    def provider(self) -> PaymentProvider:
        return PaymentProvider.RAZORPAY

    def _get_amount_in_subunits(self, amount: Decimal) -> int:
        """Converts Decimal amount to smallest currency unit (paise) without float rounding."""
        if amount <= 0:
            raise PaymentInvalidRequestError("Order amount must be greater than zero.", provider="RAZORPAY")
        subunits = (amount * Decimal("100")).quantize(Decimal("1"))
        return int(subunits)

    def _get_amount_from_subunits(self, amount_subunits: int | float | str | None) -> Decimal | None:
        """Converts smallest currency unit (paise) back to exact Decimal."""
        if amount_subunits is None:
            return None
        return Decimal(str(amount_subunits)) / Decimal("100")

    def create_order(self, request: GatewayOrderRequest) -> GatewayOrderResponse:
        if not self.key_id or not self.key_secret:
            raise PaymentConfigurationError("Razorpay credentials are not configured.", provider="RAZORPAY")

        amount_in_paise = self._get_amount_in_subunits(request.amount)

        # Build Razorpay order payload
        payload = {
            "amount": amount_in_paise,
            "currency": request.currency,
            "receipt": request.receipt,
            "notes": request.notes or {},
        }

        # Mock/Adapter response structure (reusable for Razorpay SDK / API integration)
        gateway_order_id = f"order_rzp_{hashlib.md5(f'{request.receipt}_{datetime.now(timezone.utc).timestamp()}'.encode()).hexdigest()[:14]}"
        
        raw_response = {
            "id": gateway_order_id,
            "entity": "order",
            "amount": amount_in_paise,
            "amount_paid": 0,
            "amount_due": amount_in_paise,
            "currency": request.currency,
            "receipt": request.receipt,
            "status": "created",
            "created_at": int(datetime.now(timezone.utc).timestamp()),
            "notes": request.notes or {},
        }

        return GatewayOrderResponse(
            provider=PaymentProvider.RAZORPAY,
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
        if not self.key_secret:
            raise PaymentConfigurationError("Razorpay key_secret is required for payment verification.", provider="RAZORPAY")

        message = f"{request.gateway_order_id}|{request.gateway_payment_id}"
        expected_signature = hmac.new(
            self.key_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        is_valid = hmac.compare_digest(expected_signature, request.gateway_signature)
        return GatewayPaymentVerificationResult(
            is_valid=is_valid,
            provider=PaymentProvider.RAZORPAY,
            gateway_order_id=request.gateway_order_id,
            gateway_payment_id=request.gateway_payment_id,
            message="Signature verification succeeded." if is_valid else "Signature mismatch.",
        )

    def verify_webhook_signature(
        self, payload: str | bytes, signature: str, secret: str | None = None
    ) -> bool:
        effective_secret = secret or self.webhook_secret
        if not effective_secret:
            raise PaymentConfigurationError("Razorpay webhook_secret is required for webhook verification.", provider="RAZORPAY")

        payload_bytes = payload if isinstance(payload, bytes) else payload.encode("utf-8")
        expected_signature = hmac.new(
            effective_secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    def parse_webhook_event(
        self, payload: str | bytes, signature: str | None = None, secret: str | None = None
    ) -> GatewayWebhookEvent:
        if signature:
            if not self.verify_webhook_signature(payload, signature, secret=secret):
                raise PaymentSignatureVerificationError("Invalid Razorpay webhook signature.", provider="RAZORPAY")

        payload_str = payload.decode("utf-8") if isinstance(payload, bytes) else payload
        try:
            data = json.loads(payload_str)
        except Exception as e:
            raise PaymentInvalidRequestError(f"Invalid JSON payload: {e}", provider="RAZORPAY") from e

        event_type = data.get("event", "unknown")
        event_id = data.get("event_id") or data.get("id") or f"evt_rzp_{hashlib.md5(payload_str.encode()).hexdigest()[:12]}"

        # Extract payment payload entity if present
        payload_data = data.get("payload", {})
        payment_entity = payload_data.get("payment", {}).get("entity", {})
        order_entity = payload_data.get("order", {}).get("entity", {})

        gateway_order_id = payment_entity.get("order_id") or order_entity.get("id")
        gateway_transaction_id = payment_entity.get("id")
        amount_subunits = payment_entity.get("amount") or order_entity.get("amount")
        amount = self._get_amount_from_subunits(amount_subunits)
        currency = payment_entity.get("currency") or order_entity.get("currency") or "INR"

        status_mapping = {
            "order.paid": PaymentTransactionStatus.SUCCESS,
            "payment.authorized": PaymentTransactionStatus.PENDING,
            "payment.captured": PaymentTransactionStatus.SUCCESS,
            "payment.failed": PaymentTransactionStatus.FAILED,
            "refund.processed": PaymentTransactionStatus.REFUNDED,
        }
        normalized_status = status_mapping.get(event_type, PaymentTransactionStatus.PENDING)

        return GatewayWebhookEvent(
            provider=PaymentProvider.RAZORPAY,
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
