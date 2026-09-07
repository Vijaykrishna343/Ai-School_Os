from __future__ import annotations

from decimal import Decimal
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.school.school import School
    from app.models.teacher.teacher import Teacher
    from app.models.academic_year.academic_year import AcademicYear
    from app.identity.models.user import IdentityUser


class StaffLeaveType(CommonModel):
    """
    Configurable leave type policy per school (e.g. CASUAL, SICK, EARNED, MATERNITY).
    """

    __tablename__ = "staff_leave_types"

    __table_args__ = (
        Index("ix_staff_leave_types_school_id", "school_id"),
        Index("ix_staff_leave_types_code", "code"),
        UniqueConstraint("school_id", "code", "is_deleted", name="uq_staff_leave_types_school_code"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    max_days_per_year: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("12.00"),
    )

    requires_attachment: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_paid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Relationships
    school: Mapped["School"] = relationship("School")


class StaffLeaveBalance(CommonModel):
    """
    Tracks annual leave allocations, used days, and pending days per teacher per leave type.
    """

    __tablename__ = "staff_leave_balances"

    __table_args__ = (
        Index("ix_staff_leave_balances_school_id", "school_id"),
        Index("ix_staff_leave_balances_teacher_id", "teacher_id"),
        Index("ix_staff_leave_balances_academic_year_id", "academic_year_id"),
        Index("ix_staff_leave_balances_leave_type_id", "leave_type_id"),
        UniqueConstraint("school_id", "teacher_id", "academic_year_id", "leave_type_id", "is_deleted", name="uq_staff_leave_balances_teacher_year_type"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
    )

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )

    leave_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("staff_leave_types.id", ondelete="CASCADE"),
        nullable=False,
    )

    allocated_days: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("12.00"),
    )

    used_days: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    pending_days: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Relationships
    teacher: Mapped["Teacher"] = relationship("Teacher")
    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear")
    leave_type: Mapped["StaffLeaveType"] = relationship("StaffLeaveType")


class StaffLeaveRequest(CommonModel):
    """
    Represents a staff leave request submission and approval workflow.
    """

    __tablename__ = "staff_leave_requests"

    __table_args__ = (
        Index("ix_staff_leave_requests_school_id", "school_id"),
        Index("ix_staff_leave_requests_teacher_id", "teacher_id"),
        Index("ix_staff_leave_requests_academic_year_id", "academic_year_id"),
        Index("ix_staff_leave_requests_status", "status"),
        Index("ix_staff_leave_requests_start_date", "start_date"),
        Index("ix_staff_leave_requests_end_date", "end_date"),
        CheckConstraint("end_date >= start_date", name="ck_staff_leave_requests_date_range"),
        CheckConstraint("requested_days > 0", name="ck_staff_leave_requests_positive_days"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
    )

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )

    leave_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("staff_leave_types.id", ondelete="CASCADE"),
        nullable=False,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    requested_days: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("1.00"),
    )

    half_day_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="FULL_DAY",  # FULL_DAY, FIRST_HALF, SECOND_HALF
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    attachment_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",  # DRAFT, PENDING, APPROVED, REJECTED, CANCELLED
    )

    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    rejected_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    cancelled_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    approval_remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    teacher: Mapped["Teacher"] = relationship("Teacher")
    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear")
    leave_type: Mapped["StaffLeaveType"] = relationship("StaffLeaveType")
    requested_by: Mapped["IdentityUser"] = relationship("IdentityUser", foreign_keys=[requested_by_user_id])
    approved_by: Mapped["IdentityUser | None"] = relationship("IdentityUser", foreign_keys=[approved_by_user_id])
    rejected_by: Mapped["IdentityUser | None"] = relationship("IdentityUser", foreign_keys=[rejected_by_user_id])
    cancelled_by: Mapped["IdentityUser | None"] = relationship("IdentityUser", foreign_keys=[cancelled_by_user_id])
    approval_history: Mapped[list["StaffLeaveApprovalHistory"]] = relationship("StaffLeaveApprovalHistory", back_populates="leave_request", cascade="all, delete-orphan")


class StaffLeaveApprovalHistory(CommonModel):
    """
    Workflow transition log for a staff leave request.
    """

    __tablename__ = "staff_leave_approval_history"

    __table_args__ = (
        Index("ix_staff_leave_approval_history_school_id", "school_id"),
        Index("ix_staff_leave_approval_history_request_id", "leave_request_id"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    leave_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("staff_leave_requests.id", ondelete="CASCADE"),
        nullable=False,
    )

    action_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="CASCADE"),
        nullable=False,
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,  # SUBMITTED, APPROVED, REJECTED, CANCELLED, UPDATED
    )

    from_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    to_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    leave_request: Mapped["StaffLeaveRequest"] = relationship("StaffLeaveRequest", back_populates="approval_history")
    action_by: Mapped["IdentityUser"] = relationship("IdentityUser", foreign_keys=[action_by_user_id])
