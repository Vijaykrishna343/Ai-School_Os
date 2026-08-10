from __future__ import annotations

from decimal import Decimal
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
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

from app.common.enums.fees import FeeCategory, FeeStructureStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.academic_year.academic_year import AcademicYear
    from app.models.school.school import School
    from app.models.school_class.school_class import SchoolClass


class FeeStructure(CommonModel):
    """
    Represents a fee structure applicable to a school, academic year, and optional school class.
    """

    __tablename__ = "fee_structures"

    __table_args__ = (
        Index(
            "uq_fee_structure_active_name_class",
            "school_id",
            "academic_year_id",
            "school_class_id",
            "name",
            unique=True,
            postgresql_where=text("is_deleted = false AND school_class_id IS NOT NULL"),
            sqlite_where=text("is_deleted = 0 AND school_class_id IS NOT NULL"),
        ),
        Index(
            "uq_fee_structure_active_name_noclass",
            "school_id",
            "academic_year_id",
            "name",
            unique=True,
            postgresql_where=text("is_deleted = false AND school_class_id IS NULL"),
            sqlite_where=text("is_deleted = 0 AND school_class_id IS NULL"),
        ),
        Index("ix_fee_structures_school_id", "school_id"),
        Index("ix_fee_structures_academic_year_id", "academic_year_id"),
        Index("ix_fee_structures_school_class_id", "school_class_id"),
        Index("ix_fee_structures_status", "status"),
    )

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

    school_class_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("school_classes.id", ondelete="CASCADE"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    status: Mapped[FeeStructureStatus] = mapped_column(
        Enum(
            FeeStructureStatus,
            name="fee_structure_status",
            native_enum=True,
            validate_strings=True,
        ),
        default=FeeStructureStatus.DRAFT,
        nullable=False,
    )

    school: Mapped["School"] = orm_relationship()
    academic_year: Mapped["AcademicYear"] = orm_relationship()
    school_class: Mapped["SchoolClass | None"] = orm_relationship()

    items: Mapped[list["FeeItem"]] = orm_relationship(
        back_populates="fee_structure",
        cascade="all, delete-orphan",
    )


class FeeItem(CommonModel):
    """
    Represents an individual fee line item inside a FeeStructure.
    """

    __tablename__ = "fee_items"

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_fee_items_amount_non_negative"),
        Index("ix_fee_items_fee_structure_id", "fee_structure_id"),
        Index("ix_fee_items_category", "category"),
    )

    fee_structure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fee_structures.id", ondelete="CASCADE"),
        nullable=False,
    )

    category: Mapped[FeeCategory] = mapped_column(
        Enum(
            FeeCategory,
            name="fee_category",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    is_optional: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    fee_structure: Mapped["FeeStructure"] = orm_relationship(
        back_populates="items"
    )
