from __future__ import annotations

import uuid
from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    String,
    Time,
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
    from app.models.transport.driver import TransportDriver
    from app.models.transport.stop import RouteStop
    from app.models.transport.student_transport_allocation import StudentTransportAllocation
    from app.models.transport.vehicle import Vehicle


class TransportRoute(CommonModel):
    """
    Represents a transit route operated by the school (e.g., North Campus Route 1).
    Enforces strict multi-tenant isolation via school_id.
    """

    __tablename__ = "transport_routes"

    __table_args__ = (
        Index("ix_transport_routes_school_id", "school_id"),
        Index("ix_transport_routes_vehicle_id", "vehicle_id"),
        Index("ix_transport_routes_driver_id", "driver_id"),
        Index("ix_transport_routes_is_active", "is_active"),
        Index(
            "uq_transport_route_school_code",
            "school_id",
            "route_code",
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

    route_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    route_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transport_vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )

    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transport_drivers.id", ondelete="SET NULL"),
        nullable=True,
    )

    attendant_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    attendant_phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    morning_start_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    evening_start_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    vehicle: Mapped[Vehicle | None] = orm_relationship(
        "Vehicle",
        back_populates="routes",
        foreign_keys=[vehicle_id],
    )

    driver: Mapped[TransportDriver | None] = orm_relationship(
        "TransportDriver",
        back_populates="routes",
        foreign_keys=[driver_id],
    )

    stops: Mapped[list[RouteStop]] = orm_relationship(
        "RouteStop",
        back_populates="route",
        cascade="all, delete-orphan",
        order_by="RouteStop.sequence_order",
    )

    allocations: Mapped[list[StudentTransportAllocation]] = orm_relationship(
        "StudentTransportAllocation",
        back_populates="route",
    )

    @property
    def active_allocation_count(self) -> int:
        if hasattr(self, "allocations") and self.allocations:
            from app.common.enums.transport import TransportAllocationStatus
            return sum(
                1
                for a in self.allocations
                if getattr(a, "status", None) == TransportAllocationStatus.ACTIVE
                and not getattr(a, "is_deleted", False)
            )
        return 0

