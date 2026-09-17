from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
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

from app.common.enums.inventory import AssetCondition, AssetStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.inventory.assignment import AssetAssignment
    from app.models.inventory.item import InventoryItem
    from app.models.inventory.location import InventoryLocation
    from app.models.inventory.vendor import InventoryVendor
    from app.models.school.school import School


class PhysicalAsset(CommonModel):
    """
    Represents an individually tracked durable physical asset (e.g. Laptop #IT-0042, Projector #AV-01).
    """

    __tablename__ = "physical_assets"

    __table_args__ = (
        Index("ix_physical_assets_school_id", "school_id"),
        Index("ix_physical_assets_item_id", "item_id"),
        Index("ix_physical_assets_location_id", "location_id"),
        Index("ix_physical_assets_vendor_id", "vendor_id"),
        Index("ix_physical_assets_status", "status"),
        Index(
            "uq_physical_asset_school_tag",
            "school_id",
            "asset_tag",
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

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="RESTRICT"),
        nullable=False,
    )

    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_locations.id", ondelete="SET NULL"),
        nullable=True,
    )

    vendor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_vendors.id", ondelete="SET NULL"),
        nullable=True,
    )

    asset_tag: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    serial_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    model_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus, name="asset_status", create_constraint=False),
        nullable=False,
        default=AssetStatus.AVAILABLE,
    )

    condition: Mapped[AssetCondition] = mapped_column(
        Enum(AssetCondition, name="asset_condition", create_constraint=False),
        nullable=False,
        default=AssetCondition.GOOD,
    )

    purchase_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    purchase_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    warranty_expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        String(1000),
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
        back_populates="assets",
        lazy="select",
    )

    location: Mapped[InventoryLocation | None] = orm_relationship(
        "InventoryLocation",
        foreign_keys=[location_id],
        back_populates="assets",
        lazy="select",
    )

    vendor: Mapped[InventoryVendor | None] = orm_relationship(
        "InventoryVendor",
        foreign_keys=[vendor_id],
        lazy="select",
    )

    assignments: Mapped[list[AssetAssignment]] = orm_relationship(
        "AssetAssignment",
        back_populates="asset",
        cascade="all, delete-orphan",
        lazy="select",
    )
