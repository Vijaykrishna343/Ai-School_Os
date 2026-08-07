from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.identity.models.permission import IdentityPermission
    from app.identity.models.user import IdentityUser
    from app.models.school import School


class IdentityRole(CommonModel):
    """
    Represents a role within a school.

    Roles determine what an authenticated user
    is allowed to do inside a specific school.

    System roles (is_system=True) are provided
    by the platform and cannot be modified.

    School-specific roles can be created by
    School Administrators.
    """

    __tablename__ = "identity_roles"

    __table_args__ = (
        Index("ix_identity_roles_school_id", "school_id"),
        Index("ix_identity_roles_name", "name"),
        UniqueConstraint(
            "school_id",
            "name",
            name="uq_identity_roles_school_name",
        ),
    )

    school_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "schools.id",
            ondelete="CASCADE",
        ),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    school: Mapped["School"] = orm_relationship(
        back_populates="roles",
    )

    users: Mapped[list["IdentityUser"]] = orm_relationship(
        secondary="identity_user_roles",
        back_populates="roles",
    )

    permissions: Mapped[list["IdentityPermission"]] = orm_relationship(
        secondary="identity_role_permissions",
        back_populates="roles",
    )