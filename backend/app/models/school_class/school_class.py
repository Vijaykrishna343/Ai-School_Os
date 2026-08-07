from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums import SchoolClassStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.school.school import School
    from app.models.section.section import Section
    from app.models.student.student import Student


class SchoolClass(CommonModel):
    """
    Represents a class within a school.

    Examples:
        Nursery
        LKG
        UKG
        Class 1
        Class 2

    A SchoolClass belongs to one School and can contain
    multiple Sections and Students.
    """

    __tablename__ = "school_classes"

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "name",
            name="uq_school_classes_school_id_name",
        ),
        Index(
            "ix_school_classes_school_id",
            "school_id",
        ),
        Index(
            "ix_school_classes_status",
            "status",
        ),
        Index(
            "ix_school_classes_display_order",
            "display_order",
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
    # Class Information
    # ------------------------------------------------------------------

    name: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    status: Mapped[SchoolClassStatus] = mapped_column(
        Enum(
            SchoolClassStatus,
            name="school_class_status",
            native_enum=True,
            validate_strings=True,
        ),
        default=SchoolClassStatus.ACTIVE,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    school: Mapped["School"] = orm_relationship(
        back_populates="school_classes",
    )

    sections: Mapped[list["Section"]] = orm_relationship(
        back_populates="school_class",
        cascade="all, delete-orphan",
    )

    students: Mapped[list["Student"]] = orm_relationship(
        back_populates="school_class",
        cascade="all, delete-orphan",
    )