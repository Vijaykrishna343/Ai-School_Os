from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
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

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.grading.grade_scale_entry import GradeScaleEntry
    from app.models.school.school import School


class GradeScale(CommonModel):
    """
    Represents a school's grading system / scale (e.g. CBSE 10-Point Scale).
    """

    __tablename__ = "grade_scales"

    __table_args__ = (
        Index(
            "uq_grade_scale_active_name",
            "school_id",
            "name",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index(
            "uq_grade_scale_active_default",
            "school_id",
            unique=True,
            postgresql_where=text("is_default = true AND is_deleted = false"),
            sqlite_where=text("is_default = 1 AND is_deleted = 0"),
        ),
        Index("ix_grade_scales_school_id", "school_id"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
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

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    school: Mapped["School"] = orm_relationship()

    entries: Mapped[list["GradeScaleEntry"]] = orm_relationship(
        back_populates="grade_scale",
        cascade="all, delete-orphan",
        order_by="GradeScaleEntry.min_percentage.desc()",
    )
