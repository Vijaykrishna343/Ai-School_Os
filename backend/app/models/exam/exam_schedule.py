from __future__ import annotations

import uuid
from datetime import date, time
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Numeric,
    Time,
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
    from app.models.academic_year.academic_year import AcademicYear
    from app.models.exam.exam import Exam
    from app.models.school.school import School
    from app.models.school_class.school_class import SchoolClass
    from app.models.section.section import Section
    from app.models.subject.subject import Subject


class ExamSchedule(CommonModel):
    """
    Represents an examination schedule for a specific subject, class section, and date/time.
    """

    __tablename__ = "exam_schedules"

    __table_args__ = (
        Index(
            "uq_exam_schedule_active",
            "exam_id",
            "section_id",
            "subject_id",
            "exam_date",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index("ix_exam_schedules_school_id", "school_id"),
        Index("ix_exam_schedules_academic_year_id", "academic_year_id"),
        Index("ix_exam_schedules_class_id", "school_class_id"),
        Index("ix_exam_schedules_section_id", "section_id"),
        Index("ix_exam_schedules_subject_id", "subject_id"),
        Index("ix_exam_schedules_exam_id", "exam_id"),
        Index("ix_exam_schedules_exam_date", "exam_date"),
        Index(
            "ix_exam_schedules_search",
            "school_id",
            "academic_year_id",
            "section_id",
            "exam_date",
        ),
    )

    # ------------------------------------------------------------------
    # Foreign Keys
    # ------------------------------------------------------------------

    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
    )

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

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Schedule Details
    # ------------------------------------------------------------------

    exam_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    maximum_marks: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    passing_marks: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    exam: Mapped["Exam"] = orm_relationship(
        back_populates="schedules",
    )

    school: Mapped["School"] = orm_relationship()

    academic_year: Mapped["AcademicYear"] = orm_relationship()

    school_class: Mapped["SchoolClass"] = orm_relationship()

    section: Mapped["Section"] = orm_relationship()

    subject: Mapped["Subject"] = orm_relationship()
