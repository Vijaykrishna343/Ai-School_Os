from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.identity.models.user_role import IdentityUserRole


class IdentityUserRoleRepository:
    """
    Repository for User ↔ Role assignments database operations.
    """

    # ------------------------------------------------------------------
    # Create Methods
    # ------------------------------------------------------------------

    def assign_role(
        self,
        db: Session,
        user_id: UUID,
        role_id: UUID,
    ) -> IdentityUserRole:
        """
        Assign a role to a user.
        """
        assignment = IdentityUserRole(
            user_id=user_id,
            role_id=role_id,
        )

        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        return assignment

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_roles(
        self,
        db: Session,
        user_id: UUID,
    ) -> list[IdentityUserRole]:
        """
        Retrieve all role assignments for a user.
        """
        stmt = (
            select(IdentityUserRole)
            .where(
                IdentityUserRole.user_id == user_id,
            )
        )

        return list(db.scalars(stmt))

    # ------------------------------------------------------------------
    # Delete Methods
    # ------------------------------------------------------------------

    def remove_role(
        self,
        db: Session,
        user_id: UUID,
        role_id: UUID,
    ) -> None:
        """
        Remove a role assignment from a user.
        """
        stmt = delete(IdentityUserRole).where(
            IdentityUserRole.user_id == user_id,
            IdentityUserRole.role_id == role_id,
        )

        db.execute(stmt)
        db.commit()

    # ------------------------------------------------------------------
    # Existence Methods
    # ------------------------------------------------------------------

    def role_exists(
        self,
        db: Session,
        user_id: UUID,
        role_id: UUID,
    ) -> bool:
        """
        Check whether a role assignment exists for a user.
        """
        stmt = select(IdentityUserRole).where(
            IdentityUserRole.user_id == user_id,
            IdentityUserRole.role_id == role_id,
        )

        return db.scalar(stmt) is not None


user_role_repository = IdentityUserRoleRepository()