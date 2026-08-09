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

from app.common.enums.exam import ExamStatus, ExamType
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.academic_year.academic_year import AcademicYear
    from app.models.exam.exam_schedule import ExamSchedule
    from app.models.school.school import School


class Exam(CommonModel):
    """
    Represents an examination within a school and academic year.
    """

    __tablename__ = "exams"

    __table_args__ = (
        Index(
            "uq_exam_active_name",
            "school_id",
            "academic_year_id",
            "name",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index("ix_exams_school_id", "school_id"),
        Index("ix_exams_academic_year_id", "academic_year_id"),
        Index("ix_exams_status", "status"),
        Index("ix_exams_start_date", "start_date"),
        Index("ix_exams_end_date", "end_date"),
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

    # ------------------------------------------------------------------
    # Exam Details
    # ------------------------------------------------------------------

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    exam_type: Mapped[ExamType] = mapped_column(
        Enum(
            ExamType,
            name="exam_type",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[ExamStatus] = mapped_column(
        Enum(
            ExamStatus,
            name="exam_status",
            native_enum=True,
            validate_strings=True,
        ),
        default=ExamStatus.DRAFT,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    school: Mapped["School"] = orm_relationship()

    academic_year: Mapped["AcademicYear"] = orm_relationship()

    schedules: Mapped[list["ExamSchedule"]] = orm_relationship(
        back_populates="exam",
        cascade="all, delete-orphan",
    )
