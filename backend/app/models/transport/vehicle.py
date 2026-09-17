from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
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

from app.common.enums.transport import FuelType, VehicleStatus, VehicleType
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.transport.route import TransportRoute


class Vehicle(CommonModel):
    """
    Represents a school-owned or contracted transport vehicle (bus, van, minibus).
    Enforces strict multi-tenant isolation via school_id.
    """

    __tablename__ = "transport_vehicles"

    __table_args__ = (
        CheckConstraint("seating_capacity > 0", name="ck_transport_vehicle_capacity_positive"),
        Index("ix_transport_vehicles_school_id", "school_id"),
        Index("ix_transport_vehicles_status", "status"),
        Index(
            "uq_transport_vehicle_school_reg",
            "school_id",
            "registration_number",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index(
            "uq_transport_vehicle_school_code",
            "school_id",
            "vehicle_code",
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

    registration_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    vehicle_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    vehicle_type: Mapped[VehicleType] = mapped_column(
        Enum(VehicleType, name="vehicletype", native_enum=False),
        nullable=False,
        default=VehicleType.BUS,
    )

    seating_capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    fuel_type: Mapped[FuelType] = mapped_column(
        Enum(FuelType, name="fueltype", native_enum=False),
        nullable=False,
        default=FuelType.DIESEL,
    )

    insurance_expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    fitness_expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    gps_device_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    status: Mapped[VehicleStatus] = mapped_column(
        Enum(VehicleStatus, name="vehiclestatus", native_enum=False),
        nullable=False,
        default=VehicleStatus.ACTIVE,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    routes: Mapped[list[TransportRoute]] = orm_relationship(
        "TransportRoute",
        back_populates="vehicle",
    )
