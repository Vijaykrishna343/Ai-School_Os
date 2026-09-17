from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
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

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.library.book import Book


class BookCategory(CommonModel):
    """
    Represents a subject/topic category for organizing catalog books.
    Enforces tenant isolation via school_id.
    """

    __tablename__ = "library_categories"

    __table_args__ = (
        Index("ix_library_categories_school_id", "school_id"),
        Index(
            "uq_library_category_school_name",
            "school_id",
            "name",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index(
            "uq_library_category_school_code",
            "school_id",
            "code",
            unique=True,
            postgresql_where=text("is_deleted = false AND code IS NOT NULL"),
            sqlite_where=text("is_deleted = 0 AND code IS NOT NULL"),
        ),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    books: Mapped[list[Book]] = orm_relationship(
        "Book",
        back_populates="category",
    )
