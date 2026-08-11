from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums import AcademicYearStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.academic_term.academic_term import AcademicTerm
    from app.models.school.school import School
    from app.models.student.student import Student


class AcademicYear(CommonModel):
    """
    Represents an academic year for a school.

    Example:
        2026-2027

    Each school can have multiple academic years,
    but only one should typically be marked as current.
    """

    __tablename__ = "academic_years"

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "name",
            name="uq_academic_year_school_name",
        ),
        Index(
            "ix_academic_year_school_id",
            "school_id",
        ),
        Index(
            "ix_academic_year_status",
            "status",
        ),
        Index(
            "ix_academic_year_current",
            "is_current",
        ),
        Index(
            "ix_academic_year_start_date",
            "start_date",
        ),
    )

    # ------------------------------------------------------------------
    # School
    # ------------------------------------------------------------------

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "schools.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Academic Year Details
    # ------------------------------------------------------------------

    name: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    status: Mapped[AcademicYearStatus] = mapped_column(
        Enum(
            AcademicYearStatus,
            name="academic_year_status",
            native_enum=True,
            validate_strings=True,
        ),
        default=AcademicYearStatus.UPCOMING,
        nullable=False,
    )

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    school: Mapped["School"] = orm_relationship(
        back_populates="academic_years",
    )

    students: Mapped[list["Student"]] = orm_relationship(
        back_populates="academic_year",
    )

    terms: Mapped[list["AcademicTerm"]] = orm_relationship(
        back_populates="academic_year",
        cascade="all, delete-orphan",
        order_by="AcademicTerm.display_order",
    )