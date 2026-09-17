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

from app.common.enums.inventory import (
    AssetAssignmentStatus,
    AssetAssignmentType,
    AssetCondition,
)
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.identity.models.user import IdentityUser
    from app.models.inventory.asset import PhysicalAsset
    from app.models.school.school import School
    from app.models.student.student import Student
    from app.models.teacher.teacher import Teacher
    from app.models.timetable.classroom import Classroom


class AssetAssignment(CommonModel):
    """
    Records assignment of physical asset custody to a Teacher/Staff, Student, Classroom, or Department.
    """

    __tablename__ = "asset_assignments"

    __table_args__ = (
        Index("ix_asset_assignments_school_id", "school_id"),
        Index("ix_asset_assignments_asset_id", "asset_id"),
        Index("ix_asset_assignments_teacher_id", "teacher_id"),
        Index("ix_asset_assignments_student_id", "student_id"),
        Index("ix_asset_assignments_classroom_id", "classroom_id"),
        Index("ix_asset_assignments_user_id", "user_id"),
        Index("ix_asset_assignments_status", "status"),
        Index(
            "uq_active_asset_assignment",
            "school_id",
            "asset_id",
            unique=True,
            postgresql_where=text("is_deleted = false AND status = 'ACTIVE'"),
            sqlite_where=text("is_deleted = 0 AND status = 'ACTIVE'"),
        ),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("physical_assets.id", ondelete="CASCADE"),
        nullable=False,
    )

    assignment_type: Mapped[AssetAssignmentType] = mapped_column(
        Enum(AssetAssignmentType, name="asset_assignment_type", create_constraint=False),
        nullable=False,
        default=AssetAssignmentType.STAFF,
    )

    teacher_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
    )

    student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="SET NULL"),
        nullable=True,
    )

    classroom_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id", ondelete="SET NULL"),
        nullable=True,
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    department_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    assigned_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    expected_return_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    actual_return_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    assigned_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[AssetAssignmentStatus] = mapped_column(
        Enum(AssetAssignmentStatus, name="asset_assignment_status", create_constraint=False),
        nullable=False,
        default=AssetAssignmentStatus.ACTIVE,
    )

    condition_on_assignment: Mapped[AssetCondition] = mapped_column(
        Enum(AssetCondition, name="asset_condition", create_constraint=False),
        nullable=False,
        default=AssetCondition.GOOD,
    )

    condition_on_return: Mapped[AssetCondition | None] = mapped_column(
        Enum(AssetCondition, name="asset_condition", create_constraint=False),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    school: Mapped[School] = orm_relationship(
        "School",
        foreign_keys=[school_id],
        lazy="select",
    )

    asset: Mapped[PhysicalAsset] = orm_relationship(
        "PhysicalAsset",
        foreign_keys=[asset_id],
        back_populates="assignments",
        lazy="select",
    )

    teacher: Mapped[Teacher | None] = orm_relationship(
        "Teacher",
        foreign_keys=[teacher_id],
        lazy="select",
    )

    student: Mapped[Student | None] = orm_relationship(
        "Student",
        foreign_keys=[student_id],
        lazy="select",
    )

    classroom: Mapped[Classroom | None] = orm_relationship(
        "Classroom",
        foreign_keys=[classroom_id],
        lazy="select",
    )

    user: Mapped[IdentityUser | None] = orm_relationship(
        "IdentityUser",
        foreign_keys=[user_id],
        lazy="select",
    )

    assigned_by_user: Mapped[IdentityUser | None] = orm_relationship(
        "IdentityUser",
        foreign_keys=[assigned_by_user_id],
        lazy="select",
    )
