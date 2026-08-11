from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.grading.report_card import ReportCard
    from app.models.subject.subject import Subject


class ReportCardItemSnapshot(CommonModel):
    """
    Immutable subject-level evaluation snapshot inside a ReportCard.
    """

    __tablename__ = "report_card_item_snapshots"

    __table_args__ = (
        Index("ix_report_card_item_snapshots_report_card_id", "report_card_id"),
        Index("ix_report_card_item_snapshots_subject_id", "subject_id"),
    )

    report_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("report_cards.id", ondelete="CASCADE"),
        nullable=False,
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="RESTRICT"),
        nullable=False,
    )

    subject_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    subject_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    max_marks: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    obtained_marks: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    grade_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    grade_point: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    is_pass: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    report_card: Mapped["ReportCard"] = orm_relationship(
        back_populates="items",
    )

    subject: Mapped["Subject"] = orm_relationship()
