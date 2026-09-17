from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.library import BookLoanStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.identity.models.user import IdentityUser
    from app.models.library.book_copy import BookCopy
    from app.models.library.fine import LibraryFine
    from app.models.library.member import LibraryMember


class BookLoan(CommonModel):
    """
    Represents a book copy issue / circulation transaction to a library member.
    Enforces that a single physical copy cannot have multiple active loans simultaneously.
    Enforces strict tenant isolation via school_id.
    """

    __tablename__ = "library_book_loans"

    __table_args__ = (
        CheckConstraint("due_date >= issue_date", name="ck_library_loan_due_after_issue"),
        CheckConstraint(
            "return_date IS NULL OR return_date >= issue_date",
            name="ck_library_loan_return_after_issue",
        ),
        CheckConstraint("renewal_count >= 0", name="ck_library_loan_renewal_count_non_neg"),
        Index("ix_library_book_loans_school_id", "school_id"),
        Index("ix_library_book_loans_member_id", "member_id"),
        Index("ix_library_book_loans_copy_id", "book_copy_id"),
        Index("ix_library_book_loans_status", "status"),
        Index("ix_library_book_loans_due_date", "due_date"),
        Index("ix_library_book_loans_issue_date", "issue_date"),
        Index(
            "uq_active_loan_per_book_copy",
            "school_id",
            "book_copy_id",
            unique=True,
            postgresql_where=text("is_deleted = false AND status IN ('ISSUED', 'OVERDUE')"),
            sqlite_where=text("is_deleted = 0 AND status IN ('ISSUED', 'OVERDUE')"),
        ),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("library_members.id", ondelete="CASCADE"),
        nullable=False,
    )

    book_copy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("library_book_copies.id", ondelete="CASCADE"),
        nullable=False,
    )

    issue_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    return_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    renewal_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    max_renewals: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=2,
    )

    status: Mapped[BookLoanStatus] = mapped_column(
        Enum(BookLoanStatus, name="bookloanstatus", native_enum=False),
        nullable=False,
        default=BookLoanStatus.ISSUED,
    )

    issued_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    received_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    member: Mapped[LibraryMember] = orm_relationship(
        "LibraryMember",
        back_populates="loans",
        foreign_keys=[member_id],
    )

    book_copy: Mapped[BookCopy] = orm_relationship(
        "BookCopy",
        back_populates="loans",
        foreign_keys=[book_copy_id],
    )

    issued_by: Mapped[IdentityUser | None] = orm_relationship(
        "IdentityUser",
        foreign_keys=[issued_by_user_id],
    )

    received_by: Mapped[IdentityUser | None] = orm_relationship(
        "IdentityUser",
        foreign_keys=[received_by_user_id],
    )

    fines: Mapped[list[LibraryFine]] = orm_relationship(
        "LibraryFine",
        back_populates="loan",
        cascade="all, delete-orphan",
    )
