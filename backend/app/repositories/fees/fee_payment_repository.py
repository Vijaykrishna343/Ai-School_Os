from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums.fees import PaymentMode
from app.models.fees.fee_payment import FeePayment
from app.repositories.base import BaseRepository


class FeePaymentRepository(BaseRepository[FeePayment]):
    """
    Repository for FeePayment database operations.
    """

    def __init__(self) -> None:
        super().__init__(FeePayment)

    def get_by_id_and_school(
        self,
        db: Session,
        payment_id: UUID,
        school_id: UUID,
    ) -> FeePayment | None:
        """
        Retrieve an active FeePayment by ID and school_id.
        """
        return db.scalar(
            select(FeePayment).where(
                FeePayment.id == payment_id,
                FeePayment.school_id == school_id,
                FeePayment.is_deleted.is_(False),
            )
        )

    def exists_receipt_number(
        self,
        db: Session,
        school_id: UUID,
        receipt_number: str,
    ) -> bool:
        """
        Check if an active payment with the receipt_number exists within the school.
        """
        return (
            db.scalar(
                select(FeePayment).where(
                    FeePayment.school_id == school_id,
                    FeePayment.receipt_number == receipt_number,
                    FeePayment.is_deleted.is_(False),
                )
            )
            is not None
        )

    def list_payments(
        self,
        db: Session,
        school_id: UUID,
        assignment_id: UUID | None = None,
        payment_mode: PaymentMode | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[FeePayment], int]:
        """
        List active fee payments for a school matching filters.
        """
        query = select(FeePayment).where(
            FeePayment.school_id == school_id,
            FeePayment.is_deleted.is_(False),
        )

        if assignment_id is not None:
            query = query.where(FeePayment.student_fee_assignment_id == assignment_id)

        if payment_mode is not None:
            query = query.where(FeePayment.payment_mode == payment_mode)

        total = (
            db.scalar(select(func.count()).select_from(query.subquery()))
            or 0
        )

        query = (
            query.order_by(FeePayment.payment_date.desc(), FeePayment.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        return list(db.scalars(query)), total


fee_payment_repository = FeePaymentRepository()
