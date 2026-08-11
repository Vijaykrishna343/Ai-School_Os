from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.exam import AssessmentType
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.grading.evaluation_config import EvaluationConfig


class AssessmentTypeWeightage(CommonModel):
    """
    Represents the percentage weightage of an AssessmentType within an EvaluationConfig.
    """

    __tablename__ = "assessment_type_weightages"

    __table_args__ = (
        CheckConstraint(
            "weightage_percentage >= 0 AND weightage_percentage <= 100",
            name="ck_assessment_type_weightage_pct_bounds",
        ),
        Index(
            "uq_assessment_type_weightage_active",
            "evaluation_config_id",
            "assessment_type",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index(
            "ix_assessment_type_weightages_config_id",
            "evaluation_config_id",
        ),
    )

    evaluation_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluation_configs.id", ondelete="CASCADE"),
        nullable=False,
    )

    assessment_type: Mapped[AssessmentType] = mapped_column(
        Enum(
            AssessmentType,
            name="assessment_type",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    weightage_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    evaluation_config: Mapped["EvaluationConfig"] = orm_relationship(
        back_populates="weightages",
    )
