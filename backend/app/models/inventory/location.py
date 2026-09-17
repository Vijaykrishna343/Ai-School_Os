from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
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

from app.common.enums.inventory import InventoryLocationType
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.inventory.asset import PhysicalAsset
    from app.models.inventory.stock import InventoryStock
    from app.models.school.school import School


class InventoryLocation(CommonModel):
    """
    Represents a physical storage location, storeroom, lab, or warehouse.
    """

    __tablename__ = "inventory_locations"

    __table_args__ = (
        Index("ix_inventory_locations_school_id", "school_id"),
        Index("ix_inventory_locations_parent_id", "parent_location_id"),
        Index(
            "uq_inventory_location_school_code",
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

    location_type: Mapped[InventoryLocationType] = mapped_column(
        Enum(InventoryLocationType, name="inventory_location_type", create_constraint=False),
        nullable=False,
        default=InventoryLocationType.STORE_ROOM,
    )

    parent_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_locations.id", ondelete="SET NULL"),
        nullable=True,
    )

    building_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
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

    parent_location: Mapped[InventoryLocation | None] = orm_relationship(
        "InventoryLocation",
        remote_side="InventoryLocation.id",
        foreign_keys=[parent_location_id],
        back_populates="child_locations",
        lazy="select",
    )

    child_locations: Mapped[list[InventoryLocation]] = orm_relationship(
        "InventoryLocation",
        foreign_keys=[parent_location_id],
        back_populates="parent_location",
        lazy="select",
    )

    stock_records: Mapped[list[InventoryStock]] = orm_relationship(
        "InventoryStock",
        back_populates="location",
        lazy="select",
    )

    assets: Mapped[list[PhysicalAsset]] = orm_relationship(
        "PhysicalAsset",
        back_populates="location",
        lazy="select",
    )
