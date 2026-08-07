from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.identity.models.user_role import IdentityUserRole


class IdentityUserRoleRepository:
    """
    Repository for User ↔ Role assignments.
    """

    def assign_role(
        self,
        db: Session,
        user_id: UUID,
        role_id: UUID,
    ) -> IdentityUserRole:
        assignment = IdentityUserRole(
            user_id=user_id,
            role_id=role_id,
        )

        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        return assignment

    def remove_role(
        self,
        db: Session,
        user_id: UUID,
        role_id: UUID,
    ) -> None:

        stmt = delete(IdentityUserRole).where(
            IdentityUserRole.user_id == user_id,
            IdentityUserRole.role_id == role_id,
        )

        db.execute(stmt)
        db.commit()

    def role_exists(
        self,
        db: Session,
        user_id: UUID,
        role_id: UUID,
    ) -> bool:

        stmt = select(IdentityUserRole).where(
            IdentityUserRole.user_id == user_id,
            IdentityUserRole.role_id == role_id,
        )

        return db.scalar(stmt) is not None

    def get_roles(
        self,
        db: Session,
        user_id: UUID,
    ) -> list[IdentityUserRole]:

        stmt = (
            select(IdentityUserRole)
            .where(
                IdentityUserRole.user_id == user_id,
            )
        )

        return list(db.scalars(stmt).all())


user_role_repository = IdentityUserRoleRepository()