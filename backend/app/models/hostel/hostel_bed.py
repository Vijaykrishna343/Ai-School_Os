from __future__ import annotations

import uuid
from sqlalchemy import String, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.common_model import CommonModel


class HostelBed(CommonModel):
    """
    Hostel Bed model. Statuses: AVAILABLE, OCCUPIED, MAINTENANCE, INACTIVE.
    """
    __tablename__ = "hostel_beds"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hostel_rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bed_number: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="AVAILABLE") # AVAILABLE, OCCUPIED, MAINTENANCE, INACTIVE
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    room: Mapped[HostelRoom] = relationship("HostelRoom", back_populates="beds")

    __table_args__ = (
        Index("idx_hostel_bed_room_number", "room_id", "bed_number", unique=True),
    )
