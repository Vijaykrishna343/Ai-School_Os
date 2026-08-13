from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.identity.models.user import IdentityUser
    from app.models.academic_year.academic_year import AcademicYear
    from app.models.school.school import School
    from app.models.school_class.school_class import SchoolClass
    from app.models.section.section import Section
    from app.models.student.student import Student


class ProgressionExecutionStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProgressionExecution(CommonModel):
    """
    Audit and tracking record for an Academic Progression execution run.
    """

    __tablename__ = "progression_executions"

    __table_args__ = (
        Index(
            "uq_progression_execution_idempotency",
            "school_id",
            "idempotency_key",
            unique=True,
        ),
        Index(
            "uq_progression_execution_active_school",
            "school_id",
            unique=True,
            postgresql_where=text("status IN ('PENDING', 'RUNNING')"),
            sqlite_where=text("status IN ('PENDING', 'RUNNING')"),
        ),
        Index("ix_progression_execution_school_id", "school_id"),
        Index("ix_progression_execution_source_ay", "source_academic_year_id"),
        Index("ix_progression_execution_target_ay", "target_academic_year_id"),
        Index("ix_progression_execution_status", "status"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    source_academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )

    target_academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )

    execution_plan_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    status: Mapped[ProgressionExecutionStatus] = mapped_column(
        SQLEnum(ProgressionExecutionStatus, native_enum=False, values_callable=lambda obj: [e.value for e in obj]),
        default=ProgressionExecutionStatus.PENDING,
        nullable=False,
    )

    total_students: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    promoted_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    graduated_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    retained_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    blocked_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    excluded_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    error_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    initiated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    school: Mapped["School"] = orm_relationship()
    source_academic_year: Mapped["AcademicYear"] = orm_relationship(foreign_keys=[source_academic_year_id])
    target_academic_year: Mapped["AcademicYear"] = orm_relationship(foreign_keys=[target_academic_year_id])
    initiated_by_user: Mapped["IdentityUser | None"] = orm_relationship()
    items: Mapped[list["ProgressionExecutionItem"]] = orm_relationship(
        back_populates="execution",
        cascade="all, delete-orphan",
    )


class ProgressionExecutionItem(CommonModel):
    """
    Individual student execution audit item for an Academic Progression run.
    """

    __tablename__ = "progression_execution_items"

    __table_args__ = (
        Index("ix_progression_exec_items_execution_id", "execution_id"),
        Index("ix_progression_exec_items_student_id", "student_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("progression_executions.id", ondelete="CASCADE"),
        nullable=False,
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )

    source_class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("school_classes.id", ondelete="RESTRICT"),
        nullable=False,
    )

    source_section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="RESTRICT"),
        nullable=False,
    )

    source_roll_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    target_class_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("school_classes.id", ondelete="RESTRICT"),
        nullable=True,
    )

    target_section_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="RESTRICT"),
        nullable=True,
    )

    allocated_roll_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    decision: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    execution: Mapped["ProgressionExecution"] = orm_relationship(back_populates="items")
    student: Mapped["Student"] = orm_relationship()
    source_class: Mapped["SchoolClass"] = orm_relationship(foreign_keys=[source_class_id])
    source_section: Mapped["Section"] = orm_relationship(foreign_keys=[source_section_id])
    target_class: Mapped["SchoolClass | None"] = orm_relationship(foreign_keys=[target_class_id])
    target_section: Mapped["Section | None"] = orm_relationship(foreign_keys=[target_section_id])
