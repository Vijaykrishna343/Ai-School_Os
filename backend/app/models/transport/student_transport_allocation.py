from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
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

from app.common.enums.transport import TransportAllocationStatus, TransportAllocationType
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.academic_year.academic_year import AcademicYear
    from app.models.student.student import Student
    from app.models.transport.route import TransportRoute
    from app.models.transport.stop import RouteStop


class StudentTransportAllocation(CommonModel):
    """
    Represents a student's active or historic bus route seat allocation.
    Maintains link to route, pickup/drop stops, and academic year.
    Enforces strict multi-tenant isolation and single-active allocation per academic year.
    """

    __tablename__ = "student_transport_allocations"

    __table_args__ = (
        Index("ix_student_transport_alloc_school_id", "school_id"),
        Index("ix_student_transport_alloc_student_id", "student_id"),
        Index("ix_student_transport_alloc_route_id", "route_id"),
        Index("ix_student_transport_alloc_academic_year_id", "academic_year_id"),
        Index("ix_student_transport_alloc_status", "status"),
        Index(
            "uq_active_student_transport_alloc",
            "school_id",
            "student_id",
            "academic_year_id",
            unique=True,
            postgresql_where=text("is_deleted = false AND status = 'ACTIVE'"),
            sqlite_where=text("is_deleted = 0 AND status = 'ACTIVE'"),
        ),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )

    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transport_routes.id", ondelete="CASCADE"),
        nullable=False,
    )

    pickup_stop_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transport_route_stops.id", ondelete="SET NULL"),
        nullable=True,
    )

    drop_stop_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transport_route_stops.id", ondelete="SET NULL"),
        nullable=True,
    )

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )

    allocation_type: Mapped[TransportAllocationType] = mapped_column(
        Enum(TransportAllocationType, name="transportallocationtype", native_enum=False),
        nullable=False,
        default=TransportAllocationType.TWO_WAY,
    )

    status: Mapped[TransportAllocationStatus] = mapped_column(
        Enum(TransportAllocationStatus, name="transportallocationstatus", native_enum=False),
        nullable=False,
        default=TransportAllocationStatus.ACTIVE,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    student: Mapped[Student] = orm_relationship(
        "Student",
        foreign_keys=[student_id],
    )

    route: Mapped[TransportRoute] = orm_relationship(
        "TransportRoute",
        back_populates="allocations",
        foreign_keys=[route_id],
    )

    pickup_stop: Mapped[RouteStop | None] = orm_relationship(
        "RouteStop",
        foreign_keys=[pickup_stop_id],
    )

    drop_stop: Mapped[RouteStop | None] = orm_relationship(
        "RouteStop",
        foreign_keys=[drop_stop_id],
    )

    academic_year: Mapped[AcademicYear] = orm_relationship(
        "AcademicYear",
        foreign_keys=[academic_year_id],
    )

    @property
    def student_name(self) -> str | None:
        if hasattr(self, "student") and self.student:
            first = getattr(self.student, "first_name", "") or ""
            last = getattr(self.student, "last_name", "") or ""
            name = f"{first} {last}".strip()
            return name if name else None
        return None

    @property
    def admission_number(self) -> str | None:
        if hasattr(self, "student") and self.student:
            return getattr(self.student, "admission_number", None)
        return None

    @property
    def route_code(self) -> str | None:
        if hasattr(self, "route") and self.route:
            return getattr(self.route, "route_code", None)
        return None

    @property
    def route_name(self) -> str | None:
        if hasattr(self, "route") and self.route:
            return getattr(self.route, "route_name", None)
        return None

    @property
    def pickup_stop_name(self) -> str | None:
        if hasattr(self, "pickup_stop") and self.pickup_stop:
            return getattr(self.pickup_stop, "stop_name", None)
        return None

    @property
    def drop_stop_name(self) -> str | None:
        if hasattr(self, "drop_stop") and self.drop_stop:
            return getattr(self.drop_stop, "stop_name", None)
        return None

