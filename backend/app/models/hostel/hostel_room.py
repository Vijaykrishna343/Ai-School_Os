from __future__ import annotations

import uuid
from sqlalchemy import String, Boolean, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.common_model import CommonModel


class HostelRoom(CommonModel):
    """
    Hostel Room model.
    """
    __tablename__ = "hostel_rooms"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hostel_buildings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    room_number: Mapped[str] = mapped_column(String(20), nullable=False)
    floor: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    room_type: Mapped[str] = mapped_column(String(50), nullable=False, default="STANDARD") # STANDARD, DELUXE, DORMITORY, ISOLATION
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    building: Mapped[HostelBuilding] = relationship("HostelBuilding", back_populates="rooms")
    beds: Mapped[list[HostelBed]] = relationship("HostelBed", back_populates="room", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_hostel_room_bldg_number", "building_id", "room_number", unique=True),
    )
