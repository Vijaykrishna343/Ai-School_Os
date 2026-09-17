from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
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
    from app.models.teacher.teacher import Teacher
    from app.models.transport.route import TransportRoute


class TransportDriver(CommonModel):
    """
    Represents a school bus/van driver or transit staff member.
    Supports linking to internal staff/teachers or external contractors.
    Enforces strict multi-tenant isolation via school_id.
    """

    __tablename__ = "transport_drivers"

    __table_args__ = (
        Index("ix_transport_drivers_school_id", "school_id"),
        Index("ix_transport_drivers_is_active", "is_active"),
        Index(
            "uq_transport_driver_school_license",
            "school_id",
            "license_number",
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
        String(150),
        nullable=False,
    )

    license_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    license_expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    contact_number: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    emergency_contact: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    staff_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    staff: Mapped[Teacher | None] = orm_relationship(
        "Teacher",
        foreign_keys=[staff_id],
    )

    routes: Mapped[list[TransportRoute]] = orm_relationship(
        "TransportRoute",
        back_populates="driver",
    )
