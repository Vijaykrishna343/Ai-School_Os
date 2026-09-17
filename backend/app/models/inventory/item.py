from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
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

from app.common.enums.inventory import InventoryItemType
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.inventory.asset import PhysicalAsset
    from app.models.inventory.category import InventoryCategory
    from app.models.inventory.movement import InventoryStockMovement
    from app.models.inventory.stock import InventoryStock
    from app.models.school.school import School


class InventoryItem(CommonModel):
    """
    Represents an item master / catalog definition (e.g. A4 Notebook, Dell Latitude 5420, Science Beaker).
    """

    __tablename__ = "inventory_items"

    __table_args__ = (
        Index("ix_inventory_items_school_id", "school_id"),
        Index("ix_inventory_items_category_id", "category_id"),
        Index("ix_inventory_items_item_type", "item_type"),
        Index(
            "uq_inventory_item_school_code",
            "school_id",
            "item_code",
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

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )

    item_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    item_type: Mapped[InventoryItemType] = mapped_column(
        Enum(InventoryItemType, name="inventory_item_type", create_constraint=False),
        nullable=False,
        default=InventoryItemType.CONSUMABLE,
    )

    unit_of_measure: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PCS",
    )

    track_individually: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    reorder_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
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

    category: Mapped[InventoryCategory] = orm_relationship(
        "InventoryCategory",
        foreign_keys=[category_id],
        back_populates="items",
        lazy="select",
    )

    stock_records: Mapped[list[InventoryStock]] = orm_relationship(
        "InventoryStock",
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="select",
    )

    assets: Mapped[list[PhysicalAsset]] = orm_relationship(
        "PhysicalAsset",
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="select",
    )

    movements: Mapped[list[InventoryStockMovement]] = orm_relationship(
        "InventoryStockMovement",
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="select",
    )
