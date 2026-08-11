from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.report_card import ReportCardStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.academic_term.academic_term import AcademicTerm
    from app.models.academic_year.academic_year import AcademicYear
    from app.models.grading.evaluation_config import EvaluationConfig
    from app.models.grading.grade_scale import GradeScale
    from app.models.grading.report_card_item_snapshot import ReportCardItemSnapshot
    from app.models.school.school import School
    from app.models.school_class.school_class import SchoolClass
    from app.models.section.section import Section
    from app.models.student.student import Student


class ReportCard(CommonModel):
    """
    Represents a student's academic report card for a term or academic year.
    """

    __tablename__ = "report_cards"

    __table_args__ = (
        Index(
            "uq_report_card_student_term_active",
            "school_id",
            "academic_year_id",
            "academic_term_id",
            "student_id",
            unique=True,
            postgresql_where=text("is_deleted = false AND academic_term_id IS NOT NULL"),
            sqlite_where=text("is_deleted = 0 AND academic_term_id IS NOT NULL"),
        ),
        Index(
            "uq_report_card_student_year_active",
            "school_id",
            "academic_year_id",
            "student_id",
            unique=True,
            postgresql_where=text("is_deleted = false AND academic_term_id IS NULL"),
            sqlite_where=text("is_deleted = 0 AND academic_term_id IS NULL"),
        ),
        Index("ix_report_cards_school_id", "school_id"),
        Index("ix_report_cards_academic_year_id", "academic_year_id"),
        Index("ix_report_cards_academic_term_id", "academic_term_id"),
        Index("ix_report_cards_student_id", "student_id"),
        Index("ix_report_cards_section_id", "section_id"),
        Index("ix_report_cards_status", "status"),
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

    academic_term_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_terms.id", ondelete="SET NULL"),
        nullable=True,
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
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

    grade_scale_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grade_scales.id", ondelete="RESTRICT"),
        nullable=False,
    )

    evaluation_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluation_configs.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Report Card Details & Aggregates
    # ------------------------------------------------------------------

    status: Mapped[ReportCardStatus] = mapped_column(
        Enum(
            ReportCardStatus,
            name="report_card_status",
            native_enum=True,
            validate_strings=True,
        ),
        default=ReportCardStatus.DRAFT,
        nullable=False,
    )

    total_max_marks: Mapped[Decimal] = mapped_column(
        Numeric(7, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    total_obtained_marks: Mapped[Decimal] = mapped_column(
        Numeric(7, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    overall_grade: Mapped[str] = mapped_column(
        String(10),
        default="N/A",
        nullable=False,
    )

    overall_grade_point: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    gpa: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2),
        nullable=True,
    )

    is_passed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Attendance Summary
    # ------------------------------------------------------------------

    total_working_days: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    present_days: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    attendance_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Remarks & Audit Metadata
    # ------------------------------------------------------------------

    teacher_remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    principal_remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    finalized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finalized_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    published_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    school: Mapped["School"] = orm_relationship()

    academic_year: Mapped["AcademicYear"] = orm_relationship()

    academic_term: Mapped["AcademicTerm | None"] = orm_relationship()

    student: Mapped["Student"] = orm_relationship()

    school_class: Mapped["SchoolClass"] = orm_relationship()

    section: Mapped["Section"] = orm_relationship()

    grade_scale: Mapped["GradeScale"] = orm_relationship()

    evaluation_config: Mapped["EvaluationConfig"] = orm_relationship()

    items: Mapped[list["ReportCardItemSnapshot"]] = orm_relationship(
        back_populates="report_card",
        cascade="all, delete-orphan",
    )
