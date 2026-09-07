"""
AI Student Risk Assessment database model definition for Phase 12.4.
Provides explainable academic risk scoring and data sufficiency metrics.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.identity.models.user import IdentityUser
    from app.models.academic_year.academic_year import AcademicYear
    from app.models.school.school import School
    from app.models.section.section import Section
    from app.models.student.student import Student


class AIStudentRiskAssessment(CommonModel):
    """
    Represents an explainable student academic risk assessment record.

    Risk scoring is 100% derived from educational signals:
    - Attendance history & trend
    - Exam performance & trend
    - Failed subjects count
    - Homework submission completion rate

    Financial data is strictly EXCLUDED from academic risk scoring.
    """

    __tablename__ = "ai_student_risk_assessments"

    # Multi-tenant boundary
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Risk Metrics & Classification
    risk_level: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="INSUFFICIENT_DATA",
        index=True,
    )  # LOW, MEDIUM, HIGH, CRITICAL, INSUFFICIENT_DATA

    risk_score: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2),
        nullable=True,
    )  # 0.00 to 1.00 (Nullable if INSUFFICIENT_DATA)

    confidence: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        default=Decimal("0.00"),
    )  # 0.00 to 1.00

    scoring_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="deterministic-v1",
    )

    # Educational Factors & Deltas
    attendance_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    attendance_trend_delta: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    exam_average_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    exam_trend_delta: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    homework_submission_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    failed_subjects_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Data Sufficiency & Metadata
    data_sufficiency_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="INSUFFICIENT",
    )  # FULL, PARTIAL, INSUFFICIENT

    sample_counts: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )  # {attendance_records: int, exam_results: int, homework_submissions: int}

    risk_factors: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=list,
    )  # [{factor: str, impact: str, value: str, details: str}]

    recommended_interventions: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=list,
    )  # Advisory recommendations for educators

    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    school: Mapped["School"] = orm_relationship("School")
    academic_year: Mapped["AcademicYear"] = orm_relationship("AcademicYear")
    student: Mapped["Student"] = orm_relationship("Student")
    section: Mapped["Section"] = orm_relationship("Section")

    __table_args__ = (
        Index("idx_ai_risk_school_student", "school_id", "student_id"),
        Index("idx_ai_risk_school_section", "school_id", "section_id"),
        Index("idx_ai_risk_school_year", "school_id", "academic_year_id"),
        Index("idx_ai_risk_student_assessed", "student_id", "assessed_at"),
    )
