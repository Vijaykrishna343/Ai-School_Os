"""
HomeworkSubmission model definition.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.identity.models.user import IdentityUser
    from app.models.homework.homework import Homework
    from app.models.school.school import School
    from app.models.student.student import Student


class SubmissionStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    RESUBMITTED = "RESUBMITTED"
    REVIEWED = "REVIEWED"
    GRADED = "GRADED"
    LATE = "LATE"


class HomeworkSubmission(CommonModel):
    """
    Student response submission entity for assigned homework.
    """

    __tablename__ = "homework_submissions"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    homework_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("homeworks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submission_status_enum"),
        nullable=False,
        default=SubmissionStatus.SUBMITTED,
        index=True,
    )

    content_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    grade: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    school: Mapped["School"] = orm_relationship("School")
    homework: Mapped["Homework"] = orm_relationship("Homework", back_populates="submissions")
    student: Mapped["Student"] = orm_relationship("Student")
    reviewed_by: Mapped["IdentityUser | None"] = orm_relationship("IdentityUser")

    __table_args__ = (
        UniqueConstraint("school_id", "homework_id", "student_id", name="uq_school_homework_student_submission"),
        Index("idx_submission_school_homework", "school_id", "homework_id"),
        Index("idx_submission_school_student", "school_id", "student_id"),
    )
