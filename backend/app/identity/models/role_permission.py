from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class IdentityRolePermission(Base):
    """
    Association table between roles and permissions.
    """

    __tablename__ = "identity_role_permissions"

    role_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "identity_roles.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    permission_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "identity_permissions.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )