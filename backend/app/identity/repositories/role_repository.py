from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.identity.models.role import IdentityRole
from app.repositories.base import BaseRepository


class IdentityRoleRepository(BaseRepository[IdentityRole]):
    """
    Repository for Identity Roles.
    """

    def __init__(self):
        super().__init__(IdentityRole)

    def get_by_name(
        self,
        db: Session,
        school_id: UUID | None,
        name: str,
    ) -> IdentityRole | None:
        stmt = (
            select(IdentityRole)
            .where(
                IdentityRole.school_id == school_id,
                func.lower(IdentityRole.name) == name.lower(),
                IdentityRole.is_deleted.is_(False),
            )
        )

        return db.scalar(stmt)

    def get_system_roles(
        self,
        db: Session,
    ) -> list[IdentityRole]:
        stmt = (
            select(IdentityRole)
            .where(
                IdentityRole.is_system.is_(True),
                IdentityRole.is_deleted.is_(False),
            )
            .order_by(IdentityRole.name)
        )

        return list(db.scalars(stmt).all())

    def get_school_roles(
        self,
        db: Session,
        school_id: UUID,
    ) -> list[IdentityRole]:
        stmt = (
            select(IdentityRole)
            .where(
                IdentityRole.school_id == school_id,
                IdentityRole.is_deleted.is_(False),
            )
            .order_by(IdentityRole.name)
        )

        return list(db.scalars(stmt).all())

    def exists_by_name(
        self,
        db: Session,
        school_id: UUID | None,
        name: str,
        exclude_id: UUID | None = None,
    ) -> bool:
        stmt = (
            select(IdentityRole)
            .where(
                IdentityRole.school_id == school_id,
                func.lower(IdentityRole.name) == name.lower(),
                IdentityRole.is_deleted.is_(False),
            )
        )

        if exclude_id is not None:
            stmt = stmt.where(
                IdentityRole.id != exclude_id,
            )

        return db.scalar(stmt) is not None


role_repository = IdentityRoleRepository()