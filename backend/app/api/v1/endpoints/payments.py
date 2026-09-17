from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.identity.security.current_user import get_current_user
from app.schemas.payment import (
    CreatePaymentOrderRequest,
    PaymentConfigResponse,
    PaymentConfigUpdate,
    PaymentOrderResponse,
    PaymentOrderStatusResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
    WebhookResponse,
)
from app.services.payment_config_service import payment_config_service
from app.services.payment_order_service import payment_order_service
from app.services.payment_verification_service import payment_verification_service

router = APIRouter()


@router.get(
    "/config",
    response_model=PaymentConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Payment Gateway Provider Configuration",
    description="Retrieves active payment provider configurations with all sensitive secrets masked.",
)
def get_payment_config(
    current_user: IdentityUser = Depends(require_permission("fees.view")),
) -> PaymentConfigResponse:
    """
    Returns payment provider configuration. Secrets are strictly masked and absent from responses.
    """
    school_id = getattr(current_user, "school_id", None)
    return payment_config_service.get_config(school_id=school_id)


@router.put(
    "/config",
    response_model=PaymentConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Payment Gateway Provider Configuration",
    description="Updates provider credentials securely. New secrets are encrypted at rest with write-only protection.",
)
def update_payment_config(
    data: PaymentConfigUpdate,
    current_user: IdentityUser = Depends(require_permission("fees.update")),
) -> PaymentConfigResponse:
    """
    Updates payment provider credentials. Enforces encryption at rest and role-based authorization.
    """
    school_id = getattr(current_user, "school_id", None)
    return payment_config_service.update_config(updates=data, school_id=school_id)


@router.post(
    "/orders",
    response_model=PaymentOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Payment Order",
    description="Creates a provider-neutral payment checkout order for a StudentFeeAssignment. The payable amount is strictly calculated on the server side.",
)
def create_payment_order(
    data: CreatePaymentOrderRequest,
    current_user: IdentityUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentOrderResponse:
    """
    Creates a payment order for an eligible student fee assignment.
    Enforces tenant isolation, relationship authorization, and server-side amount calculation.
    """
    return payment_order_service.create_payment_order(
        db=db,
        current_user=current_user,
        data=data,
    )


@router.get(
    "/orders/{order_id}",
    response_model=PaymentOrderStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Authoritative Payment Order Status",
    description="Retrieves the authoritative server status of a PaymentOrder for UI polling.",
)
def get_payment_order_status(
    order_id: UUID,
    current_user: IdentityUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentOrderStatusResponse:
    """
    Returns authoritative payment order state, amount, currency, and settled receipt info.
    """
    return payment_order_service.get_order_status(
        db=db,
        current_user=current_user,
        order_id=order_id,
    )


@router.post(
    "/verify",
    response_model=VerifyPaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Payment",
    description="Verifies payment completion via client callback parameters and gateway cryptographic signature.",
)
def verify_payment(
    data: VerifyPaymentRequest,
    current_user: IdentityUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VerifyPaymentResponse:
    """
    Verifies payment completion for an authenticated user.
    Enforces relationship authorization, provider consistency, and exact amount/currency validation.
    """
    return payment_verification_service.verify_payment(
        db=db,
        current_user=current_user,
        data=data,
    )


@router.post(
    "/webhooks/razorpay",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Handle Razorpay Gateway Webhook",
    description="Unauthenticated endpoint receiving raw webhook events from Razorpay. Cryptographically verified against X-Razorpay-Signature.",
)
async def handle_razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> WebhookResponse:
    """
    Handles Razorpay webhook event notifications.
    Validates HMAC-SHA256 signatures directly on raw HTTP request body bytes.
    Resolves tenant context server-side from stored PaymentOrder records.
    """
    raw_body = await request.body()
    sig_header = request.headers.get("x-razorpay-signature") or request.headers.get("x-signature")
    return payment_verification_service.process_webhook(
        db=db,
        provider_str="RAZORPAY",
        raw_body=raw_body,
        signature_header=sig_header,
    )


@router.post(
    "/webhooks/stripe",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Handle Stripe Gateway Webhook",
    description="Unauthenticated endpoint receiving raw webhook events from Stripe. Cryptographically verified against Stripe-Signature header.",
)
async def handle_stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> WebhookResponse:
    """
    Handles Stripe webhook event notifications.
    Validates timestamped HMAC-SHA256 signatures directly on raw HTTP request body bytes.
    Resolves tenant context server-side from stored PaymentOrder records.
    """
    raw_body = await request.body()
    sig_header = request.headers.get("stripe-signature") or request.headers.get("x-signature")
    return payment_verification_service.process_webhook(
        db=db,
        provider_str="STRIPE",
        raw_body=raw_body,
        signature_header=sig_header,
    )


@router.post(
    "/webhooks/{provider}",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Handle Provider Gateway Webhook (Plural path)",
    description="Unauthenticated endpoint receiving raw webhook events from payment gateway providers.",
)
@router.post(
    "/webhook/{provider}",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Handle Provider Gateway Webhook (Singular path)",
    description="Unauthenticated endpoint receiving raw webhook events from payment gateway providers (Razorpay, Stripe).",
)
async def handle_payment_webhook(
    provider: str,
    request: Request,
    db: Session = Depends(get_db),
) -> WebhookResponse:
    """
    Handles payment webhook event notifications.
    Validates cryptographic signatures directly on raw HTTP request body bytes.
    Resolves tenant context server-side from stored PaymentOrder records.
    """
    raw_body = await request.body()
    sig_header = (
        request.headers.get("x-razorpay-signature")
        or request.headers.get("stripe-signature")
        or request.headers.get("x-signature")
    )
    return payment_verification_service.process_webhook(
        db=db,
        provider_str=provider,
        raw_body=raw_body,
        signature_header=sig_header,
    )
