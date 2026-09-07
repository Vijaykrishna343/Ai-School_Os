from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums.fees import PaymentMode
from app.common.enums.payment import PaymentTransactionStatus
from app.common.exceptions import (
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.common.logger.logger import get_logger
from app.models.fees.fee_payment import FeePayment
from app.models.fees.student_fee_assignment import StudentFeeAssignment
from app.models.payment.payment_order import PaymentOrder
from app.models.payment.payment_transaction import PaymentTransaction
from app.models.student.student import Student
from app.schemas.fees.fees import FeePaymentCreate
from app.services.fee_service import fee_service

logger = get_logger(__name__)


def map_payment_mode(payment_method: str | None) -> PaymentMode:
    """
    Maps gateway payment method string to project PaymentMode enum.
    """
    if payment_method:
        pm_lower = payment_method.lower()
        if "upi" in pm_lower:
            return PaymentMode.UPI
        if "card" in pm_lower:
            return PaymentMode.CARD
        if "bank" in pm_lower or "netbanking" in pm_lower:
            return PaymentMode.BANK_TRANSFER
        if "cash" in pm_lower:
            return PaymentMode.CASH
        if "cheque" in pm_lower:
            return PaymentMode.CHEQUE
    return PaymentMode.CARD


class PaymentSettlementService:
    """
    Automated Fee Settlement Engine for the School ERP payment system.
    Takes a verified successful PaymentTransaction and applies its financial effect
    to the student's fee ledger idempotently and atomically.
    """

    def settle_payment_transaction(
        self,
        db: Session,
        transaction_id_or_obj: UUID | PaymentTransaction | str,
    ) -> FeePayment:
        """
        Settles a verified PaymentTransaction against the student's fee assignment.

        Steps:
        1. Row lock PaymentTransaction via with_for_update().
        2. Verify transaction status is SUCCESS.
        3. Resolve PaymentOrder & StudentFeeAssignment with row locks.
        4. Validate tenant consistency across Transaction, Order, Assignment, and Student.
        5. Validate amount & currency exact match.
        6. Check idempotency: Return existing FeePayment if already settled.
        7. Record payment using FeeService.record_payment.
        """
        # 1. Resolve & Row-lock PaymentTransaction
        if isinstance(transaction_id_or_obj, PaymentTransaction):
            txn_id = transaction_id_or_obj.id
        elif isinstance(transaction_id_or_obj, str):
            txn_id = UUID(transaction_id_or_obj)
        else:
            txn_id = transaction_id_or_obj

        txn = db.scalar(
            select(PaymentTransaction)
            .where(
                PaymentTransaction.id == txn_id,
                PaymentTransaction.is_deleted == False,
            )
            .with_for_update()
        )
        if not txn:
            raise NotFoundException("PaymentTransaction", str(txn_id))

        # 2. Status Enforcement: Only SUCCESS transactions may settle
        if txn.status != PaymentTransactionStatus.SUCCESS:
            logger.warning(
                "Settlement rejected: PaymentTransaction %s status is %s",
                txn.id,
                txn.status,
            )
            raise ValidationException(
                f"Only successful payment transactions can be settled. Current status is {txn.status.value}."
            )

        # 3. Resolve PaymentOrder
        order = db.scalar(
            select(PaymentOrder)
            .where(
                PaymentOrder.id == txn.payment_order_id,
                PaymentOrder.is_deleted == False,
            )
            .with_for_update()
        )
        if not order:
            raise NotFoundException("PaymentOrder", str(txn.payment_order_id))

        # 4. Resolve StudentFeeAssignment
        assignment = db.scalar(
            select(StudentFeeAssignment)
            .where(
                StudentFeeAssignment.id == order.student_fee_assignment_id,
                StudentFeeAssignment.is_deleted == False,
            )
            .with_for_update()
        )
        if not assignment:
            raise NotFoundException("StudentFeeAssignment", str(order.student_fee_assignment_id))

        # Resolve Student
        student = db.scalar(
            select(Student).where(
                Student.id == assignment.student_id,
                Student.is_deleted == False,
            )
        )
        if not student:
            raise NotFoundException("Student", str(assignment.student_id))

        # 5. Tenant Consistency Validation (Fail Closed)
        if (
            txn.school_id != order.school_id
            or order.school_id != assignment.school_id
            or assignment.school_id != student.school_id
        ):
            logger.error(
                "Tenant mismatch during settlement for Txn %s: Txn school=%s, Order school=%s, Assignment school=%s, Student school=%s",
                txn.id,
                txn.school_id,
                order.school_id,
                assignment.school_id,
                student.school_id,
            )
            raise ForbiddenException("Cross-tenant settlement attempt detected.")

        # 6. Validate Amount & Currency (Exact Decimal Match)
        if Decimal(str(txn.amount)) != Decimal(str(order.amount)):
            logger.error(
                "Settlement amount mismatch: Txn amount %s vs Order amount %s",
                txn.amount,
                order.amount,
            )
            raise ValidationException(
                f"Transaction amount ({txn.amount}) does not match payment order amount ({order.amount})."
            )

        if txn.currency.upper() != order.currency.upper():
            logger.error(
                "Settlement currency mismatch: Txn currency %s vs Order currency %s",
                txn.currency,
                order.currency,
            )
            raise ValidationException(
                f"Transaction currency ({txn.currency}) does not match payment order currency ({order.currency})."
            )

        # 7. Idempotency Check: Existing settlement for this transaction
        existing_payment = db.scalar(
            select(FeePayment).where(
                FeePayment.school_id == txn.school_id,
                FeePayment.student_fee_assignment_id == assignment.id,
                FeePayment.reference_number == txn.gateway_transaction_id,
                FeePayment.is_deleted == False,
            )
        )
        if existing_payment:
            logger.info(
                "PaymentTransaction %s (gateway txn: %s) already settled via FeePayment %s (Receipt: %s)",
                txn.id,
                txn.gateway_transaction_id,
                existing_payment.id,
                existing_payment.receipt_number,
            )
            return existing_payment

        # 8. Outstanding Balance & Overpayment Check
        metrics = fee_service.calculate_metrics(assignment)
        outstanding = metrics["outstanding_due"]

        if Decimal(str(txn.amount)) > outstanding:
            logger.error(
                "Overpayment settlement rejected for Assignment %s: Txn amount %s > Outstanding %s",
                assignment.id,
                txn.amount,
                outstanding,
            )
            raise ValidationException(
                f"Settlement amount ({txn.amount}) exceeds outstanding due balance ({outstanding})."
            )

        # 9. Payment Mode & Create FeePayment via FeeService canonical path
        pm = map_payment_mode(txn.payment_method)
        pay_date = txn.event_timestamp.date() if txn.event_timestamp else date.today()

        fee_payment_create = FeePaymentCreate(
            student_fee_assignment_id=assignment.id,
            amount=txn.amount,
            payment_date=pay_date,
            payment_mode=pm,
            reference_number=txn.gateway_transaction_id,
            remarks=f"Online payment via {txn.provider.value} (Gateway Order: {order.gateway_order_id})",
        )

        fee_payment_resp = fee_service.record_payment(
            db=db,
            data=fee_payment_create,
            current_school_id=txn.school_id,
        )

        # Retrieve created FeePayment model
        created_payment = db.scalar(
            select(FeePayment).where(
                FeePayment.id == fee_payment_resp.id,
                FeePayment.is_deleted == False,
            )
        )
        if not created_payment:
            raise NotFoundException("FeePayment", str(fee_payment_resp.id))

        logger.info(
            "Successfully settled PaymentTransaction %s -> FeePayment %s (Receipt %s) for Assignment %s",
            txn.id,
            created_payment.id,
            created_payment.receipt_number,
            assignment.id,
        )

        return created_payment


payment_settlement_service = PaymentSettlementService()
