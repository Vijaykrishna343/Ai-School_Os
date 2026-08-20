from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Index, String
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.school import SchoolStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.identity.models.role import IdentityRole
    from app.identity.models.user import IdentityUser

    from app.models.academic_year.academic_year import AcademicYear
    from app.models.parent.parent import Parent
    from app.models.school_class.school_class import SchoolClass
    from app.models.student.student import Student
    from app.models.subject.subject import Subject
    from app.models.teacher.teacher import Teacher


class School(CommonModel):
    """
    Represents a school in the ERP system.

    A school is the root entity for all academic data.
    Every Academic Year, Class, Parent, Student, Teacher,
    Subject, Attendance, Fee, and Examination record belongs
    to a School.
    """

    __tablename__ = "schools"

    __table_args__ = (
        Index("ix_schools_code", "code"),
        Index("ix_schools_city", "city"),
        Index("ix_schools_status", "status"),
    )

    # ------------------------------------------------------------------
    # Basic Information
    # ------------------------------------------------------------------

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    website: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    logo_url: Mapped[str | None] = mapped_column(
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

    # ------------------------------------------------------------------
    # Status & Subscription Lifecycle
    # ------------------------------------------------------------------

    status: Mapped[SchoolStatus] = mapped_column(
        Enum(
            SchoolStatus,
            name="school_status",
            native_enum=False,
            validate_strings=True,
        ),
        default=SchoolStatus.ACTIVE,
        nullable=False,
    )

    subscription_tier: Mapped[str] = mapped_column(
        String(50),
        default="STANDARD",
        nullable=False,
    )

    max_students: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    max_teachers: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    trial_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    subscription_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    grace_period_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    suspended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    suspension_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )


    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    academic_years: Mapped[list["AcademicYear"]] = orm_relationship(
        back_populates="school",
        cascade="all, delete-orphan",
    )

    parents: Mapped[list["Parent"]] = orm_relationship(
        back_populates="school",
        cascade="all, delete-orphan",
    )

    school_classes: Mapped[list["SchoolClass"]] = orm_relationship(
        back_populates="school",
        cascade="all, delete-orphan",
    )

    students: Mapped[list["Student"]] = orm_relationship(
        back_populates="school",
        cascade="all, delete-orphan",
    )

    teachers: Mapped[list["Teacher"]] = orm_relationship(
        back_populates="school",
        cascade="all, delete-orphan",
    )

    subjects: Mapped[list["Subject"]] = orm_relationship(
        back_populates="school",
        cascade="all, delete-orphan",
    )

    identity_users: Mapped[list["IdentityUser"]] = orm_relationship(
        "IdentityUser",
        back_populates="school",
        cascade="all, delete-orphan",
    )

    roles: Mapped[list["IdentityRole"]] = orm_relationship(
        "IdentityRole",
        back_populates="school",
        cascade="all, delete-orphan",
    )