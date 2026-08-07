from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Index,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship as orm_relationship,
)

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.identity.models.role import IdentityRole


class IdentityPermission(CommonModel):
    """
    Represents a permission that can be assigned to roles.

    Examples:
        student.create
        student.update
        attendance.mark
        fee.collect
    """

    __tablename__ = "identity_permissions"

    __table_args__ = (
        Index("ix_identity_permissions_name", "name"),
        Index("ix_identity_permissions_module", "module"),
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    module: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    roles: Mapped[list["IdentityRole"]] = orm_relationship(
        secondary="identity_role_permissions",
        back_populates="permissions",
    )