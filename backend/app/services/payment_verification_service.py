from __future__ import annotations

import json
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.authorization import enforce_relationship_access
from app.common.enums.payment import PaymentOrderStatus, PaymentProvider, PaymentTransactionStatus
from app.common.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.common.exceptions.payment import PaymentSignatureVerificationError
from app.common.logger.logger import get_logger
from app.identity.models.user import IdentityUser
from app.models.fees.student_fee_assignment import StudentFeeAssignment
from app.models.payment.payment_order import PaymentOrder
from app.models.payment.payment_transaction import PaymentTransaction
from app.schemas.payment import (
    GatewayPaymentVerificationRequest,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
    WebhookResponse,
)
from app.services.payment_gateway_service import PaymentGatewayFactory
from app.services.payment_order_service import PaymentOrderService
from app.services.payment_settlement_service import payment_settlement_service

logger = get_logger(__name__)

SENSITIVE_KEYS = {
    "key_secret",
    "secret",
    "webhook_secret",
    "access_token",
    "authorization",
    "card_number",
    "cvv",
    "cvc",
    "pin",
    "password",
    "secret_key",
    "api_key",
    "private_key",
}


def sanitize_raw_payload(payload: Any) -> Any:
    """
    Sanitizes raw response/event payload to strip API secrets, keys, credentials, and sensitive card data.
    """
    if isinstance(payload, dict):
        sanitized = {}
        for k, v in payload.items():
            k_str = str(k).lower()
            if k_str in SENSITIVE_KEYS or any(s in k_str for s in ("secret", "token", "password", "private_key")):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_raw_payload(v)
        return sanitized
    elif isinstance(payload, list):
        return [sanitize_raw_payload(item) for item in payload]
    return payload


