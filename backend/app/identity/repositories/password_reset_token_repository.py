from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.identity.models.password_reset_token import IdentityPasswordResetToken
from app.repositories.base import BaseRepository


class IdentityPasswordResetTokenRepository(BaseRepository[IdentityPasswordResetToken]):
    """
    Repository for Identity Password Reset Token database operations.
    """

    def __init__(self) -> None:
        super().__init__(IdentityPasswordResetToken)

    def create_token_record(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        requested_ip: str | None = None,
        commit: bool = True,
    ) -> IdentityPasswordResetToken:
        """
        Record a new password reset token in the database.
        """
        record = IdentityPasswordResetToken(
            school_id=school_id,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            requested_ip=requested_ip,
        )
        db.add(record)
        if commit:
            db.commit()
            db.refresh(record)
        else:
            db.flush()
        return record

    def get_by_token_hash(
        self,
        db: Session,
        token_hash: str,
    ) -> IdentityPasswordResetToken | None:
        """
        Retrieve a password reset token record by its SHA-256 hash digest.
        """
        stmt = select(IdentityPasswordResetToken).where(
            IdentityPasswordResetToken.token_hash == token_hash,
            IdentityPasswordResetToken.is_deleted.is_(False),
        )
        return db.scalar(stmt)

    def get_by_token_hash_for_update(
        self,
        db: Session,
        token_hash: str,
    ) -> IdentityPasswordResetToken | None:
        """
        Retrieve a password reset token record and acquire an exclusive row lock (FOR UPDATE).
        """
        stmt = (
            select(IdentityPasswordResetToken)
            .where(
                IdentityPasswordResetToken.token_hash == token_hash,
                IdentityPasswordResetToken.is_deleted.is_(False),
            )
            .with_for_update()
        )
        return db.scalar(stmt)

    def mark_used(
        self,
        db: Session,
        record: IdentityPasswordResetToken,
        commit: bool = True,
    ) -> IdentityPasswordResetToken:
        """
        Mark a password reset token as consumed.
        """
        record.used_at = datetime.now(timezone.utc)
        if commit:
            db.commit()
            db.refresh(record)
        else:
            db.flush()
        return record


identity_password_reset_token_repository = IdentityPasswordResetTokenRepository()
