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
    from app.identity.models.role import IdentityRole
    from app.models.school import School


class IdentityUser(CommonModel):
    """
    Identity User Model.

    Handles authentication for every user in the system.

    Business entities like Teacher, Student,
    Parent, etc. will be linked to this model.
    """

    __tablename__ = "identity_users"

    school_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "schools.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="ACTIVE",
        nullable=False,
    )

    suspended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    suspension_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


    school: Mapped["School"] = orm_relationship(
        "School",
        back_populates="identity_users",
    )

    roles: Mapped[list["IdentityRole"]] = orm_relationship(
        secondary="identity_user_roles",
        back_populates="users",
    )

    @property
    def is_super_admin(self) -> bool:
        """
        Returns True if the user has active Super Admin role.
        """
        return any(
            role.name == "Super Admin" and not getattr(role, "is_deleted", False)
            for role in self.roles
        )