class PaymentVerificationService:
    """
    Business logic for client payment verification and secure provider webhooks.
    Enforces server-side tenant resolution, raw-bytes signature verification, replay protection, and payload sanitization.
    """

    def verify_payment(
        self,
        db: Session,
        current_user: IdentityUser,
        data: VerifyPaymentRequest,
    ) -> VerifyPaymentResponse:
        """
        Verifies a payment from a client callback.

        Steps:
        1. Resolve active tenant context from current_user.school_id.
        2. Retrieve target PaymentOrder.
        3. Enforce relationship authorization via enforce_relationship_access.
        4. Check if order is already PAID (prevent state regression).
        5. Validate provider, gateway order ID, amount, and currency consistency.
        6. Cryptographically verify signature using gateway adapter.
        7. Atomically persist PaymentTransaction and update PaymentOrder status to PAID.
        """
        school_id = getattr(current_user, "school_id", None)
        if not school_id:
            raise ForbiddenException("Active tenant context is required.")

        # 1. Retrieve local PaymentOrder
        order = db.scalar(
            select(PaymentOrder).where(
                PaymentOrder.id == data.payment_order_id,
                PaymentOrder.school_id == school_id,
                PaymentOrder.is_deleted == False,
            )
        )
        if not order:
            raise NotFoundException("Payment order not found.")

        # 2. Retrieve StudentFeeAssignment & enforce relationship access
        assignment = db.scalar(
            select(StudentFeeAssignment).where(
                StudentFeeAssignment.id == order.student_fee_assignment_id,
                StudentFeeAssignment.school_id == school_id,
                StudentFeeAssignment.is_deleted == False,
            )
        )
        if not assignment:
            raise NotFoundException("Student fee assignment not found.")

        enforce_relationship_access(
            db,
            school_id=school_id,
            current_user=current_user,
            target_student_id=assignment.student_id,
        )

        # 3. If already PAID, trigger settlement check & return response
        if order.status == PaymentOrderStatus.PAID:
            existing_txn = db.scalar(
                select(PaymentTransaction).where(
                    PaymentTransaction.provider == order.provider,
                    PaymentTransaction.gateway_transaction_id == data.gateway_payment_id,
                    PaymentTransaction.is_deleted == False,
                )
            )
            if existing_txn and existing_txn.status == PaymentTransactionStatus.SUCCESS:
                payment_settlement_service.settle_payment_transaction(db, existing_txn)

            return VerifyPaymentResponse(
                success=True,
                message="Payment has already been verified and processed.",
                order_id=order.id,
                status=order.status,
                gateway_transaction_id=data.gateway_payment_id,
                amount=order.amount,
                currency=order.currency,
            )

        # 4. Validate Provider Consistency
        if order.provider != data.provider:
            raise BadRequestException(f"Payment provider mismatch. Order expects '{order.provider.value}'.")

        # 5. Validate Gateway Order ID
        if order.gateway_order_id != data.gateway_order_id:
            raise BadRequestException("Gateway order ID mismatch.")

        # 6. Validate Amount & Currency (if client supplied)
        if data.amount is not None and data.amount != order.amount:
            raise BadRequestException(f"Amount mismatch. Submitted {data.amount}, expected {order.amount}.")

        if data.currency is not None and data.currency.upper() != order.currency.upper():
            raise BadRequestException(f"Currency mismatch. Submitted {data.currency}, expected {order.currency}.")

        # 7. Resolve provider credentials and verify signature
        key_id, key_secret, webhook_secret = PaymentOrderService._resolve_credentials(order.provider, school_id=school_id)
        gateway = PaymentGatewayFactory.get_gateway(
            provider=order.provider,
            key_id=key_id,
            key_secret=key_secret,
            webhook_secret=webhook_secret,
        )

        verification_req = GatewayPaymentVerificationRequest(
            provider=order.provider,
            gateway_order_id=data.gateway_order_id,
            gateway_payment_id=data.gateway_payment_id,
            gateway_signature=data.gateway_signature,
        )

        verification_res = gateway.verify_payment_signature(verification_req)
        if not verification_res.is_valid:
            raise BadRequestException("Payment signature verification failed.")

        # 8. Atomically persist PaymentTransaction and mark PaymentOrder as PAID
        existing_txn = db.scalar(
            select(PaymentTransaction).where(
                PaymentTransaction.provider == order.provider,
                PaymentTransaction.gateway_transaction_id == data.gateway_payment_id,
                PaymentTransaction.is_deleted == False,
            )
        )

        if not existing_txn:
            sanitized_resp = sanitize_raw_payload({
                "gateway_order_id": data.gateway_order_id,
                "gateway_payment_id": data.gateway_payment_id,
                "verification_message": verification_res.message,
            })
            txn = PaymentTransaction(
                school_id=school_id,
                payment_order_id=order.id,
                provider=order.provider,
                gateway_transaction_id=data.gateway_payment_id,
                status=PaymentTransactionStatus.SUCCESS,
                amount=order.amount,
                currency=order.currency,
                raw_response=sanitized_resp,
            )
            db.add(txn)
            db.flush()
        else:
            txn = existing_txn

        order.status = PaymentOrderStatus.PAID
        db.commit()
        db.refresh(order)

        logger.info(
            "Successfully verified payment for PaymentOrder %s (gateway txn: %s)",
            order.id,
            data.gateway_payment_id,
        )

        # Trigger automated fee settlement
        payment_settlement_service.settle_payment_transaction(db, txn)

        return VerifyPaymentResponse(
            success=True,
            message="Payment verified successfully.",
            order_id=order.id,
            status=order.status,
            gateway_transaction_id=data.gateway_payment_id,
            amount=order.amount,
            currency=order.currency,
        )

    def process_webhook(
        self,
        db: Session,
        provider_str: str,
        raw_body: bytes,
        signature_header: str | None,
    ) -> WebhookResponse:
        """
        Processes incoming unauthenticated provider webhooks safely.

        Security Enforcement:
        - Raw HTTP body bytes signature verification.
        - Server-controlled tenant resolution via gateway_order_id lookup in database.
        - Replay protection via gateway_event_id and conflicting replay detection.
        - Transaction-level idempotency via provider + gateway_transaction_id unique index.
        - Order state transition safety (cannot regress PAID orders).
        - Payload sanitization before persistence.
        """
        # 1. Provider enum resolution
        try:
            provider = PaymentProvider(provider_str.upper())
        except ValueError:
            raise BadRequestException(f"Unsupported payment provider: '{provider_str}'")

        if not signature_header:
            raise BadRequestException("Missing gateway signature header.")

        # 2. Parse payload to extract event_id and gateway_order_id
        try:
            body_str = raw_body.decode("utf-8")
            payload_data = json.loads(body_str)
        except Exception as e:
            raise BadRequestException(f"Invalid JSON payload: {e}")

        event_id = None
        gateway_order_id = None

        if provider == PaymentProvider.RAZORPAY:
            event_id = payload_data.get("event_id") or payload_data.get("id")
            payload_sub = payload_data.get("payload", {})
            p_entity = payload_sub.get("payment", {}).get("entity", {})
            o_entity = payload_sub.get("order", {}).get("entity", {})
            gateway_order_id = p_entity.get("order_id") or o_entity.get("id")
        elif provider == PaymentProvider.STRIPE:
            event_id = payload_data.get("id")
            data_obj = payload_data.get("data", {}).get("object", {})
            event_type = payload_data.get("type", "")
            if event_type.startswith("checkout.session"):
                gateway_order_id = data_obj.get("id")
            else:
                gateway_order_id = data_obj.get("metadata", {}).get("order_id") or data_obj.get("id")

        if not gateway_order_id:
            raise BadRequestException("Webhook payload missing gateway order identifier.")

        # 3. Server-Controlled Tenant Resolution
        # Lookup local PaymentOrder by (provider, gateway_order_id) to resolve tenant school_id securely!
        order = db.scalar(
            select(PaymentOrder).where(
                PaymentOrder.provider == provider,
                PaymentOrder.gateway_order_id == gateway_order_id,
                PaymentOrder.is_deleted == False,
            )
        )
        if not order:
            raise NotFoundException("Payment order not found for gateway webhook.")

        school_id = order.school_id

        # 4. Resolve tenant credentials & verify signature against raw HTTP request bytes
        key_id, key_secret, webhook_secret = PaymentOrderService._resolve_credentials(provider, school_id=school_id)
        gateway = PaymentGatewayFactory.get_gateway(
            provider=provider,
            key_id=key_id,
            key_secret=key_secret,
            webhook_secret=webhook_secret,
        )

        try:
            event = gateway.parse_webhook_event(raw_body, signature=signature_header, secret=webhook_secret)
        except PaymentSignatureVerificationError:
            raise BadRequestException("Invalid webhook signature.")
        except Exception as exc:
            logger.warning("Webhook parsing failed: %s", exc)
            raise BadRequestException(f"Invalid webhook request: {exc}")

        # 5. Replay & Idempotency Protection: Check existing gateway_event_id
        if event.event_id:
            existing_event_txn = db.scalar(
                select(PaymentTransaction).where(
                    PaymentTransaction.gateway_event_id == event.event_id,
                    PaymentTransaction.is_deleted == False,
                )
            )
            if existing_event_txn:
                # Check for conflicting replay
                conflicting = False
                if existing_event_txn.payment_order_id != order.id:
                    conflicting = True
                if event.gateway_transaction_id and existing_event_txn.gateway_transaction_id != event.gateway_transaction_id:
                    conflicting = True
                if event.amount is not None and existing_event_txn.amount != event.amount:
                    conflicting = True
                if event.currency is not None and existing_event_txn.currency.upper() != event.currency.upper():
                    conflicting = True

                if conflicting:
                    logger.error("Conflicting replay detected for event_id %s", event.event_id)
                    raise BadRequestException("Conflicting webhook replay detected.")

                logger.info("Duplicate webhook event %s already processed. Acknowledging safely.", event.event_id)
                return WebhookResponse(
                    success=True,
                    message="Event already processed.",
                    event_id=event.event_id,
                    processed=False,
                )

        # 6. Amount & Currency Integrity Validation
        if event.amount is not None and event.amount != order.amount:
            logger.error("Webhook amount mismatch: order amount %s vs webhook amount %s", order.amount, event.amount)
            raise BadRequestException(f"Amount mismatch. Order amount is {order.amount}, received {event.amount}.")

        if event.currency is not None and event.currency.upper() != order.currency.upper():
            logger.error("Webhook currency mismatch: order currency %s vs webhook currency %s", order.currency, event.currency)
            raise BadRequestException(f"Currency mismatch. Order currency is {order.currency}, received {event.currency}.")

        # 7. Transaction-level Idempotency: Check provider + gateway_transaction_id
        txn_id = event.gateway_transaction_id or f"txn_evt_{event.event_id}"
        existing_txn = db.scalar(
            select(PaymentTransaction).where(
                PaymentTransaction.provider == provider,
                PaymentTransaction.gateway_transaction_id == txn_id,
                PaymentTransaction.is_deleted == False,
            )
        )

        target_txn = None
        if not existing_txn:
            sanitized_payload = sanitize_raw_payload(event.raw_payload or {})
            new_txn = PaymentTransaction(
                school_id=school_id,
                payment_order_id=order.id,
                provider=provider,
                gateway_transaction_id=txn_id,
                gateway_event_id=event.event_id,
                status=event.status or PaymentTransactionStatus.SUCCESS,
                amount=order.amount,
                currency=order.currency,
                event_timestamp=event.event_timestamp,
                raw_response=sanitized_payload,
            )
            try:
                db.add(new_txn)
                db.flush()
                target_txn = new_txn
            except IntegrityError:
                db.rollback()
                logger.warning("Duplicate transaction caught by DB constraint: %s", txn_id)
                target_txn = db.scalar(
                    select(PaymentTransaction).where(
                        PaymentTransaction.provider == provider,
                        PaymentTransaction.gateway_transaction_id == txn_id,
                        PaymentTransaction.is_deleted == False,
                    )
                )
        else:
            target_txn = existing_txn

        # 8. Order State Transition Safety: Prevent regression if order is already PAID
        if order.status != PaymentOrderStatus.PAID:
            if event.status == PaymentTransactionStatus.SUCCESS:
                order.status = PaymentOrderStatus.PAID
            elif event.status == PaymentTransactionStatus.FAILED:
                order.status = PaymentOrderStatus.FAILED
            db.commit()

        # 9. Automated Fee Settlement for SUCCESS transactions
        if target_txn and target_txn.status == PaymentTransactionStatus.SUCCESS:
            payment_settlement_service.settle_payment_transaction(db, target_txn)

        return WebhookResponse(
            success=True,
            message="Webhook processed successfully.",
            event_id=event.event_id,
            processed=True,
        )


payment_verification_service = PaymentVerificationService()
