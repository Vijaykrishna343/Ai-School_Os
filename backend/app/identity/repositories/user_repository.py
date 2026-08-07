from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.identity.models.user import IdentityUser
from app.repositories.base import BaseRepository


class IdentityUserRepository(BaseRepository[IdentityUser]):
    """
    Repository for Identity Users.
    """

    def __init__(self):
        super().__init__(IdentityUser)

    def get_by_id(
        self,
        db: Session,
        user_id: UUID,
    ) -> IdentityUser | None:
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
        stmt = (
            select(IdentityUser)
            .where(
                IdentityUser.school_id == school_id,
                func.lower(IdentityUser.email) == email.lower(),
                IdentityUser.is_deleted.is_(False),
            )
        )

        return db.scalar(stmt)

    def exists_by_email(
        self,
        db: Session,
        school_id: UUID,
        email: str,
    ) -> bool:
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
        stmt = (
            select(IdentityUser)
            .where(
                IdentityUser.school_id == school_id,
                func.lower(IdentityUser.username)
                == username.lower(),
                IdentityUser.is_deleted.is_(False),
            )
        )

        return db.scalar(stmt) is not None

    def count_by_school(
        self,
        db: Session,
        school_id: UUID,
    ) -> int:
        stmt = (
            select(func.count(IdentityUser.id))
            .where(
                IdentityUser.school_id == school_id,
                IdentityUser.is_deleted.is_(False),
            )
        )
        return db.scalar(stmt) or 0

    def update_last_login(
        self,
        db: Session,
        user: IdentityUser,
    ) -> None:
        user.last_login = datetime.now(timezone.utc)
        db.commit()

    def soft_delete(
        self,
        db: Session,
        user: IdentityUser,
    ) -> None:
        user.soft_delete()
        db.commit()


identity_user_repository = IdentityUserRepository()