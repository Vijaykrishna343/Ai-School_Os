from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
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

from app.common.enums.timetable import RoomType
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.school.school import School


class Classroom(CommonModel):
    """
    Represents a physical room or facility in a school
    (e.g. Room 101, Science Lab 2, Main Auditorium).
    """

    __tablename__ = "classrooms"

    __table_args__ = (
        Index(
            "uq_classroom_room_number",
            "school_id",
            "room_number",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index("ix_classrooms_school_id", "school_id"),
    )

    # ------------------------------------------------------------------
    # Foreign Key
    # ------------------------------------------------------------------

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Classroom Details
    # ------------------------------------------------------------------

    room_number: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    building_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=40,
    )

    room_type: Mapped[RoomType] = mapped_column(
        Enum(RoomType, name="room_type", create_constraint=False),
        nullable=False,
        default=RoomType.CLASSROOM,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    school: Mapped["School"] = orm_relationship()
