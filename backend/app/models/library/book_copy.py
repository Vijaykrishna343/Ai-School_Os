from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
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

from app.common.enums.library import BookCondition, BookCopyStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.library.book import Book
    from app.models.library.loan import BookLoan


class BookCopy(CommonModel):
    """
    Represents an individual physical copy (accession record) of a book.
    Maintains accession uniqueness, physical condition, and availability status.
    Enforces strict tenant isolation via school_id.
    """

    __tablename__ = "library_book_copies"

    __table_args__ = (
        CheckConstraint(
            "acquisition_price IS NULL OR acquisition_price >= 0",
            name="ck_library_book_copy_price_non_neg",
        ),
        Index("ix_library_book_copies_school_id", "school_id"),
        Index("ix_library_book_copies_book_id", "book_id"),
        Index("ix_library_book_copies_status", "status"),
        Index("ix_library_book_copies_condition", "condition"),
        Index("ix_library_book_copies_shelf", "shelf_location"),
        Index(
            "uq_library_copy_school_accession",
            "school_id",
            "accession_number",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index(
            "uq_library_copy_school_barcode",
            "school_id",
            "barcode",
            unique=True,
            postgresql_where=text("is_deleted = false AND barcode IS NOT NULL"),
            sqlite_where=text("is_deleted = 0 AND barcode IS NOT NULL"),
        ),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("library_books.id", ondelete="CASCADE"),
        nullable=False,
    )

    accession_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    barcode: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    rfid_tag: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    status: Mapped[BookCopyStatus] = mapped_column(
        Enum(BookCopyStatus, name="bookcopystatus", native_enum=False),
        nullable=False,
        default=BookCopyStatus.AVAILABLE,
    )

    condition: Mapped[BookCondition] = mapped_column(
        Enum(BookCondition, name="bookcondition", native_enum=False),
        nullable=False,
        default=BookCondition.GOOD,
    )

    shelf_location: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    acquisition_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    acquisition_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    book: Mapped[Book] = orm_relationship(
        "Book",
        back_populates="copies",
    )

    loans: Mapped[list[BookLoan]] = orm_relationship(
        "BookLoan",
        back_populates="book_copy",
        cascade="all, delete-orphan",
    )
