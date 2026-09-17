from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.inventory import InventoryStockMovementType
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.identity.models.user import IdentityUser
    from app.models.inventory.item import InventoryItem
    from app.models.inventory.location import InventoryLocation
    from app.models.inventory.vendor import InventoryVendor
    from app.models.school.school import School


class InventoryStockMovement(CommonModel):
    """
    Append-only inventory movement and stock ledger transaction.
    """

    __tablename__ = "inventory_stock_movements"

    __table_args__ = (
        Index("ix_inv_movements_school_id", "school_id"),
        Index("ix_inv_movements_item_id", "item_id"),
        Index("ix_inv_movements_src_loc_id", "source_location_id"),
        Index("ix_inv_movements_dst_loc_id", "destination_location_id"),
        Index("ix_inv_movements_type", "movement_type"),
        Index("ix_inv_movements_date", "movement_date"),
        CheckConstraint("quantity > 0", name="ck_inv_movement_quantity_positive"),
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

    source_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_locations.id", ondelete="SET NULL"),
        nullable=True,
    )

    destination_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_locations.id", ondelete="SET NULL"),
        nullable=True,
    )

    movement_type: Mapped[InventoryStockMovementType] = mapped_column(
        Enum(InventoryStockMovementType, name="inventory_stock_movement_type", create_constraint=False),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    reference_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    vendor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_vendors.id", ondelete="SET NULL"),
        nullable=True,
    )

    performed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    movement_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(500),
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
        back_populates="movements",
        lazy="select",
    )

    source_location: Mapped[InventoryLocation | None] = orm_relationship(
        "InventoryLocation",
        foreign_keys=[source_location_id],
        lazy="select",
    )

    destination_location: Mapped[InventoryLocation | None] = orm_relationship(
        "InventoryLocation",
        foreign_keys=[destination_location_id],
        lazy="select",
    )

    vendor: Mapped[InventoryVendor | None] = orm_relationship(
        "InventoryVendor",
        foreign_keys=[vendor_id],
        lazy="select",
    )

    performed_by_user: Mapped[IdentityUser | None] = orm_relationship(
        "IdentityUser",
        foreign_keys=[performed_by_user_id],
        lazy="select",
    )
