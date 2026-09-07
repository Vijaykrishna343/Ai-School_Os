from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.identity.models.user import IdentityUser
from app.identity.security.current_user import get_current_user
from app.schemas.payment import (
    CreatePaymentOrderRequest,
    PaymentOrderResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
    WebhookResponse,
)
from app.services.payment_order_service import payment_order_service
from app.services.payment_verification_service import payment_verification_service

router = APIRouter()


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
    "/webhook/{provider}",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Handle Gateway Webhook",
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

