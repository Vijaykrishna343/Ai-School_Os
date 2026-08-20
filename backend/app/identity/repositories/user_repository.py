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

    def list_users(
        self,
        db: Session,
        school_id: UUID | None = None,
        email: str | None = None,
        username: str | None = None,
        first_name: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[IdentityUser], int]:
        """
        Get filtered, paginated list of users for a school.
        """
        stmt = select(IdentityUser).where(IdentityUser.is_deleted.is_(False))

        if school_id is not None:
            stmt = stmt.where(IdentityUser.school_id == school_id)
        if email:
            stmt = stmt.where(func.lower(IdentityUser.email).contains(email.lower()))
        if username:
            stmt = stmt.where(func.lower(IdentityUser.username).contains(username.lower()))
        if first_name:
            stmt = stmt.where(func.lower(IdentityUser.first_name).contains(first_name.lower()))
        if is_active is not None:
            stmt = stmt.where(IdentityUser.is_active.is_(is_active))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        stmt = stmt.order_by(IdentityUser.first_name).offset((page - 1) * page_size).limit(page_size)
        items = list(db.scalars(stmt).all())

        return items, total


identity_user_repository = IdentityUserRepository()