from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.fees import PaymentMode
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.fees.student_fee_assignment import StudentFeeAssignment
    from app.models.school.school import School


class FeePayment(CommonModel):
    """
    Represents a payment made towards a student's fee assignment.
    """

    __tablename__ = "fee_payments"

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_fee_payments_amount_positive"),
        Index(
            "uq_fee_payment_receipt",
            "school_id",
            "receipt_number",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index("ix_fee_payments_school_id", "school_id"),
        Index("ix_fee_payments_assignment_id", "student_fee_assignment_id"),
        Index("ix_fee_payments_receipt_number", "receipt_number"),
        Index("ix_fee_payments_payment_date", "payment_date"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    student_fee_assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_fee_assignments.id", ondelete="CASCADE"),
        nullable=False,
    )

    receipt_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    payment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    payment_mode: Mapped[PaymentMode] = mapped_column(
        Enum(
            PaymentMode,
            name="payment_mode",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    reference_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    school: Mapped["School"] = orm_relationship()
    assignment: Mapped["StudentFeeAssignment"] = orm_relationship(
        back_populates="payments"
    )
