from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
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

from app.common.enums.admissions import AdmissionApplicationStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.academic_year.academic_year import AcademicYear
    from app.models.admissions.admission_cycle import AdmissionCycle
    from app.models.admissions.admission_decision import AdmissionDecision
    from app.models.admissions.applicant import Applicant
    from app.models.admissions.application_status_history import ApplicationStatusHistory
    from app.models.school.school import School
    from app.models.school_class.school_class import SchoolClass
    from app.models.section.section import Section


class AdmissionApplication(CommonModel):
    """
    Represents an admission application submitted by an applicant for a target class/cycle.
    """

    __tablename__ = "admission_applications"

    __table_args__ = (
        Index("ix_admission_applications_school_id", "school_id"),
        Index("ix_admission_applications_applicant_id", "applicant_id"),
        Index("ix_admission_applications_cycle_id", "admission_cycle_id"),
        Index("ix_admission_applications_year_id", "academic_year_id"),
        Index("ix_admission_applications_class_id", "target_class_id"),
        Index("ix_admission_applications_status", "status"),
        Index(
            "uq_admission_app_school_app_number",
            "school_id",
            "application_number",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index(
            "uq_admission_app_applicant_cycle_active",
            "school_id",
            "applicant_id",
            "admission_cycle_id",
            unique=True,
            postgresql_where=text("is_deleted = false AND status NOT IN ('REJECTED', 'WITHDRAWN')"),
            sqlite_where=text("is_deleted = 0 AND status NOT IN ('REJECTED', 'WITHDRAWN')"),
        ),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    applicant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applicants.id", ondelete="CASCADE"),
        nullable=False,
    )

    admission_cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admission_cycles.id", ondelete="RESTRICT"),
        nullable=False,
    )

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )

    target_class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("school_classes.id", ondelete="RESTRICT"),
        nullable=False,
    )

    target_section_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="SET NULL"),
        nullable=True,
    )

    application_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    application_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[AdmissionApplicationStatus] = mapped_column(
        Enum(AdmissionApplicationStatus),
        default=AdmissionApplicationStatus.DRAFT,
        nullable=False,
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    decision_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    # Relationships
    school: Mapped[School] = orm_relationship(
        "School",
        foreign_keys=[school_id],
        lazy="select",
    )

    applicant: Mapped[Applicant] = orm_relationship(
        "Applicant",
        foreign_keys=[applicant_id],
        back_populates="applications",
        lazy="select",
    )

    admission_cycle: Mapped[AdmissionCycle] = orm_relationship(
        "AdmissionCycle",
        foreign_keys=[admission_cycle_id],
        back_populates="applications",
        lazy="select",
    )

    academic_year: Mapped[AcademicYear] = orm_relationship(
        "AcademicYear",
        foreign_keys=[academic_year_id],
        lazy="select",
    )

    target_class: Mapped[SchoolClass] = orm_relationship(
        "SchoolClass",
        foreign_keys=[target_class_id],
        lazy="select",
    )

    target_section: Mapped[Section | None] = orm_relationship(
        "Section",
        foreign_keys=[target_section_id],
        lazy="select",
    )

    status_history: Mapped[list[ApplicationStatusHistory]] = orm_relationship(
        "ApplicationStatusHistory",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="select",
    )

    decisions: Mapped[list[AdmissionDecision]] = orm_relationship(
        "AdmissionDecision",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="select",
    )
