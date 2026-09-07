from __future__ import annotations

import uuid
from datetime import date
from sqlalchemy import String, Numeric, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.common_model import CommonModel


class HostelFeeStructure(CommonModel):
    """
    Hostel Fee Structure definition.
    """
    __tablename__ = "hostel_fee_structures"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("idx_hostel_fee_struct_school", "school_id", "academic_year_id"),
    )


class HostelFeeAllocation(CommonModel):
    """
    Student Hostel Fee Allocation and Payment Ledger.
    """
    __tablename__ = "hostel_fee_allocations"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fee_structure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hostel_fee_structures.id", ondelete="CASCADE"),
        nullable=False,
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount_due: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    paid_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="UNPAID") # UNPAID, PARTIAL, PAID

    __table_args__ = (
        Index("idx_hostel_fee_alloc_student", "school_id", "student_id"),
    )
