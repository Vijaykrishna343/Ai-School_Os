from __future__ import annotations

import uuid
from sqlalchemy import String, Boolean, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.common_model import CommonModel


class HostelBuilding(CommonModel):
    """
    Hostel Building / Block model.
    """
    __tablename__ = "hostel_buildings"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    gender_designation: Mapped[str] = mapped_column(String(20), nullable=False, default="BOYS") # BOYS, GIRLS, COED
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    rooms: Mapped[list[HostelRoom]] = relationship("HostelRoom", back_populates="building", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_hostel_building_school_code", "school_id", "code", unique=True),
    )
