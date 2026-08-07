from __future__ import annotations

from decimal import Decimal
import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    Enum,
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

from app.common.enums import (
    BloodGroup,
    Gender,
    TeacherStatus,
)
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.school.school import School


class Teacher(CommonModel):
    """
    Represents a teacher working in a school.
    """

    __tablename__ = "teachers"

    __table_args__ = (
        Index("ix_teachers_school_id", "school_id"),
        Index("ix_teachers_employee_id", "employee_id"),
        Index("ix_teachers_email", "email"),
        Index("ix_teachers_phone", "phone"),
        Index("ix_teachers_status", "status"),
        Index("ix_teachers_first_name", "first_name"),
        Index("ix_teachers_last_name", "last_name"),
    )

    # ------------------------------------------------------------------
    # Foreign Key
    # ------------------------------------------------------------------

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Employee Information
    # ------------------------------------------------------------------

    employee_id: Mapped[str] = mapped_column(
        String(30),
        unique=True,
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

    last_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    gender: Mapped[Gender] = mapped_column(
        Enum(
            Gender,
            name="gender",
            native_enum=True,
            validate_strings=True,
            create_type=False,
        ),
        nullable=False,
    )

    blood_group: Mapped[BloodGroup | None] = mapped_column(
        Enum(
            BloodGroup,
            name="blood_group",
            native_enum=True,
            validate_strings=True,
            create_type=False,
        ),
        nullable=True,
    )

    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    joining_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    qualification: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    specialization: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    experience_years: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    # ------------------------------------------------------------------
    # Contact
    # ------------------------------------------------------------------

    phone: Mapped[str] = mapped_column(
        String(15),
        unique=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    emergency_contact: Mapped[str | None] = mapped_column(
        String(15),
        nullable=True,
    )

    profile_photo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Address
    # ------------------------------------------------------------------

    address_line1: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    address_line2: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    district: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    country: Mapped[str] = mapped_column(
        String(100),
        default="India",
        server_default=text("'India'"),
        nullable=False,
    )

    postal_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Employment
    # ------------------------------------------------------------------

    salary: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    status: Mapped[TeacherStatus] = mapped_column(
        Enum(
            TeacherStatus,
            name="teacher_status",
            native_enum=True,
            validate_strings=True,
            create_type=False,
        ),
        default=TeacherStatus.ACTIVE,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Relationship
    # ------------------------------------------------------------------

    school: Mapped["School"] = orm_relationship(
        back_populates="teachers",
    )

    @property
    def full_name(self) -> str:
        return " ".join(
            part
            for part in (
                self.first_name,
                self.middle_name,
                self.last_name,
            )
            if part
        )