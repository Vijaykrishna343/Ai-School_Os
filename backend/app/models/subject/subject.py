from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.subject import SubjectStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.school.school import School


subject_status_enum = ENUM(
    SubjectStatus,
    name="subject_status",
    create_type=False,
)


class Subject(CommonModel):
    __tablename__ = "subjects"

    school_id: Mapped[str] = mapped_column(
        ForeignKey("schools.id"),
        nullable=False,
        index=True,
    )

    subject_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    subject_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_optional: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    status: Mapped[SubjectStatus] = mapped_column(
        subject_status_enum,
        default=SubjectStatus.ACTIVE,
        nullable=False,
    )

    school: Mapped["School"] = orm_relationship(
        back_populates="subjects",
    )