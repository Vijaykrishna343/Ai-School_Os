from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.identity.models.role_permission import IdentityRolePermission


class IdentityRolePermissionRepository:
    """
    Repository for Role ↔ Permission assignments.
    """

    def assign_permission(
        self,
        db: Session,
        role_id: UUID,
        permission_id: UUID,
    ) -> IdentityRolePermission:
        assignment = IdentityRolePermission(
            role_id=role_id,
            permission_id=permission_id,
        )

        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        return assignment

    def remove_permission(
        self,
        db: Session,
        role_id: UUID,
        permission_id: UUID,
    ) -> None:

        stmt = delete(IdentityRolePermission).where(
            IdentityRolePermission.role_id == role_id,
            IdentityRolePermission.permission_id == permission_id,
        )

        db.execute(stmt)
        db.commit()

    def permission_exists(
        self,
        db: Session,
        role_id: UUID,
        permission_id: UUID,
    ) -> bool:

        stmt = select(IdentityRolePermission).where(
            IdentityRolePermission.role_id == role_id,
            IdentityRolePermission.permission_id == permission_id,
        )

        return db.scalar(stmt) is not None

    def get_permissions(
        self,
        db: Session,
        role_id: UUID,
    ) -> list[IdentityRolePermission]:

        stmt = (
            select(IdentityRolePermission)
            .where(
                IdentityRolePermission.role_id == role_id,
            )
        )

        return list(db.scalars(stmt).all())


role_permission_repository = IdentityRolePermissionRepository()
