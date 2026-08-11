from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Index,
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

from app.common.enums.report_card import (
    CalculationMode,
    RetestPolicy,
    RoundingMode,
)
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.academic_year.academic_year import AcademicYear
    from app.models.grading.assessment_type_weightage import AssessmentTypeWeightage
    from app.models.school.school import School


class EvaluationConfig(CommonModel):
    """
    Represents a school's academic evaluation and grading scheme for an AcademicYear.
    """

    __tablename__ = "evaluation_configs"

    __table_args__ = (
        Index(
            "uq_evaluation_config_active_name",
            "school_id",
            "academic_year_id",
            "name",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index(
            "uq_evaluation_config_active_default",
            "school_id",
            "academic_year_id",
            unique=True,
            postgresql_where=text("is_default = true AND is_deleted = false"),
            sqlite_where=text("is_default = 1 AND is_deleted = 0"),
        ),
        Index("ix_evaluation_configs_school_id", "school_id"),
        Index("ix_evaluation_configs_academic_year_id", "academic_year_id"),
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
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    calculation_mode: Mapped[CalculationMode] = mapped_column(
        Enum(
            CalculationMode,
            name="calculation_mode",
            native_enum=True,
            validate_strings=True,
        ),
        default=CalculationMode.SIMPLE_TOTAL,
        nullable=False,
    )

    retest_policy: Mapped[RetestPolicy] = mapped_column(
        Enum(
            RetestPolicy,
            name="retest_policy",
            native_enum=True,
            validate_strings=True,
        ),
        default=RetestPolicy.REPLACE_ORIGINAL,
        nullable=False,
    )

    rounding_mode: Mapped[RoundingMode] = mapped_column(
        Enum(
            RoundingMode,
            name="rounding_mode",
            native_enum=True,
            validate_strings=True,
        ),
        default=RoundingMode.ROUND_HALF_UP,
        nullable=False,
    )

    gpa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    school: Mapped["School"] = orm_relationship()

    academic_year: Mapped["AcademicYear"] = orm_relationship()

    weightages: Mapped[list["AssessmentTypeWeightage"]] = orm_relationship(
        back_populates="evaluation_config",
        cascade="all, delete-orphan",
    )
