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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.common.enums.admissions import AdmissionDecisionType
from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.identity.models.user import IdentityUser
    from app.models.admissions.admission_application import AdmissionApplication
    from app.models.school.school import School


class AdmissionDecision(CommonModel):
    """
    Formal record of an admission decision made for an application.
    """

    __tablename__ = "admission_decisions"

    __table_args__ = (
        Index("ix_admission_decisions_school_id", "school_id"),
        Index("ix_admission_decisions_application_id", "application_id"),
        Index("ix_admission_decisions_user_id", "decided_by_user_id"),
        Index("ix_admission_decisions_type", "decision_type"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admission_applications.id", ondelete="CASCADE"),
        nullable=False,
    )

    decision_type: Mapped[AdmissionDecisionType] = mapped_column(
        Enum(AdmissionDecisionType),
        nullable=False,
    )

    decided_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    comments: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    conditions: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    # Relationships
    school: Mapped[School] = orm_relationship(
        "School",
        foreign_keys=[school_id],
        lazy="select",
    )

    application: Mapped[AdmissionApplication] = orm_relationship(
        "AdmissionApplication",
        foreign_keys=[application_id],
        back_populates="decisions",
        lazy="select",
    )

    decided_by_user: Mapped[IdentityUser | None] = orm_relationship(
        "IdentityUser",
        foreign_keys=[decided_by_user_id],
        lazy="select",
    )
