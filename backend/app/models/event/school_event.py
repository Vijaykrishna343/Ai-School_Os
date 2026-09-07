from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.common_model import CommonModel


class SchoolEvent(CommonModel):
    """
    School Event & Calendar Model.
    Supports targeted audience scopes, date-range filtering, lifecycle statuses,
    and multi-tenant isolation.
    """
    __tablename__ = "school_events"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    academic_year_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="HOLIDAY",
        index=True,
    )  # HOLIDAY, PTM, EXAM, SPORTS, ANNUAL_DAY, CULTURAL, FLAG_HOISTING, SCHOOL_FUNCTION, MEETING, WORKSHOP, COMPETITION, OTHER
    start_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    end_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    venue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    organizer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    audience_scope: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="SCHOOL",
        index=True,
    )  # SCHOOL, TEACHERS, PARENTS, STUDENTS, CLASS, SECTION
    target_class_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("school_classes.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_section_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="DRAFT",
        index=True,
    )  # DRAFT, PUBLISHED, CANCELLED, COMPLETED

    __table_args__ = (
        Index("idx_school_event_dates", "school_id", "start_datetime", "end_datetime"),
        Index("idx_school_event_audience", "school_id", "audience_scope", "status"),
    )
