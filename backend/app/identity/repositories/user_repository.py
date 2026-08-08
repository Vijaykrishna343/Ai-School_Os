from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.identity.models.user import IdentityUser
from app.repositories.base import BaseRepository


class IdentityUserRepository(BaseRepository[IdentityUser]):
    """
    Repository for Identity Users database operations.
    """

    def __init__(self) -> None:
        """
        Initialize IdentityUserRepository with IdentityUser model.
        """
        super().__init__(IdentityUser)

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_by_id(
        self,
        db: Session,
        user_id: UUID,
    ) -> IdentityUser | None:
        """
        Retrieve an active identity user by primary ID.
        """
        stmt = (
            select(IdentityUser)
            .where(
                IdentityUser.id == user_id,
                IdentityUser.is_deleted.is_(False),
            )
        )

        return db.scalar(stmt)

    def get_by_email(
        self,
        db: Session,
        school_id: UUID,
        email: str,
    ) -> IdentityUser | None:
        """
        Retrieve an active identity user by school ID and email (case-insensitive).
        """
        stmt = (
            select(IdentityUser)
            .where(
                IdentityUser.school_id == school_id,
                func.lower(IdentityUser.email) == email.lower(),
                IdentityUser.is_deleted.is_(False),
            )
        )

        return db.scalar(stmt)

    # ------------------------------------------------------------------
    # Update Methods
    # ------------------------------------------------------------------

    def update_last_login(
        self,
        db: Session,
        user: IdentityUser,
    ) -> None:
        """
        Update the last login timestamp for an identity user.
        """
        user.last_login = datetime.now(timezone.utc)
        db.commit()

    # ------------------------------------------------------------------
    # Delete Methods
    # ------------------------------------------------------------------

    def soft_delete(
        self,
        db: Session,
        user: IdentityUser,
    ) -> None:
        """
        Soft delete an identity user entity.
        """
        user.soft_delete()
        db.commit()

    # ------------------------------------------------------------------
    # Existence & Count Methods
    # ------------------------------------------------------------------

    def exists_by_email(
        self,
        db: Session,
        school_id: UUID,
        email: str,
    ) -> bool:
        """
        Check whether an active user exists with the given email for a school.
        """
        return (
            self.get_by_email(db, school_id, email)
            is not None
        )

    def exists_by_username(
        self,
        db: Session,
        school_id: UUID,
        username: str,
    ) -> bool:
        """
        Check whether an active user exists with the given username for a school.
        """
        stmt = (
            select(IdentityUser)
            .where(
                IdentityUser.school_id == school_id,
                func.lower(IdentityUser.username) == username.lower(),
                IdentityUser.is_deleted.is_(False),
            )
        )

        return db.scalar(stmt) is not None

    def count_by_school(
        self,
        db: Session,
        school_id: UUID,
    ) -> int:
        """
        Count active identity users belonging to a school.
        """
        stmt = (
            select(func.count(IdentityUser.id))
            .where(
                IdentityUser.school_id == school_id,
                IdentityUser.is_deleted.is_(False),
            )
        )
        return db.scalar(stmt) or 0


identity_user_repository = IdentityUserRepository()