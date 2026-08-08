from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.identity.models.role import IdentityRole
from app.repositories.base import BaseRepository


class IdentityRoleRepository(BaseRepository[IdentityRole]):
    """
    Repository for Identity Roles database operations.
    """

    def __init__(self) -> None:
        """
        Initialize IdentityRoleRepository with IdentityRole model.
        """
        super().__init__(IdentityRole)

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_by_name(
        self,
        db: Session,
        school_id: UUID | None,
        name: str,
    ) -> IdentityRole | None:
        """
        Retrieve an active role by school ID and name (case-insensitive).
        """
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
        """
        Retrieve all active system roles ordered by name.
        """
        stmt = (
            select(IdentityRole)
            .where(
                IdentityRole.is_system.is_(True),
                IdentityRole.is_deleted.is_(False),
            )
            .order_by(IdentityRole.name)
        )

        return list(db.scalars(stmt))

    def get_school_roles(
        self,
        db: Session,
        school_id: UUID,
    ) -> list[IdentityRole]:
        """
        Retrieve all active roles for a specific school ordered by name.
        """
        stmt = (
            select(IdentityRole)
            .where(
                IdentityRole.school_id == school_id,
                IdentityRole.is_deleted.is_(False),
            )
            .order_by(IdentityRole.name)
        )

        return list(db.scalars(stmt))

    # ------------------------------------------------------------------
    # Existence Methods
    # ------------------------------------------------------------------

    def exists_by_name(
        self,
        db: Session,
        school_id: UUID | None,
        name: str,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check whether an active role exists with the given name, optionally excluding an ID.
        """
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