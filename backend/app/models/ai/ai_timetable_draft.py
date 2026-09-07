from __future__ import annotations

import uuid
from typing import Any, TYPE_CHECKING
from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    Index,
    Text,
    JSON,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.school.school import School
    from app.models.academic_year.academic_year import AcademicYear
    from app.identity.models.user import IdentityUser
    from app.models.school_class.school_class import SchoolClass
    from app.models.section.section import Section
    from app.models.subject.subject import Subject
    from app.models.teacher.teacher import Teacher
    from app.models.timetable.classroom import Classroom
    from app.models.timetable.period_slot import PeriodSlot


class AITimetableDraft(CommonModel):
    """
    Represents an AI-generated timetable optimization draft.
    Lifecycle: DRAFT -> SOLVING -> SOLVED (or FAILED) -> APPROVED -> PUBLISHED.
    """

    __tablename__ = "ai_timetable_drafts"

    __table_args__ = (
        Index("ix_ai_timetable_drafts_school_id", "school_id"),
        Index("ix_ai_timetable_drafts_academic_year_id", "academic_year_id"),
        Index("ix_ai_timetable_drafts_status", "status"),
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

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="AI Timetable Draft",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="DRAFT",  # DRAFT, SOLVING, SOLVED, FAILED, APPROVED, PUBLISHED
    )

    solver_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="UNKNOWN",  # UNKNOWN, FEASIBLE, OPTIMAL, INFEASIBLE, MODEL_INVALID
    )

    objective_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    solver_duration_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    constraint_summary: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    validation_report: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="CASCADE"),
        nullable=False,
    )

    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    published_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    approved_at: Mapped[Any | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    published_at: Mapped[Any | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    school: Mapped["School"] = orm_relationship()
    academic_year: Mapped["AcademicYear"] = orm_relationship()
    created_by: Mapped["IdentityUser"] = orm_relationship(foreign_keys=[created_by_id])
    approved_by: Mapped["IdentityUser | None"] = orm_relationship(foreign_keys=[approved_by_id])
    published_by: Mapped["IdentityUser | None"] = orm_relationship(foreign_keys=[published_by_id])

    entries: Mapped[list["AITimetableDraftEntry"]] = orm_relationship(
        back_populates="draft",
        cascade="all, delete-orphan",
    )


class AITimetableDraftEntry(CommonModel):
    """
    Represents an individual scheduled period slot entry within an AI timetable draft.
    """

    __tablename__ = "ai_timetable_draft_entries"

    __table_args__ = (
        Index("ix_ai_timetable_draft_entries_draft_id", "draft_id"),
        Index("ix_ai_timetable_draft_entries_teacher_id", "teacher_id"),
        Index("ix_ai_timetable_draft_entries_section_id", "section_id"),
    )

    draft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_timetable_drafts.id", ondelete="CASCADE"),
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

    period_slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("period_slots.id", ondelete="CASCADE"),
        nullable=False,
    )

    day_of_week: Mapped[str] = mapped_column(
        String(20),
        nullable=False,  # MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY
    )

    # Relationships
    draft: Mapped["AITimetableDraft"] = orm_relationship(back_populates="entries")
    school_class: Mapped["SchoolClass"] = orm_relationship()
    section: Mapped["Section"] = orm_relationship()
    subject: Mapped["Subject"] = orm_relationship()
    teacher: Mapped["Teacher"] = orm_relationship()
    classroom: Mapped["Classroom | None"] = orm_relationship()
    period_slot: Mapped["PeriodSlot"] = orm_relationship()
