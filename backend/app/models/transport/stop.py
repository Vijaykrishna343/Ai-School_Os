from __future__ import annotations

from decimal import Decimal
import uuid
from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
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
    from app.models.transport.route import TransportRoute


class RouteStop(CommonModel):
    """
    Represents a designated pickup/drop point along a transport route.
    Maintains ordered stop sequences and stop-specific transit fee rates.
    Enforces strict multi-tenant isolation via school_id.
    """

    __tablename__ = "transport_route_stops"

    __table_args__ = (
        CheckConstraint("sequence_order > 0", name="ck_transport_stop_sequence_positive"),
        CheckConstraint("pickup_fee_amount >= 0", name="ck_transport_stop_fee_non_negative"),
        Index("ix_transport_route_stops_school_id", "school_id"),
        Index("ix_transport_route_stops_route_id", "route_id"),
        Index("ix_transport_route_stops_sequence", "route_id", "sequence_order"),
        Index(
            "uq_transport_stop_route_sequence",
            "route_id",
            "sequence_order",
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

    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transport_routes.id", ondelete="CASCADE"),
        nullable=False,
    )

    stop_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    stop_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    sequence_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    morning_pickup_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    afternoon_drop_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    landmark: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pickup_fee_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    route: Mapped[TransportRoute] = orm_relationship(
        "TransportRoute",
        back_populates="stops",
    )
