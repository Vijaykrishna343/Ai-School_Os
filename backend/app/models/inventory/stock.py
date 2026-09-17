from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
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
    from app.models.inventory.location import InventoryLocation
    from app.models.school.school import School


class InventoryStock(CommonModel):
    """
    Authoritative quantity-based stock level for an inventory item in a specific storage location.
    """

    __tablename__ = "inventory_stock"

    __table_args__ = (
        Index("ix_inventory_stock_school_id", "school_id"),
        Index("ix_inventory_stock_item_id", "item_id"),
        Index("ix_inventory_stock_location_id", "location_id"),
        Index(
            "uq_inventory_stock_item_location",
            "school_id",
            "item_id",
            "location_id",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        CheckConstraint("quantity >= 0", name="ck_inventory_stock_quantity_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="ck_inventory_stock_reserved_non_negative"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
    )

    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_locations.id", ondelete="CASCADE"),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    reserved_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    last_counted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    school: Mapped[School] = orm_relationship(
        "School",
        foreign_keys=[school_id],
        lazy="select",
    )

    item: Mapped[InventoryItem] = orm_relationship(
        "InventoryItem",
        foreign_keys=[item_id],
        back_populates="stock_records",
        lazy="select",
    )

    location: Mapped[InventoryLocation] = orm_relationship(
        "InventoryLocation",
        foreign_keys=[location_id],
        back_populates="stock_records",
        lazy="select",
    )
