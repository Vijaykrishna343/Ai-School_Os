from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
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
    from app.models.school.school import School
    from app.models.teacher.teacher import Teacher
    from app.models.timetable.timetable_entry import TimetableEntry


class TeacherSubstitution(CommonModel):
    """
    Represents a daily teacher substitution for a specific timetable entry on a specific date.
    Maintains historical integrity without altering the master TimetableEntry.teacher_id.
    """

    __tablename__ = "teacher_substitutions"

    __table_args__ = (
        Index(
            "uq_teacher_substitution_active_slot",
            "timetable_entry_id",
            "substitution_date",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index("ix_teacher_substitutions_school_id", "school_id"),
        Index("ix_teacher_substitutions_entry_id", "timetable_entry_id"),
        Index("ix_teacher_substitutions_substitute_date", "substitute_teacher_id", "substitution_date"),
        Index("ix_teacher_substitutions_original_date", "original_teacher_id", "substitution_date"),
    )

    # ------------------------------------------------------------------
    # Foreign Keys
    # ------------------------------------------------------------------

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    timetable_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("timetable_entries.id", ondelete="CASCADE"),
        nullable=False,
    )

    original_teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
    )

    substitute_teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Attributes
    # ------------------------------------------------------------------

    substitution_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    school: Mapped["School"] = orm_relationship()
    timetable_entry: Mapped["TimetableEntry"] = orm_relationship()
    original_teacher: Mapped["Teacher"] = orm_relationship(
        foreign_keys=[original_teacher_id]
    )
    substitute_teacher: Mapped["Teacher"] = orm_relationship(
        foreign_keys=[substitute_teacher_id]
    )
