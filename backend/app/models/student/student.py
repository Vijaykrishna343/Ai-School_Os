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

from app.common.enums import (
    BloodGroup,
    Gender,
    StudentStatus,
)
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.academic_year.academic_year import AcademicYear
    from app.models.parent.parent import Parent
    from app.models.school.school import School
    from app.models.school_class.school_class import SchoolClass
    from app.models.section.section import Section


class Student(CommonModel):
    """
    Represents a student enrolled in a school.

    Every student belongs to exactly one:
    - School
    - Academic Year
    - Class
    - Section
    - Parent/Guardian
    """

    __tablename__ = "students"

    __table_args__ = (
        Index(
            "uq_students_admission_number_active",
            "admission_number",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index(
            "uq_students_roll_number_active",
            "academic_year_id",
            "school_class_id",
            "roll_number",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index("ix_students_school_id", "school_id"),
        Index("ix_students_parent_id", "parent_id"),
        Index("ix_students_class_id", "school_class_id"),
        Index("ix_students_section_id", "section_id"),
        Index("ix_students_status", "status"),
        Index("ix_students_admission_number", "admission_number"),
        Index("ix_students_roll_number", "roll_number"),
        Index("ix_students_first_name", "first_name"),
        Index("ix_students_last_name", "last_name"),
    )

    # ------------------------------------------------------------------
    # Relationships (Foreign Keys)
    # ------------------------------------------------------------------

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )

    school_class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("school_classes.id", ondelete="CASCADE"),
        nullable=False,
    )

    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
    )

    parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parents.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Student Information
    # ------------------------------------------------------------------

    admission_number: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    roll_number: Mapped[str] = mapped_column(
        String(20),
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
        ),
        nullable=False,
    )

    blood_group: Mapped[BloodGroup | None] = mapped_column(
        Enum(
            BloodGroup,
            name="blood_group",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=True,
    )

    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    admission_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Contact
    # ------------------------------------------------------------------

    phone: Mapped[str | None] = mapped_column(
        String(15),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
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
        nullable=False,
    )

    postal_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    status: Mapped[StudentStatus] = mapped_column(
        Enum(
            StudentStatus,
            name="student_status",
            native_enum=True,
            validate_strings=True,
        ),
        default=StudentStatus.ACTIVE,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    school: Mapped["School"] = orm_relationship(
        back_populates="students",
    )

    academic_year: Mapped["AcademicYear"] = orm_relationship(
        back_populates="students",
    )

    school_class: Mapped["SchoolClass"] = orm_relationship(
        back_populates="students",
    )

    section: Mapped["Section"] = orm_relationship(
        back_populates="students",
    )

    parent: Mapped["Parent"] = orm_relationship(
        back_populates="students",
    )

    @property
    def full_name(self) -> str:
        """
        Returns the student's full name.
        """
        return " ".join(
            part
            for part in (
                self.first_name,
                self.middle_name,
                self.last_name,
            )
            if part
        )