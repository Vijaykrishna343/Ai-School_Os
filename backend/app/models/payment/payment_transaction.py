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
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.payment import PaymentProvider, PaymentTransactionStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.payment.payment_order import PaymentOrder
    from app.models.school.school import School


class PaymentTransaction(CommonModel):
    """
    Represents a payment transaction or webhook event received from a payment gateway.
    """

    __tablename__ = "payment_transactions"

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payment_transactions_amount_positive"),
        Index(
            "uq_payment_transaction_provider_txn",
            "provider",
            "gateway_transaction_id",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index("ix_payment_transactions_school_id", "school_id"),
        Index("ix_payment_transactions_order_id", "payment_order_id"),
        Index("ix_payment_transactions_status", "status"),
        Index("ix_payment_transactions_school_created", "school_id", "created_at"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    payment_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_orders.id", ondelete="CASCADE"),
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

    gateway_transaction_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    gateway_event_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    status: Mapped[PaymentTransactionStatus] = mapped_column(
        Enum(
            PaymentTransactionStatus,
            name="payment_transaction_status",
            native_enum=True,
            validate_strings=True,
        ),
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

    payment_method: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    failure_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    event_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    raw_response: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    school: Mapped["School"] = orm_relationship()
    order: Mapped["PaymentOrder"] = orm_relationship(
        back_populates="transactions"
    )
