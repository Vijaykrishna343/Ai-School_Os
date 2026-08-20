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
    Time,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums import AttendanceStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.school.school import School
    from app.models.teacher.teacher import Teacher


class TeacherAttendance(CommonModel):
    """
    Represents a daily attendance record for a teacher/staff member.

    Every teacher attendance record belongs to:
    - School (multi-tenant boundary)
    - Teacher
    """

    __tablename__ = "teacher_attendances"

    __table_args__ = (
        Index(
            "uq_teacher_daily_attendance_active",
            "school_id",
            "teacher_id",
            "attendance_date",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index("ix_teacher_attendances_school_id", "school_id"),
        Index("ix_teacher_attendances_teacher_id", "teacher_id"),
        Index("ix_teacher_attendances_date", "attendance_date"),
        Index("ix_teacher_attendances_status", "status"),
    )

    # ------------------------------------------------------------------
    # Foreign Keys
    # ------------------------------------------------------------------

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------

    attendance_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus),
        nullable=False,
        default=AttendanceStatus.PRESENT,
    )

    check_in_time: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    check_out_time: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    school: Mapped[School] = orm_relationship(
        "School",
        foreign_keys=[school_id],
    )

    teacher: Mapped[Teacher] = orm_relationship(
        "Teacher",
        foreign_keys=[teacher_id],
    )
