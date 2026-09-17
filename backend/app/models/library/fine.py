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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.library import LibraryFineReason, LibraryFineStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.identity.models.user import IdentityUser
    from app.models.library.loan import BookLoan
    from app.models.library.member import LibraryMember


class LibraryFine(CommonModel):
    """
    Represents a financial charge or fine associated with an overdue, lost, or damaged loan.
    Enforces exact decimal arithmetic and multi-tenant isolation via school_id.
    """

    __tablename__ = "library_fines"

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_library_fine_amount_non_neg"),
        Index("ix_library_fines_school_id", "school_id"),
        Index("ix_library_fines_loan_id", "loan_id"),
        Index("ix_library_fines_member_id", "member_id"),
        Index("ix_library_fines_status", "status"),
        Index("ix_library_fines_reason", "fine_reason"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    loan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("library_book_loans.id", ondelete="CASCADE"),
        nullable=False,
    )

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("library_members.id", ondelete="CASCADE"),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    fine_reason: Mapped[LibraryFineReason] = mapped_column(
        Enum(LibraryFineReason, name="libraryfinereason", native_enum=False),
        nullable=False,
        default=LibraryFineReason.OVERDUE,
    )

    status: Mapped[LibraryFineStatus] = mapped_column(
        Enum(LibraryFineStatus, name="libraryfinestatus", native_enum=False),
        nullable=False,
        default=LibraryFineStatus.PENDING,
    )

    paid_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    waived_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    waived_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    loan: Mapped[BookLoan] = orm_relationship(
        "BookLoan",
        back_populates="fines",
        foreign_keys=[loan_id],
    )

    member: Mapped[LibraryMember] = orm_relationship(
        "LibraryMember",
        back_populates="fines",
        foreign_keys=[member_id],
    )

    waived_by: Mapped[IdentityUser | None] = orm_relationship(
        "IdentityUser",
        foreign_keys=[waived_by_user_id],
    )
