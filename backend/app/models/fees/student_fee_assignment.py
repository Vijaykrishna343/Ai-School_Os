from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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

from app.common.enums.fees import (
    DiscountType,
    FeeCategory,
    StudentFeeAssignmentStatus,
)
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.academic_year.academic_year import AcademicYear
    from app.models.fees.fee_payment import FeePayment
    from app.models.fees.fee_structure import FeeStructure
    from app.models.school.school import School
    from app.models.student.student import Student


class StudentFeeAssignment(CommonModel):
    """
    Represents the assignment of a fee structure to a student for an academic year.
    """

    __tablename__ = "student_fee_assignments"

    __table_args__ = (
        Index(
            "uq_student_fee_assignment_active",
            "school_id",
            "academic_year_id",
            "student_id",
            "fee_structure_id",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index("ix_student_fee_assignments_school_id", "school_id"),
        Index("ix_student_fee_assignments_academic_year_id", "academic_year_id"),
        Index("ix_student_fee_assignments_student_id", "student_id"),
        Index("ix_student_fee_assignments_fee_structure_id", "fee_structure_id"),
        Index("ix_student_fee_assignments_status", "status"),
        Index("ix_fee_assignments_school_year_student", "school_id", "academic_year_id", "student_id"),
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

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )

    fee_structure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fee_structures.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[StudentFeeAssignmentStatus] = mapped_column(
        Enum(
            StudentFeeAssignmentStatus,
            name="student_fee_assignment_status",
            native_enum=True,
            validate_strings=True,
        ),
        default=StudentFeeAssignmentStatus.PENDING,
        nullable=False,
    )

    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    school: Mapped["School"] = orm_relationship()
    academic_year: Mapped["AcademicYear"] = orm_relationship()
    student: Mapped["Student"] = orm_relationship()
    fee_structure: Mapped["FeeStructure"] = orm_relationship()

    student_fee_items: Mapped[list["StudentFeeItem"]] = orm_relationship(
        back_populates="assignment",
        cascade="all, delete-orphan",
    )

    discounts: Mapped[list["FeeDiscount"]] = orm_relationship(
        back_populates="assignment",
        cascade="all, delete-orphan",
    )

    payments: Mapped[list["FeePayment"]] = orm_relationship(
        back_populates="assignment",
        cascade="all, delete-orphan",
    )


class StudentFeeItem(CommonModel):
    """
    Represents a specific fee line item assigned to a student.
    Can be derived from a structure item or created as a student-specific item.
    """

    __tablename__ = "student_fee_items"

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_student_fee_items_amount_non_negative"),
        Index("ix_student_fee_items_assignment_id", "student_fee_assignment_id"),
        Index("ix_student_fee_items_category", "category"),
    )

    student_fee_assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_fee_assignments.id", ondelete="CASCADE"),
        nullable=False,
    )

    fee_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fee_items.id", ondelete="SET NULL"),
        nullable=True,
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

    is_applicable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    assignment: Mapped["StudentFeeAssignment"] = orm_relationship(
        back_populates="student_fee_items"
    )


class FeeDiscount(CommonModel):
    """
    Represents a discount or concession applied to a student's fee assignment.
    """

    __tablename__ = "fee_discounts"

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_fee_discounts_amount_positive"),
        Index("ix_fee_discounts_assignment_id", "student_fee_assignment_id"),
        Index("ix_fee_discounts_type", "discount_type"),
    )

    student_fee_assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_fee_assignments.id", ondelete="CASCADE"),
        nullable=False,
    )

    discount_type: Mapped[DiscountType] = mapped_column(
        Enum(
            DiscountType,
            name="discount_type",
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

    remarks: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    assignment: Mapped["StudentFeeAssignment"] = orm_relationship(
        back_populates="discounts"
    )
