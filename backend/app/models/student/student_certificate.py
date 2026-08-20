from __future__ import annotations

import uuid
from datetime import date
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    Enum,
    ForeignKey,
    Index,
    JSON,
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
    from app.identity.models.user import IdentityUser
    from app.models.school.school import School
    from app.models.student.student import Student


class CertificateType(str, PyEnum):
    TRANSFER_CERTIFICATE = "TC"
    BONAFIDE = "BONAFIDE"


class StudentCertificate(CommonModel):
    """
    Represents an official issued certificate (Transfer Certificate or Bonafide) for a student.

    Every certificate belongs to:
    - School (multi-tenant boundary)
    - Student
    """

    __tablename__ = "student_certificates"

    __table_args__ = (
        Index(
            "uq_student_certificate_number_active",
            "school_id",
            "certificate_number",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index("ix_student_certificates_school_id", "school_id"),
        Index("ix_student_certificates_student_id", "student_id"),
        Index("ix_student_certificates_type", "certificate_type"),
        Index("ix_student_certificates_issued_date", "issued_date"),
    )

    # ------------------------------------------------------------------
    # Foreign Keys
    # ------------------------------------------------------------------

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

    issued_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------

    certificate_type: Mapped[CertificateType] = mapped_column(
        Enum(CertificateType),
        nullable=False,
    )

    certificate_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    issued_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )

    purpose: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    reason_for_leaving: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    conduct: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default="Good",
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    school: Mapped[School] = orm_relationship(
        "School",
        foreign_keys=[school_id],
    )

    student: Mapped[Student] = orm_relationship(
        "Student",
        foreign_keys=[student_id],
    )

    issued_by: Mapped[IdentityUser | None] = orm_relationship(
        "IdentityUser",
        foreign_keys=[issued_by_id],
    )
