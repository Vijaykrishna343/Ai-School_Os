from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
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
    from app.models.grading.grade_scale import GradeScale


class GradeScaleEntry(CommonModel):
    """
    Represents an individual grade band inside a GradeScale.
    """

    __tablename__ = "grade_scale_entries"

    __table_args__ = (
        CheckConstraint(
            "min_percentage >= 0",
            name="ck_grade_scale_entry_min_pct_non_negative",
        ),
        CheckConstraint(
            "max_percentage <= 100",
            name="ck_grade_scale_entry_max_pct_bounds",
        ),
        CheckConstraint(
            "min_percentage <= max_percentage",
            name="ck_grade_scale_entry_min_le_max",
        ),
        CheckConstraint(
            "grade_point >= 0",
            name="ck_grade_scale_entry_grade_point_non_negative",
        ),
        Index(
            "uq_grade_scale_entry_active_code",
            "grade_scale_id",
            "grade_code",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index("ix_grade_scale_entries_grade_scale_id", "grade_scale_id"),
    )

    grade_scale_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grade_scales.id", ondelete="CASCADE"),
        nullable=False,
    )

    grade_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    min_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    max_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    grade_point: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    is_pass: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    grade_scale: Mapped["GradeScale"] = orm_relationship(
        back_populates="entries",
    )
