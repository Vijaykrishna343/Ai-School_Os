from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    Enum,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.library import BookReservationStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.library.book import Book
    from app.models.library.member import LibraryMember


class BookReservation(CommonModel):
    """
    Represents a hold/reservation placed by a member for an unavailable catalog title.
    Enforces that a member cannot place multiple pending reservations for the same title.
    Enforces strict tenant isolation via school_id.
    """

    __tablename__ = "library_book_reservations"

    __table_args__ = (
        Index("ix_library_book_reservations_school_id", "school_id"),
        Index("ix_library_book_reservations_member_id", "member_id"),
        Index("ix_library_book_reservations_book_id", "book_id"),
        Index("ix_library_book_reservations_status", "status"),
        Index("ix_library_book_reservations_date", "reservation_date"),
        Index(
            "uq_pending_member_book_reservation",
            "school_id",
            "member_id",
            "book_id",
            unique=True,
            postgresql_where=text("is_deleted = false AND status = 'PENDING'"),
            sqlite_where=text("is_deleted = 0 AND status = 'PENDING'"),
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

    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("library_books.id", ondelete="CASCADE"),
        nullable=False,
    )

    reservation_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    status: Mapped[BookReservationStatus] = mapped_column(
        Enum(BookReservationStatus, name="bookreservationstatus", native_enum=False),
        nullable=False,
        default=BookReservationStatus.PENDING,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    member: Mapped[LibraryMember] = orm_relationship(
        "LibraryMember",
        back_populates="reservations",
    )

    book: Mapped[Book] = orm_relationship(
        "Book",
        back_populates="reservations",
    )
