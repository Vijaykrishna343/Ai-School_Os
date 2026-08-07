from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class IdentityUserRole(Base):
    """
    Association table between users and roles.
    """

    __tablename__ = "identity_user_roles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "identity_users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    role_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "identity_roles.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )