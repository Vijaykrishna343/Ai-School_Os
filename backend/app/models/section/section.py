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

from app.common.enums import SectionStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.school_class.school_class import SchoolClass
    from app.models.student.student import Student


class Section(CommonModel):
    """
    Represents a section within a school class.

    Examples:
        Class 1 -> A
        Class 1 -> B
        Class 2 -> A

    A Section belongs to one SchoolClass and can contain
    multiple Students.
    """

    __tablename__ = "sections"

    __table_args__ = (
        UniqueConstraint(
            "school_class_id",
            "name",
            name="uq_sections_school_class_id_name",
        ),
        Index(
            "ix_sections_school_class_id",
            "school_class_id",
        ),
        Index(
            "ix_sections_status",
            "status",
        ),
        Index(
            "ix_sections_name",
            "name",
        ),
    )

    # ------------------------------------------------------------------
    # School Class
    # ------------------------------------------------------------------

    school_class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "school_classes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Section Information
    # ------------------------------------------------------------------

    name: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    room_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    capacity: Mapped[int] = mapped_column(
        Integer,
        default=40,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    status: Mapped[SectionStatus] = mapped_column(
        Enum(
            SectionStatus,
            name="section_status",
            native_enum=True,
            validate_strings=True,
        ),
        default=SectionStatus.ACTIVE,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    school_class: Mapped["SchoolClass"] = orm_relationship(
        back_populates="sections",
    )

    students: Mapped[list["Student"]] = orm_relationship(
        back_populates="section",
        cascade="all, delete-orphan",
    )