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
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.visitor import HostType, IdProofType, VisitorStatus
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.school.school import School
    from app.models.visitor.reception_inquiry import ReceptionInquiry


class Visitor(CommonModel):
    """
    Represents a visitor record for campus entry, gate pass management, and visitor logs.
    Enforces strict multi-tenant isolation via school_id.
    """

    __tablename__ = "visitors"

    __table_args__ = (
        Index("ix_visitors_school_id", "school_id"),
        Index("ix_visitors_status", "status"),
        Index("ix_visitors_check_in_time", "check_in_time"),
        Index("ix_visitors_school_status", "school_id", "status"),
        Index("ix_visitors_school_phone", "school_id", "phone"),
        Index("ix_visitors_host", "school_id", "host_type", "host_id"),
        Index(
            "uq_visitor_school_pass_number",
            "school_id",
            "pass_number",
            unique=True,
            postgresql_where=text("is_deleted = false AND pass_number IS NOT NULL"),
            sqlite_where=text("is_deleted = 0 AND pass_number IS NOT NULL"),
        ),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    visitor_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    id_proof_type: Mapped[IdProofType | None] = mapped_column(
        Enum(
            IdProofType,
            name="id_proof_type",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=True,
    )

    id_proof_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    purpose: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
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

    check_in_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    check_out_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[VisitorStatus] = mapped_column(
        Enum(
            VisitorStatus,
            name="visitor_status",
            native_enum=True,
            validate_strings=True,
        ),
        default=VisitorStatus.EXPECTED,
        nullable=False,
    )

    pass_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    school: Mapped["School"] = orm_relationship()
    inquiries: Mapped[list["ReceptionInquiry"]] = orm_relationship(
        back_populates="visitor",
        cascade="all, delete-orphan",
    )
