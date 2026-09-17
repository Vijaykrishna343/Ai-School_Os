from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
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

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.identity.models.user import IdentityUser
    from app.models.admissions.admission_application import AdmissionApplication
    from app.models.school.school import School


class ApplicationStatusHistory(CommonModel):
    """
    Audit log of lifecycle status changes for an admission application.
    """

    __tablename__ = "application_status_history"

    __table_args__ = (
        Index("ix_app_status_hist_school_id", "school_id"),
        Index("ix_app_status_hist_application_id", "application_id"),
        Index("ix_app_status_hist_user_id", "changed_by_user_id"),
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

    old_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    new_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
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
        back_populates="status_history",
        lazy="select",
    )

    changed_by_user: Mapped[IdentityUser | None] = orm_relationship(
        "IdentityUser",
        foreign_keys=[changed_by_user_id],
        lazy="select",
    )
