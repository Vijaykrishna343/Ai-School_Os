from __future__ import annotations

import uuid
from datetime import date
from sqlalchemy import String, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.common_model import CommonModel


class HostelAllocation(CommonModel):
    """
    Student Hostel Allocation model. Statuses: ACTIVE, RELEASED, TRANSFERRED.
    """
    __tablename__ = "hostel_allocations"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hostel_buildings.id", ondelete="CASCADE"),
        nullable=False,
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hostel_rooms.id", ondelete="CASCADE"),
        nullable=False,
    )
    bed_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hostel_beds.id", ondelete="CASCADE"),
        nullable=False,
    )
    allocated_at: Mapped[date] = mapped_column(Date, nullable=False)
    released_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE") # ACTIVE, RELEASED, TRANSFERRED
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("idx_hostel_alloc_student", "school_id", "student_id"),
        Index("idx_hostel_alloc_bed", "bed_id"),
    )
