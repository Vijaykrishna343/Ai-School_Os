"""
Homework model definition.
"""
from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.homework.homework_submission import HomeworkSubmission
    from app.models.school.school import School
    from app.models.school_class.school_class import SchoolClass
    from app.models.section.section import Section
    from app.models.subject.subject import Subject
    from app.models.teacher.teacher import Teacher


class HomeworkStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"


class Homework(CommonModel):
    """
    Homework entity created by teachers for specific classes/sections and subjects.
    """

    __tablename__ = "homeworks"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    school_class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("school_classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    section_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    assigned_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )

    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    status: Mapped[HomeworkStatus] = mapped_column(
        Enum(HomeworkStatus, name="homework_status_enum"),
        nullable=False,
        default=HomeworkStatus.DRAFT,
        index=True,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    school: Mapped["School"] = orm_relationship("School")
    teacher: Mapped["Teacher"] = orm_relationship("Teacher")
    school_class: Mapped["SchoolClass"] = orm_relationship("SchoolClass")
    section: Mapped["Section | None"] = orm_relationship("Section")
    subject: Mapped["Subject"] = orm_relationship("Subject")
    submissions: Mapped[List["HomeworkSubmission"]] = orm_relationship(
        "HomeworkSubmission",
        back_populates="homework",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_homework_school_class_section", "school_id", "school_class_id", "section_id"),
        Index("idx_homework_school_status_due", "school_id", "status", "due_date"),
        Index("idx_homework_school_teacher", "school_id", "teacher_id"),
    )
