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
    from app.models.inventory.item import InventoryItem
    from app.models.school.school import School


class InventoryCategory(CommonModel):
    """
    Represents an inventory category classification (e.g. Stationery, IT Equipment, Lab Supplies).
    """

    __tablename__ = "inventory_categories"

    __table_args__ = (
        Index("ix_inventory_categories_school_id", "school_id"),
        Index(
            "uq_inventory_category_school_code",
            "school_id",
            "code",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
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

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Relationships
    school: Mapped[School] = orm_relationship(
        "School",
        foreign_keys=[school_id],
        lazy="select",
    )

    items: Mapped[list[InventoryItem]] = orm_relationship(
        "InventoryItem",
        back_populates="category",
        cascade="all, delete-orphan",
        lazy="select",
    )
