from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.identity.models.user import IdentityUser


class IdentityBootstrapState(CommonModel):
    """
    Tracks durable platform and tenant bootstrap/setup completion.

    Ensures that unauthenticated bootstrap creation is a strictly one-time,
    irreversible operation that does NOT reopen even if all active users
    are later deactivated, deleted, or suspended.
    """

    __tablename__ = "identity_bootstrap_states"

    scope: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        default="platform",
    )

    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "identity_users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    completed_by: Mapped[IdentityUser | None] = orm_relationship(
        "IdentityUser",
        foreign_keys=[completed_by_id],
        lazy="select",
    )
