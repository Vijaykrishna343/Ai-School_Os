from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.timetable import TimetableStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.academic_term.academic_term import AcademicTerm
    from app.models.academic_year.academic_year import AcademicYear
    from app.models.school.school import School
    from app.models.school_class.school_class import SchoolClass
    from app.models.section.section import Section
    from app.models.timetable.timetable_entry import TimetableEntry


class Timetable(CommonModel):
    """
    Represents a timetable container for a class section in an academic year/term.
    """

    __tablename__ = "timetables"

    __table_args__ = (
        Index("ix_timetables_school_id", "school_id"),
        Index("ix_timetables_academic_year_id", "academic_year_id"),
        Index("ix_timetables_school_class_id", "school_class_id"),
        Index("ix_timetables_section_id", "section_id"),
        Index("ix_timetables_academic_term_id", "academic_term_id"),
        Index("ix_timetables_status", "status"),
    )

    # ------------------------------------------------------------------
    # Foreign Keys
    # ------------------------------------------------------------------

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

    school_class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("school_classes.id", ondelete="CASCADE"),
        nullable=False,
    )

    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
    )

    academic_term_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_terms.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Attributes
    # ------------------------------------------------------------------

    status: Mapped[TimetableStatus] = mapped_column(
        Enum(TimetableStatus, name="timetable_status", create_constraint=False),
        nullable=False,
        default=TimetableStatus.DRAFT,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    school: Mapped["School"] = orm_relationship()
    academic_year: Mapped["AcademicYear"] = orm_relationship()
    school_class: Mapped["SchoolClass"] = orm_relationship()
    section: Mapped["Section"] = orm_relationship()
    academic_term: Mapped["AcademicTerm | None"] = orm_relationship()

    entries: Mapped[list["TimetableEntry"]] = orm_relationship(
        back_populates="timetable",
        cascade="all, delete-orphan",
    )
