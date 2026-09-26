from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.identity.models.refresh_token import IdentityRefreshToken
from app.repositories.base import BaseRepository


class IdentityRefreshTokenRepository(BaseRepository[IdentityRefreshToken]):
    """
    Repository for Identity Refresh Token session and revocation operations.
    """

    def __init__(self) -> None:
        super().__init__(IdentityRefreshToken)

    def create_session(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        jti: str,
        expires_at: datetime,
        token_hash: str | None = None,
        commit: bool = True,
    ) -> IdentityRefreshToken:
        """
        Record a new refresh token session in the database.
        """
        session = IdentityRefreshToken(
            school_id=school_id,
            user_id=user_id,
            jti=jti,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
        )
        db.add(session)
        if commit:
            db.commit()
            db.refresh(session)
        else:
            db.flush()
        return session

    def get_by_jti(
        self,
        db: Session,
        jti: str,
    ) -> IdentityRefreshToken | None:
        """
        Retrieve a refresh token session by its unique JTI.
        """
        stmt = select(IdentityRefreshToken).where(
            IdentityRefreshToken.jti == jti,
            IdentityRefreshToken.is_deleted.is_(False),
        )
        return db.scalar(stmt)

    def get_by_jti_for_update(
        self,
        db: Session,
        jti: str,
    ) -> IdentityRefreshToken | None:
        """
        Retrieve a refresh token session by its unique JTI and acquire an exclusive row lock (FOR UPDATE).
        """
        stmt = (
            select(IdentityRefreshToken)
            .where(
                IdentityRefreshToken.jti == jti,
                IdentityRefreshToken.is_deleted.is_(False),
            )
            .with_for_update()
        )
        return db.scalar(stmt)

    def revoke_session(
        self,
        db: Session,
        session: IdentityRefreshToken,
        reason: str | None = None,
        commit: bool = True,
    ) -> IdentityRefreshToken:
        """
        Explicitly revoke an active refresh session.
        """
        session.is_revoked = True
        session.revoked_at = datetime.now(timezone.utc)
        if reason:
            session.revocation_reason = reason
        if commit:
            db.commit()
            db.refresh(session)
        else:
            db.flush()
        return session

    def revoke_by_jti(
        self,
        db: Session,
        jti: str,
        user_id: UUID | None = None,
        school_id: UUID | None = None,
        reason: str | None = None,
        commit: bool = True,
    ) -> IdentityRefreshToken | None:
        """
        Find and revoke a session matching jti (optionally scoped to user and school).
        """
        session = self.get_by_jti(db, jti)
        if session is None:
            return None

        if user_id and session.user_id != user_id:
            return None

        if school_id and session.school_id != school_id:
            return None

        return self.revoke_session(db, session, reason, commit=commit)

    def revoke_all_active_sessions_for_user(
        self,
        db: Session,
        user_id: UUID,
        school_id: UUID | None = None,
        reason: str = "PASSWORD_RESET",
        commit: bool = True,
    ) -> int:
        """
        Revoke all active refresh sessions for a specific user.
        """
        stmt = (
            select(IdentityRefreshToken)
            .where(
                IdentityRefreshToken.user_id == user_id,
                IdentityRefreshToken.is_revoked.is_(False),
                IdentityRefreshToken.is_deleted.is_(False),
            )
            .with_for_update()
        )
        if school_id is not None:
            stmt = stmt.where(IdentityRefreshToken.school_id == school_id)

        active_sessions = db.scalars(stmt).all()
        now = datetime.now(timezone.utc)
        count = 0
        for session in active_sessions:
            session.is_revoked = True
            session.revoked_at = now
            session.revocation_reason = reason
            count += 1

        if commit:
            db.commit()
        else:
            db.flush()
        return count


identity_refresh_token_repository = IdentityRefreshTokenRepository()
