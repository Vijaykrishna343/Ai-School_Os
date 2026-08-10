from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Numeric, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.exam.exam_schedule import ExamSchedule
    from app.models.student.student import Student


class StudentExamResult(CommonModel):
    """
    Represents a student's result for a specific exam schedule.

    A student can have only one active result for a given
    exam schedule.
    """

    __tablename__ = "student_exam_results"

    __table_args__ = (
        Index(
            "uq_student_exam_result_active",
            "exam_schedule_id",
            "student_id",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index(
            "ix_student_exam_results_exam_schedule_id",
            "exam_schedule_id",
        ),
        Index(
            "ix_student_exam_results_student_id",
            "student_id",
        ),
    )

    # ------------------------------------------------------------------
    # Foreign Keys
    # ------------------------------------------------------------------

    exam_schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "exam_schedules.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "students.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Result Data
    # ------------------------------------------------------------------

    marks_obtained: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    remarks: Mapped[str | None] = mapped_column(
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    exam_schedule: Mapped["ExamSchedule"] = orm_relationship()

    student: Mapped["Student"] = orm_relationship()