from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.library.book_copy import BookCopy
    from app.models.library.category import BookCategory
    from app.models.library.library import Library
    from app.models.library.reservation import BookReservation


class Book(CommonModel):
    """
    Represents a bibliographic book title record in the catalog.
    Physical copies are modeled separately via BookCopy.
    Enforces strict tenant isolation via school_id.
    """

    __tablename__ = "library_books"

    __table_args__ = (
        Index("ix_library_books_school_id", "school_id"),
        Index("ix_library_books_title", "title"),
        Index("ix_library_books_author", "author"),
        Index("ix_library_books_isbn", "isbn"),
        Index("ix_library_books_category_id", "category_id"),
        Index("ix_library_books_library_id", "library_id"),
        Index("ix_library_books_school_title", "school_id", "title"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    library_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("libraries.id", ondelete="SET NULL"),
        nullable=True,
    )

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("library_categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    subtitle: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    author: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    publisher: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    publication_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    isbn: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    edition: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    language: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="English",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    total_pages: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    library: Mapped[Library | None] = orm_relationship(
        "Library",
        back_populates="books",
    )

    category: Mapped[BookCategory | None] = orm_relationship(
        "BookCategory",
        back_populates="books",
    )

    copies: Mapped[list[BookCopy]] = orm_relationship(
        "BookCopy",
        back_populates="book",
        cascade="all, delete-orphan",
    )

    reservations: Mapped[list[BookReservation]] = orm_relationship(
        "BookReservation",
        back_populates="book",
        cascade="all, delete-orphan",
    )
