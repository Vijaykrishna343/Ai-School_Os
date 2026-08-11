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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums import TransferCertificateStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.academic_year.academic_year import AcademicYear
    from app.models.school.school import School
    from app.models.student.student import Student


class TransferCertificate(CommonModel):
    """
    Represents a Transfer Certificate (TC) issued to a student upon exit/leaving school.
    """

    __tablename__ = "transfer_certificates"

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "tc_number",
            name="uq_tc_school_number",
        ),
        Index("ix_tc_school_id", "school_id"),
        Index("ix_tc_student_id", "student_id"),
        Index("ix_tc_academic_year_id", "academic_year_id"),
        Index("ix_tc_number", "tc_number"),
        Index("ix_tc_status", "status"),
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

    tc_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    issue_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    leaving_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    destination_school: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    status: Mapped[TransferCertificateStatus] = mapped_column(
        Enum(
            TransferCertificateStatus,
            name="transfer_certificate_status",
            native_enum=True,
            validate_strings=True,
        ),
        default=TransferCertificateStatus.ISSUED,
        nullable=False,
    )

    # Relationships
    school: Mapped["School"] = orm_relationship()
    student: Mapped["Student"] = orm_relationship()
    academic_year: Mapped["AcademicYear"] = orm_relationship()
