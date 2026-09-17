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

from app.common.enums.admissions import ApplicantStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.admissions.admission_application import AdmissionApplication
    from app.models.admissions.admission_cycle import AdmissionCycle
    from app.models.school.school import School


class Applicant(CommonModel):
    """
    Represents a prospective student applicant in the Admissions pipeline.
    Distinct from the authoritative Student entity in Student SIS.
    """

    __tablename__ = "applicants"

    __table_args__ = (
        Index("ix_applicants_school_id", "school_id"),
        Index("ix_applicants_admission_cycle_id", "admission_cycle_id"),
        Index("ix_applicants_status", "status"),
        Index("ix_applicants_names", "school_id", "first_name", "last_name"),
        Index(
            "uq_applicant_school_applicant_number",
            "school_id",
            "applicant_number",
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

    admission_cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admission_cycles.id", ondelete="SET NULL"),
        nullable=True,
    )

    applicant_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    middle_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    gender: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    parent_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    parent_phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    parent_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    status: Mapped[ApplicantStatus] = mapped_column(
        Enum(ApplicantStatus),
        default=ApplicantStatus.PROSPECT,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    # Relationships
    school: Mapped[School] = orm_relationship(
        "School",
        foreign_keys=[school_id],
        lazy="select",
    )

    admission_cycle: Mapped[AdmissionCycle | None] = orm_relationship(
        "AdmissionCycle",
        foreign_keys=[admission_cycle_id],
        back_populates="applicants",
        lazy="select",
    )

    applications: Mapped[list[AdmissionApplication]] = orm_relationship(
        "AdmissionApplication",
        back_populates="applicant",
        cascade="all, delete-orphan",
        lazy="select",
    )
