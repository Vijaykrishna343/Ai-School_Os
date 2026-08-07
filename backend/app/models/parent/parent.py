from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.parent import ParentRelationship
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.school.school import School
    from app.models.student.student import Student


class Parent(CommonModel):
    """
    Represents a parent or guardian.

    A parent can be associated with one or more students.
    Every parent belongs to exactly one school.
    """

    __tablename__ = "parents"

    __table_args__ = (
        Index("ix_parents_school_id", "school_id"),
        Index("ix_parents_primary_phone", "primary_phone"),
        Index("ix_parents_email", "email"),
        Index("ix_parents_is_active", "is_active"),
    )

    # ------------------------------------------------------------------
    # Parent Information
    # ------------------------------------------------------------------

    father_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    mother_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    guardian_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    relationship: Mapped[ParentRelationship] = mapped_column(
        Enum(
            ParentRelationship,
            name="parent_relationship",
            native_enum=True,
            validate_strings=True,
        ),
        default=ParentRelationship.FATHER,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Contact Information
    # ------------------------------------------------------------------

    primary_phone: Mapped[str] = mapped_column(
        String(15),
        unique=True,
        nullable=False,
    )

    secondary_phone: Mapped[str | None] = mapped_column(
        String(15),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    occupation: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    annual_income: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
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
    # Status
    # ------------------------------------------------------------------

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "schools.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    school: Mapped["School"] = orm_relationship(
        back_populates="parents",
    )

    students: Mapped[list["Student"]] = orm_relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
    )