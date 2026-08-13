from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
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

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.school.school import School
    from app.models.school_class.school_class import SchoolClass


class ClassProgressionRule(CommonModel):
    """
    Defines academic class progression rules for a school.

    Examples:
        Class 1 -> Class 2 (is_terminal = False, target_class_id = Class 2 ID)
        Class 12 -> NULL (is_terminal = True, target_class_id = None)
    """

    __tablename__ = "class_progression_rules"

    __table_args__ = (
        Index(
            "uq_class_progression_school_source",
            "school_id",
            "source_class_id",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index("ix_class_progression_school_id", "school_id"),
        Index("ix_class_progression_source_class_id", "source_class_id"),
        Index("ix_class_progression_target_class_id", "target_class_id"),
        Index("ix_class_progression_is_terminal", "is_terminal"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    source_class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("school_classes.id", ondelete="CASCADE"),
        nullable=False,
    )

    target_class_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("school_classes.id", ondelete="CASCADE"),
        nullable=True,
    )

    is_terminal: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    school: Mapped["School"] = orm_relationship()
    source_class: Mapped["SchoolClass"] = orm_relationship(
        foreign_keys=[source_class_id],
    )
    target_class: Mapped["SchoolClass | None"] = orm_relationship(
        foreign_keys=[target_class_id],
    )
