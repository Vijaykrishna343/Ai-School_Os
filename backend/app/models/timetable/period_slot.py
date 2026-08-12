from __future__ import annotations

import uuid
from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import (
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.timetable import PeriodType
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.school.school import School


class PeriodSlot(CommonModel):
    """
    Represents a named time period in a school's daily schedule
    (e.g. Period 1: 08:30–09:15, Lunch: 12:30–13:00).
    """

    __tablename__ = "period_slots"

    __table_args__ = (
        Index(
            "uq_period_slot_order",
            "school_id",
            "display_order",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
        Index("ix_period_slots_school_id", "school_id"),
    )

    # ------------------------------------------------------------------
    # Foreign Key
    # ------------------------------------------------------------------

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Period Slot Details
    # ------------------------------------------------------------------

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    period_type: Mapped[PeriodType] = mapped_column(
        Enum(PeriodType, name="period_type", create_constraint=False),
        nullable=False,
        default=PeriodType.REGULAR,
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    school: Mapped["School"] = orm_relationship()
