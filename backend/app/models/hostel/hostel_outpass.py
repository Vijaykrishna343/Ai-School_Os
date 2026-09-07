from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.common_model import CommonModel


class HostelOutpass(CommonModel):
    """
    Hostel Outpass / Leave Request model.
    Statuses: PENDING, APPROVED, REJECTED, CHECKED_OUT, RETURNED, EXPIRED, CANCELLED.
    """
    __tablename__ = "hostel_outpasses"

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
    requested_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_return_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_checkout_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_return_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    emergency_contact: Mapped[str | None] = mapped_column(String(50), nullable=True)
    remarks: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")

    __table_args__ = (
        Index("idx_hostel_outpass_student", "school_id", "student_id"),
        Index("idx_hostel_outpass_status", "school_id", "status"),
    )
