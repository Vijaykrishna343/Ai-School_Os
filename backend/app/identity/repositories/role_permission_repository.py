from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.identity.models.role_permission import IdentityRolePermission


class IdentityRolePermissionRepository:
    """
    Repository for Role ↔ Permission assignments database operations.
    """

    # ------------------------------------------------------------------
    # Create Methods
    # ------------------------------------------------------------------

    def assign_permission(
        self,
        db: Session,
        role_id: UUID,
        permission_id: UUID,
    ) -> IdentityRolePermission:
        """
        Assign a permission to a role.
        """
        assignment = IdentityRolePermission(
            role_id=role_id,
            permission_id=permission_id,
        )

        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        return assignment

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_permissions(
        self,
        db: Session,
        role_id: UUID,
    ) -> list[IdentityRolePermission]:
        """
        Retrieve all permission assignments for a role.
        """
        stmt = (
            select(IdentityRolePermission)
            .where(
                IdentityRolePermission.role_id == role_id,
            )
        )

        return list(db.scalars(stmt))

    # ------------------------------------------------------------------
    # Delete Methods
    # ------------------------------------------------------------------

    def remove_permission(
        self,
        db: Session,
        role_id: UUID,
        permission_id: UUID,
    ) -> None:
        """
        Remove a permission assignment from a role.
        """
        stmt = delete(IdentityRolePermission).where(
            IdentityRolePermission.role_id == role_id,
            IdentityRolePermission.permission_id == permission_id,
        )

        db.execute(stmt)
        db.commit()

    # ------------------------------------------------------------------
    # Existence Methods
    # ------------------------------------------------------------------

    def permission_exists(
        self,
        db: Session,
        role_id: UUID,
        permission_id: UUID,
    ) -> bool:
        """
        Check whether a permission assignment exists for a role.
        """
        stmt = select(IdentityRolePermission).where(
            IdentityRolePermission.role_id == role_id,
            IdentityRolePermission.permission_id == permission_id,
        )

        return db.scalar(stmt) is not None


role_permission_repository = IdentityRolePermissionRepository()
