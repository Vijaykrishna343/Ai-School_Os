from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.library import LibraryMemberStatus, LibraryMemberType
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.identity.models.user import IdentityUser
    from app.models.library.fine import LibraryFine
    from app.models.library.loan import BookLoan
    from app.models.library.reservation import BookReservation
    from app.models.student.student import Student
    from app.models.teacher.teacher import Teacher


class LibraryMember(CommonModel):
    """
    Represents a registered library borrower (student, teacher, or staff member).
    Maintains card number uniqueness and borrowing limits.
    Enforces strict tenant isolation via school_id.
    """

    __tablename__ = "library_members"

    __table_args__ = (
        CheckConstraint("max_books_allowed > 0", name="ck_library_member_max_books_pos"),
        Index("ix_library_members_school_id", "school_id"),
        Index("ix_library_members_student_id", "student_id"),
        Index("ix_library_members_teacher_id", "teacher_id"),
        Index("ix_library_members_user_id", "user_id"),
        Index("ix_library_members_status", "status"),
        Index("ix_library_members_member_type", "member_type"),
        Index(
            "uq_library_member_school_card",
            "school_id",
            "card_number",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index(
            "uq_library_member_school_student",
            "school_id",
            "student_id",
            unique=True,
            postgresql_where=text("is_deleted = false AND student_id IS NOT NULL"),
            sqlite_where=text("is_deleted = 0 AND student_id IS NOT NULL"),
        ),
        Index(
            "uq_library_member_school_teacher",
            "school_id",
            "teacher_id",
            unique=True,
            postgresql_where=text("is_deleted = false AND teacher_id IS NOT NULL"),
            sqlite_where=text("is_deleted = 0 AND teacher_id IS NOT NULL"),
        ),
        Index(
            "uq_library_member_school_user",
            "school_id",
            "user_id",
            unique=True,
            postgresql_where=text("is_deleted = false AND user_id IS NOT NULL"),
            sqlite_where=text("is_deleted = 0 AND user_id IS NOT NULL"),
        ),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    member_type: Mapped[LibraryMemberType] = mapped_column(
        Enum(LibraryMemberType, name="librarymembertype", native_enum=False),
        nullable=False,
        default=LibraryMemberType.STUDENT,
    )

    student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="SET NULL"),
        nullable=True,
    )

    teacher_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    card_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    issue_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    max_books_allowed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
    )

    status: Mapped[LibraryMemberStatus] = mapped_column(
        Enum(LibraryMemberStatus, name="librarymemberstatus", native_enum=False),
        nullable=False,
        default=LibraryMemberStatus.ACTIVE,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    student: Mapped[Student | None] = orm_relationship(
        "Student",
        foreign_keys=[student_id],
    )

    teacher: Mapped[Teacher | None] = orm_relationship(
        "Teacher",
        foreign_keys=[teacher_id],
    )

    user: Mapped[IdentityUser | None] = orm_relationship(
        "IdentityUser",
        foreign_keys=[user_id],
    )

    loans: Mapped[list[BookLoan]] = orm_relationship(
        "BookLoan",
        back_populates="member",
        cascade="all, delete-orphan",
    )

    reservations: Mapped[list[BookReservation]] = orm_relationship(
        "BookReservation",
        back_populates="member",
        cascade="all, delete-orphan",
    )

    fines: Mapped[list[LibraryFine]] = orm_relationship(
        "LibraryFine",
        back_populates="member",
        cascade="all, delete-orphan",
    )

    @property
    def display_name(self) -> str:
        if self.member_type == LibraryMemberType.STUDENT and self.student:
            first = getattr(self.student, "first_name", "") or ""
            last = getattr(self.student, "last_name", "") or ""
            return f"{first} {last}".strip()
        if self.member_type == LibraryMemberType.TEACHER and self.teacher:
            first = getattr(self.teacher, "first_name", "") or ""
            last = getattr(self.teacher, "last_name", "") or ""
            return f"{first} {last}".strip()
        if self.user:
            return getattr(self.user, "full_name", None) or getattr(self.user, "email", "") or self.card_number
        return self.card_number
