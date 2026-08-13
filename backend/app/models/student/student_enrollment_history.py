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

from app.common.enums import (
    EnrollmentStatus,
    PromotionDecision,
)
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.academic_year.academic_year import AcademicYear
    from app.models.school.school import School
    from app.models.school_class.school_class import SchoolClass
    from app.models.section.section import Section
    from app.models.student.student import Student


class StudentEnrollmentHistory(CommonModel):
    """
    Preserves historical student academic placement across academic years.
    Ensures student class/section history is preserved immutably when students
    are promoted, retained, transferred, or graduated.
    """

    __tablename__ = "student_enrollment_histories"

    __table_args__ = (
        Index(
            "uq_enrollment_history_year_active",
            "school_id",
            "student_id",
            "academic_year_id",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index("ix_enrollment_history_school_id", "school_id"),
        Index("ix_enrollment_history_student_id", "student_id"),
        Index("ix_enrollment_history_academic_year_id", "academic_year_id"),
        Index("ix_enrollment_history_class_id", "school_class_id"),
        Index("ix_enrollment_history_section_id", "section_id"),
        Index("ix_enrollment_history_status", "enrollment_status"),
        Index("ix_enrollment_history_decision", "promotion_decision"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )

    school_class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("school_classes.id", ondelete="RESTRICT"),
        nullable=False,
    )

    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="RESTRICT"),
        nullable=False,
    )

    roll_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    enrollment_status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(
            EnrollmentStatus,
            name="enrollment_status",
            native_enum=True,
            validate_strings=True,
        ),
        default=EnrollmentStatus.ENROLLED,
        nullable=False,
    )

    promotion_decision: Mapped[PromotionDecision] = mapped_column(
        Enum(
            PromotionDecision,
            name="promotion_decision",
            native_enum=True,
            validate_strings=True,
        ),
        default=PromotionDecision.PENDING,
        nullable=False,
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    school: Mapped["School"] = orm_relationship()
    student: Mapped["Student"] = orm_relationship()
    academic_year: Mapped["AcademicYear"] = orm_relationship()
    school_class: Mapped["SchoolClass"] = orm_relationship()
    section: Mapped["Section"] = orm_relationship()
