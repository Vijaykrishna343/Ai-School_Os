from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.common_model import CommonModel


class IdentityPasswordResetToken(CommonModel):
    """
    Persisted password reset token record for single-use time-limited account recovery.
    Stores a cryptographic SHA-256 digest of the raw random reset token.
    """

    __tablename__ = "identity_password_reset_tokens"

    school_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "schools.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "identity_users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    requested_ip: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
