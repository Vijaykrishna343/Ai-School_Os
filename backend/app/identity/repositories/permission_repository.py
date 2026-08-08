from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.identity.models.permission import IdentityPermission
from app.repositories.base import BaseRepository


class IdentityPermissionRepository(
    BaseRepository[IdentityPermission]
):
    """
    Repository for Identity Permissions database operations.
    """

    def __init__(self) -> None:
        """
        Initialize IdentityPermissionRepository with IdentityPermission model.
        """
        super().__init__(IdentityPermission)

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_by_name(
        self,
        db: Session,
        name: str,
    ) -> IdentityPermission | None:
        """
        Retrieve an active permission by name (case-insensitive).
        """
        stmt = (
            select(IdentityPermission)
            .where(
                func.lower(IdentityPermission.name) == name.lower(),
                IdentityPermission.is_deleted.is_(False),
            )
        )

        return db.scalar(stmt)

    def get_by_module(
        self,
        db: Session,
        module: str,
    ) -> list[IdentityPermission]:
        """
        Retrieve active permissions belonging to a specific module.
        """
        stmt = (
            select(IdentityPermission)
            .where(
                func.lower(IdentityPermission.module) == module.lower(),
                IdentityPermission.is_deleted.is_(False),
            )
            .order_by(
                IdentityPermission.action,
            )
        )

        return list(db.scalars(stmt))

    # ------------------------------------------------------------------
    # Existence Methods
    # ------------------------------------------------------------------

    def exists_by_name(
        self,
        db: Session,
        name: str,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check whether an active permission exists with the given name, optionally excluding an ID.
        """
        stmt = (
            select(IdentityPermission)
            .where(
                func.lower(IdentityPermission.name) == name.lower(),
                IdentityPermission.is_deleted.is_(False),
            )
        )

        if exclude_id is not None:
            stmt = stmt.where(
                IdentityPermission.id != exclude_id,
            )

        return db.scalar(stmt) is not None


permission_repository = (
    IdentityPermissionRepository()
)