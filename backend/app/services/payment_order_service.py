from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.authorization import enforce_relationship_access
from app.common.enums.fees import StudentFeeAssignmentStatus
from app.common.enums.payment import PaymentOrderStatus, PaymentProvider
from app.common.exceptions import (
    BadRequestException,
    ForbiddenException,
    InternalServerException,
    NotFoundException,
    ValidationException,
)
from app.common.exceptions.payment import (
    PaymentAuthenticationError,
    PaymentConfigurationError,
    PaymentGatewayError,
    PaymentInvalidRequestError,
    PaymentProviderUnavailableError,
    PaymentUnsupportedProviderError,
)
from app.common.logger.logger import get_logger
from app.core.config import settings
from app.identity.models.user import IdentityUser
from app.models.fees.student_fee_assignment import StudentFeeAssignment
from app.models.payment.payment_order import PaymentOrder
from app.schemas.payment import (
    CreatePaymentOrderRequest,
    GatewayOrderRequest,
    PaymentOrderResponse,
    PaymentOrderStatusResponse,
)
from app.services.fee_service import FeeService
from app.services.payment_config_service import payment_config_service
from app.services.payment_gateway_service import PaymentGatewayFactory

logger = get_logger(__name__)


class PaymentOrderService:
    """
    Business logic for creating and managing Payment Orders.
    Enforces server-side amount calculation, tenant isolation, and relationship security.
    """

    @staticmethod
    def get_order_by_id(
        db: Session,
        order_id: UUID,
        current_school_id: UUID,
    ) -> PaymentOrder:
        """
        Retrieves a PaymentOrder by ID scoped to current school.
        """
        stmt = select(PaymentOrder).where(
            PaymentOrder.id == order_id,
            PaymentOrder.school_id == current_school_id,
            PaymentOrder.is_deleted == False,
        )
        order = db.scalar(stmt)
        if not order:
            raise NotFoundException("Payment order not found.")
        return order

    def create_payment_order(
        self,
        db: Session,
        current_user: IdentityUser,
        data: CreatePaymentOrderRequest,
    ) -> PaymentOrderResponse:
        """
        Creates a payment order for a StudentFeeAssignment.

        Steps:
        1. Resolve tenant context from current_user.school_id.
        2. Retrieve target StudentFeeAssignment.
        3. Enforce relationship authorization (parent->child, student->self, staff).
        4. Validate fee assignment eligibility & calculate payable balance server-side.
        5. Check idempotency (reuse matching active existing order if available).
        6. Resolve payment gateway configuration and credentials safely.
        7. Call PaymentGatewayFactory to create order on gateway.
        8. Persist PaymentOrder and return sanitized response.
        """
        school_id = getattr(current_user, "school_id", None)
        if not school_id:
            raise ForbiddenException("Active tenant context is required.")

        # 1. Load assignment & verify tenant boundary
        stmt = select(StudentFeeAssignment).where(
            StudentFeeAssignment.id == data.student_fee_assignment_id,
            StudentFeeAssignment.school_id == school_id,
            StudentFeeAssignment.is_deleted == False,
        )
        assignment = db.scalar(stmt)

        if not assignment:
            # Failsafe check for cross-tenant disclosure prevention
            raise NotFoundException("Student fee assignment not found.")

        # 2. Relationship access check
        enforce_relationship_access(
            db,
            school_id=school_id,
            current_user=current_user,
            target_student_id=assignment.student_id,
        )

        # 3. Check fee assignment status & calculate metrics
        if assignment.status == StudentFeeAssignmentStatus.CANCELLED:
            raise ValidationException("Fee assignment is cancelled and cannot accept payments.")

        metrics = FeeService.calculate_metrics(assignment)
        payable_amount = metrics["outstanding_due"]

        if assignment.status == StudentFeeAssignmentStatus.PAID or payable_amount <= Decimal("0.00"):
            raise ValidationException("Fee assignment is already fully paid.")

        # 4. Resolve provider
        target_provider = data.provider or PaymentProvider.RAZORPAY
        if not isinstance(target_provider, PaymentProvider):
            try:
                target_provider = PaymentProvider(str(target_provider).upper())
            except ValueError:
                raise ValidationException(f"Unsupported payment provider: '{data.provider}'")

        # 5. Idempotency Check: search active orders for same assignment
        active_order_stmt = select(PaymentOrder).where(
            PaymentOrder.student_fee_assignment_id == assignment.id,
            PaymentOrder.school_id == school_id,
            PaymentOrder.status.in_([PaymentOrderStatus.CREATED, PaymentOrderStatus.PENDING]),
            PaymentOrder.is_deleted == False,
        ).order_by(PaymentOrder.created_at.desc())
        active_orders = db.scalars(active_order_stmt).all()

        for active_order in active_orders:
            if active_order.provider == target_provider and active_order.amount == payable_amount:
                logger.info(
                    "Reusing existing active PaymentOrder %s for assignment %s",
                    active_order.id,
                    assignment.id,
                )
                return PaymentOrderResponse.model_validate(active_order)
            else:
                # Cancel superseded active orders
                active_order.status = PaymentOrderStatus.CANCELLED

        # 6. Resolve provider credentials from settings
        key_id, key_secret, webhook_secret = self._resolve_credentials(target_provider)

        if not key_id or not key_secret:
            raise ValidationException(
                f"Payment provider '{target_provider.value}' is not configured for this school."
            )

        # 7. Gateway order creation through abstraction
        customer_name = None
        customer_email = None
        customer_phone = None

        if getattr(assignment, "student", None):
            student_obj = assignment.student
            customer_name = getattr(student_obj, "full_name", None) or f"{getattr(student_obj, 'first_name', '')} {getattr(student_obj, 'last_name', '')}".strip() or None
            customer_email = getattr(student_obj, "email", None)
            customer_phone = getattr(student_obj, "phone_number", None) or getattr(student_obj, "emergency_contact_number", None)

        gateway_req = GatewayOrderRequest(
            amount=payable_amount,
            currency="INR",
            receipt=f"SFA-{str(assignment.id)[:18]}",
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            notes={
                "school_id": str(school_id),
                "assignment_id": str(assignment.id),
                "student_id": str(assignment.student_id),
            },
        )

        try:
            gateway = PaymentGatewayFactory.get_gateway(
                provider=target_provider,
                key_id=key_id,
                key_secret=key_secret,
                webhook_secret=webhook_secret,
            )
            gateway_res = gateway.create_order(gateway_req)
        except PaymentConfigurationError as exc:
            logger.error("Payment configuration error: %s", exc)
            raise ValidationException(f"Payment configuration error: {exc.message}")
        except PaymentAuthenticationError as exc:
            logger.error("Payment gateway auth failed: %s", exc)
            raise BadRequestException("Payment gateway credentials rejected.")
        except PaymentInvalidRequestError as exc:
            logger.error("Payment invalid request: %s", exc)
            raise ValidationException(f"Invalid payment order request: {exc.message}")
        except PaymentProviderUnavailableError as exc:
            logger.error("Payment gateway timeout/unavailable: %s", exc)
            raise InternalServerException("Payment gateway is temporarily unavailable. Please try again.")
        except PaymentUnsupportedProviderError as exc:
            raise ValidationException(exc.message)
        except PaymentGatewayError as exc:
            logger.error("Payment gateway error: %s", exc)
            raise BadRequestException(f"Payment order creation failed: {exc.message}")
        except Exception as exc:
            logger.exception("Unexpected error during gateway order creation: %s", exc)
            raise InternalServerException("Unable to create payment order at this time.")

        # 8. Persist PaymentOrder
        payment_order = PaymentOrder(
            school_id=school_id,
            student_fee_assignment_id=assignment.id,
            provider=target_provider,
            gateway_order_id=gateway_res.gateway_order_id,
            amount=payable_amount,
            currency=gateway_res.currency or "INR",
            status=PaymentOrderStatus.CREATED,
            extra_metadata={
                "receipt": gateway_req.receipt,
                "notes": gateway_req.notes,
            },
        )

        db.add(payment_order)
        db.flush()
        db.commit()
        db.refresh(payment_order)

        logger.info(
            "Successfully created PaymentOrder %s (gateway: %s) for assignment %s",
            payment_order.id,
            payment_order.gateway_order_id,
            assignment.id,
        )

        return PaymentOrderResponse.model_validate(payment_order)

    @staticmethod
    def _resolve_credentials(provider: PaymentProvider, school_id: UUID | str | None = None) -> tuple[str, str, str]:
        """
        Resolves gateway credentials securely from PaymentConfigService or application settings.
        """
        key_id, key_secret, webhook_secret = payment_config_service.resolve_credentials(provider, school_id)
        if key_id and key_secret:
            return (key_id, key_secret, webhook_secret)

        if provider == PaymentProvider.RAZORPAY:
            return (
                getattr(settings, "RAZORPAY_KEY_ID", "") or "",
                getattr(settings, "RAZORPAY_KEY_SECRET", "") or "",
                getattr(settings, "RAZORPAY_WEBHOOK_SECRET", "") or "",
            )
        if provider == PaymentProvider.STRIPE:
            return (
                getattr(settings, "STRIPE_PUBLISHABLE_KEY", "") or "",
                getattr(settings, "STRIPE_SECRET_KEY", "") or "",
                getattr(settings, "STRIPE_WEBHOOK_SECRET", "") or "",
            )
        return ("", "", "")

    def get_order_status(
        self,
        db: Session,
        current_user: IdentityUser,
        order_id: UUID,
    ) -> PaymentOrderStatusResponse:
        """
        Retrieves authoritative payment order status for UI polling.
        Enforces tenant isolation and relationship authorization.
        """
        school_id = getattr(current_user, "school_id", None)
        if not school_id:
            raise ForbiddenException("Active tenant context is required.")

        order = db.scalar(
            select(PaymentOrder).where(
                PaymentOrder.id == order_id,
                PaymentOrder.school_id == school_id,
                PaymentOrder.is_deleted == False,
            )
        )
        if not order:
            raise NotFoundException("Payment order not found.")

        # Relationship authorization check
        assignment = db.scalar(
            select(StudentFeeAssignment).where(
                StudentFeeAssignment.id == order.student_fee_assignment_id,
                StudentFeeAssignment.school_id == school_id,
                StudentFeeAssignment.is_deleted == False,
            )
        )
        if assignment:
            enforce_relationship_access(
                db,
                school_id=school_id,
                current_user=current_user,
                target_student_id=assignment.student_id,
            )

        # Check for settled FeePayment receipt
        from app.models.fees.fee_payment import FeePayment
        fee_payment = db.scalar(
            select(FeePayment).where(
                FeePayment.student_fee_assignment_id == order.student_fee_assignment_id,
                FeePayment.school_id == school_id,
                FeePayment.is_deleted == False,
            ).order_by(FeePayment.created_at.desc())
        )

        receipt_num = fee_payment.receipt_number if fee_payment else None
        is_settled = order.status == PaymentOrderStatus.PAID

        return PaymentOrderStatusResponse(
            order_id=order.id,
            school_id=order.school_id,
            student_fee_assignment_id=order.student_fee_assignment_id,
            provider=order.provider,
            gateway_order_id=order.gateway_order_id,
            amount=order.amount,
            currency=order.currency,
            status=order.status,
            receipt_number=receipt_num,
            is_settled=is_settled,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )


payment_order_service = PaymentOrderService()

