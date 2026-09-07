from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.payment import PaymentOrderStatus, PaymentProvider
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.fees.student_fee_assignment import StudentFeeAssignment
    from app.models.payment.payment_transaction import PaymentTransaction
    from app.models.school.school import School


class PaymentOrder(CommonModel):
    """
    Represents an online payment checkout order created for a student fee assignment.
    """

    __tablename__ = "payment_orders"

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payment_orders_amount_positive"),
        UniqueConstraint(
            "provider",
            "gateway_order_id",
            name="uq_payment_orders_provider_gateway_order_id",
        ),
        Index("ix_payment_orders_school_id", "school_id"),
        Index("ix_payment_orders_assignment_id", "student_fee_assignment_id"),
        Index("ix_payment_orders_status", "status"),
        Index("ix_payment_orders_school_status", "school_id", "status"),
        Index("ix_payment_orders_school_created", "school_id", "created_at"),
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

    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(
            PaymentProvider,
            name="payment_provider",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    gateway_order_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="INR",
        nullable=False,
    )

    status: Mapped[PaymentOrderStatus] = mapped_column(
        Enum(
            PaymentOrderStatus,
            name="payment_order_status",
            native_enum=True,
            validate_strings=True,
        ),
        default=PaymentOrderStatus.CREATED,
        nullable=False,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    school: Mapped["School"] = orm_relationship()
    assignment: Mapped["StudentFeeAssignment"] = orm_relationship(
        back_populates="payment_orders"
    )
    transactions: Mapped[list["PaymentTransaction"]] = orm_relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
