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

from app.common.enums import AttendanceStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.identity.models.user import IdentityUser
    from app.models.academic_year.academic_year import AcademicYear
    from app.models.school.school import School
    from app.models.school_class.school_class import SchoolClass
    from app.models.section.section import Section
    from app.models.student.student import Student


class Attendance(CommonModel):
    """
    Represents a daily attendance record for a student.

    Every attendance record belongs to:
    - School (multi-tenant boundary)
    - Academic Year
    - Class
    - Section
    - Student
    """

    __tablename__ = "attendances"

    __table_args__ = (
        Index(
            "uq_student_daily_attendance_active",
            "school_id",
            "academic_year_id",
            "section_id",
            "student_id",
            "attendance_date",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index("ix_attendances_school_id", "school_id"),
        Index("ix_attendances_academic_year_id", "academic_year_id"),
        Index("ix_attendances_class_id", "school_class_id"),
        Index("ix_attendances_section_id", "section_id"),
        Index("ix_attendances_student_id", "student_id"),
        Index("ix_attendances_date", "attendance_date"),
        Index("ix_attendances_status", "status"),
        Index("ix_attendances_section_date", "school_id", "section_id", "attendance_date"),
    )

    # ------------------------------------------------------------------
    # Foreign Keys
    # ------------------------------------------------------------------

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )

    school_class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("school_classes.id", ondelete="CASCADE"),
        nullable=False,
    )

    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )

    recorded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Attendance Data
    # ------------------------------------------------------------------

    attendance_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(
            AttendanceStatus,
            name="attendance_status",
            native_enum=True,
            validate_strings=True,
        ),
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

    academic_year: Mapped["AcademicYear"] = orm_relationship()

    school_class: Mapped["SchoolClass"] = orm_relationship()

    section: Mapped["Section"] = orm_relationship()

    student: Mapped["Student"] = orm_relationship()

    recorded_by_user: Mapped["IdentityUser | None"] = orm_relationship()
