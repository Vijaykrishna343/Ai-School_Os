from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Enum,
    ForeignKey,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.timetable import DayOfWeek
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.subject.subject import Subject
    from app.models.teacher.teacher import Teacher
    from app.models.timetable.classroom import Classroom
    from app.models.timetable.period_slot import PeriodSlot
    from app.models.timetable.timetable import Timetable


class TimetableEntry(CommonModel):
    """
    Represents an individual entry in a timetable matrix cell
    mapping (day_of_week, period_slot, subject, teacher, classroom).
    """

    __tablename__ = "timetable_entries"

    __table_args__ = (
        Index(
            "uq_timetable_entry_slot",
            "timetable_id",
            "day_of_week",
            "period_slot_id",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index("ix_timetable_entries_teacher_slot", "teacher_id", "day_of_week", "period_slot_id"),
        Index("ix_timetable_entries_room_slot", "classroom_id", "day_of_week", "period_slot_id"),
        Index("ix_timetable_entries_timetable_id", "timetable_id"),
        Index("ix_timetable_entries_subject_id", "subject_id"),
        Index("ix_timetable_entries_period_slot_id", "period_slot_id"),
    )

    # ------------------------------------------------------------------
    # Foreign Keys
    # ------------------------------------------------------------------

    timetable_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("timetables.id", ondelete="CASCADE"),
        nullable=False,
    )

    period_slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("period_slots.id", ondelete="CASCADE"),
        nullable=False,
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
    )

    classroom_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Attributes
    # ------------------------------------------------------------------

    day_of_week: Mapped[DayOfWeek] = mapped_column(
        Enum(DayOfWeek, name="day_of_week", create_constraint=False),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    timetable: Mapped["Timetable"] = orm_relationship(back_populates="entries")
    period_slot: Mapped["PeriodSlot"] = orm_relationship()
    subject: Mapped["Subject"] = orm_relationship()
    teacher: Mapped["Teacher"] = orm_relationship()
    classroom: Mapped["Classroom | None"] = orm_relationship()
