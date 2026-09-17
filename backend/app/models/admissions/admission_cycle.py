from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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

from app.common.enums.admissions import AdmissionCycleStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.academic_year.academic_year import AcademicYear
    from app.models.admissions.admission_application import AdmissionApplication
    from app.models.admissions.applicant import Applicant
    from app.models.school.school import School


class AdmissionCycle(CommonModel):
    """
    Represents an admission campaign or intake cycle for an academic year.
    Strictly tenant-scoped to a school and mapped to an Academic Year.
    """

    __tablename__ = "admission_cycles"

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_admission_cycle_dates_valid"),
        Index("ix_admission_cycles_school_id", "school_id"),
        Index("ix_admission_cycles_academic_year_id", "academic_year_id"),
        Index("ix_admission_cycles_status", "status"),
        Index(
            "uq_admission_cycle_school_code",
            "school_id",
            "code",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index(
            "uq_admission_cycle_school_name_year",
            "school_id",
            "academic_year_id",
            "name",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(50),
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

    status: Mapped[AdmissionCycleStatus] = mapped_column(
        Enum(AdmissionCycleStatus),
        default=AdmissionCycleStatus.DRAFT,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    school: Mapped[School] = orm_relationship(
        "School",
        foreign_keys=[school_id],
        lazy="select",
    )

    academic_year: Mapped[AcademicYear] = orm_relationship(
        "AcademicYear",
        foreign_keys=[academic_year_id],
        lazy="select",
    )

    applicants: Mapped[list[Applicant]] = orm_relationship(
        "Applicant",
        back_populates="admission_cycle",
        cascade="all, delete-orphan",
        lazy="select",
    )

    applications: Mapped[list[AdmissionApplication]] = orm_relationship(
        "AdmissionApplication",
        back_populates="admission_cycle",
        cascade="all, delete-orphan",
        lazy="select",
    )
