from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.visitor import HostType, ReceptionInquiryStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.school.school import School
    from app.models.visitor.visitor import Visitor


class ReceptionInquiry(CommonModel):
    """
    Represents front-desk inquiries, appointments, and general reception log records.
    Enforces strict multi-tenant isolation via school_id.
    """

    __tablename__ = "reception_inquiries"

    __table_args__ = (
        Index("ix_reception_inquiries_school_id", "school_id"),
        Index("ix_reception_inquiries_visitor_id", "visitor_id"),
        Index("ix_reception_inquiries_status", "status"),
        Index("ix_reception_inquiries_school_status", "school_id", "status"),
        Index("ix_reception_inquiries_appointment", "school_id", "appointment_time"),
        Index("ix_reception_inquiries_host", "school_id", "host_type", "host_id"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    visitor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("visitors.id", ondelete="SET NULL"),
        nullable=True,
    )

    contact_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    contact_phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    contact_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    host_type: Mapped[HostType | None] = mapped_column(
        Enum(
            HostType,
            name="host_type",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=True,
    )

    host_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    appointment_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[ReceptionInquiryStatus] = mapped_column(
        Enum(
            ReceptionInquiryStatus,
            name="reception_inquiry_status",
            native_enum=True,
            validate_strings=True,
        ),
        default=ReceptionInquiryStatus.PENDING,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    school: Mapped["School"] = orm_relationship()
    visitor: Mapped["Visitor | None"] = orm_relationship(
        back_populates="inquiries"
    )
