from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.common.enums.payment import PaymentOrderStatus, PaymentProvider, PaymentTransactionStatus


class GatewayOrderRequest(BaseModel):
    """
    Provider-neutral DTO for requesting checkout order creation from a payment gateway.
    """
    amount: Decimal = Field(..., gt=0, description="Order amount in major currency units (e.g. 100.50)")
    currency: str = Field("INR", max_length=10, description="Currency code (e.g. INR, USD)")
    receipt: str = Field(..., max_length=100, description="Internal receipt or assignment identifier")
    customer_name: str | None = Field(None, max_length=150)
    customer_email: str | None = Field(None, max_length=255)
    customer_phone: str | None = Field(None, max_length=20)
    notes: dict[str, Any] | None = Field(None, description="Metadata or key-value notes")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        clean = v.strip().upper()
        if not clean:
            raise ValueError("Currency cannot be empty.")
        return clean


class GatewayOrderResponse(BaseModel):
    """
    Provider-neutral DTO returned after successful order creation.
    """
    provider: PaymentProvider
    gateway_order_id: str = Field(..., description="Provider-issued order reference")
    amount: Decimal = Field(..., gt=0)
    currency: str = Field("INR")
    status: PaymentOrderStatus = Field(default=PaymentOrderStatus.CREATED)
    created_at: datetime | None = None
    raw_response: dict[str, Any] | None = None


class GatewayPaymentVerificationRequest(BaseModel):
    """
    Provider-neutral DTO for client callback payment verification.
    """
    provider: PaymentProvider
    gateway_order_id: str
    gateway_payment_id: str
    gateway_signature: str


class GatewayPaymentVerificationResult(BaseModel):
    """
    Provider-neutral DTO representing payment signature verification result.
    """
    is_valid: bool
    provider: PaymentProvider
    gateway_order_id: str
    gateway_payment_id: str
    message: str | None = None


class GatewayWebhookEvent(BaseModel):
    """
    Provider-neutral DTO for normalized gateway webhook events.
    """
    provider: PaymentProvider
    event_id: str = Field(..., description="Unique event ID issued by provider")
    event_type: str = Field(..., description="Normalized or raw event type name")
    gateway_order_id: str | None = None
    gateway_transaction_id: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    status: PaymentTransactionStatus | None = None
    event_timestamp: datetime | None = None
    raw_payload: dict[str, Any] | None = None


class CreatePaymentOrderRequest(BaseModel):
    """
    Request DTO for creating a payment checkout order.
    The client does NOT supply the payable amount — it is strictly calculated server-side.
    """
    student_fee_assignment_id: UUID = Field(..., description="Target student fee assignment ID")
    provider: PaymentProvider | None = Field(
        None, description="Optional target payment gateway provider (e.g. RAZORPAY, STRIPE)"
    )


class PaymentOrderResponse(BaseModel):
    """
    Sanitized provider-neutral response DTO for payment orders.
    Contains no secrets, API tokens, or raw gateway credentials.
    """
    id: UUID
    school_id: UUID
    student_fee_assignment_id: UUID
    provider: PaymentProvider
    gateway_order_id: str
    amount: Decimal
    currency: str = "INR"
    status: PaymentOrderStatus
    expires_at: datetime | None = None
    extra_metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VerifyPaymentRequest(BaseModel):
    """
    Client request DTO for verifying payment.
    Contains local payment order identifier and gateway verification parameters.
    Client-supplied amount/currency are strictly validated or ignored in favor of server state.
    """
    provider: PaymentProvider
    payment_order_id: UUID = Field(..., description="Local PaymentOrder ID")
    gateway_order_id: str = Field(..., description="Provider-issued order ID (e.g. order_xxx or cs_xxx)")
    gateway_payment_id: str = Field(..., description="Provider-issued payment/transaction ID (e.g. pay_xxx or pi_xxx)")
    gateway_signature: str = Field(..., description="Provider cryptographic signature (e.g. Razorpay HMAC signature)")
    amount: Decimal | None = Field(None, description="Optional client-submitted amount (validated against local order)")
    currency: str | None = Field(None, description="Optional client-submitted currency (validated against local order)")


class VerifyPaymentResponse(BaseModel):
    """
    Response DTO after client payment verification.
    """
    success: bool
    message: str
    order_id: UUID
    status: PaymentOrderStatus
    gateway_transaction_id: str | None = None
    amount: Decimal
    currency: str


class WebhookResponse(BaseModel):
    """
    Response DTO acknowledged to payment gateway webhook calls.
    """
    success: bool
    message: str
    event_id: str | None = None
    processed: bool = True


