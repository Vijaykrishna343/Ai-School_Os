from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
)
from app.identity.repositories import (
    permission_repository,
    role_repository,
    role_permission_repository,
)


class IdentityRolePermissionService:
    """
    Business logic for Role ↔ Permission assignments.
    """

    def assign_permission(
        self,
        db: Session,
        role_id: UUID,
        permission_id: UUID,
    ):
        # -------------------------------
        # Validate Role
        # -------------------------------

        role = role_repository.get_by_id(
            db,
            role_id,
        )

        if role is None:
            raise NotFoundException(
                "Role",
                str(role_id),
            )

        # -------------------------------
        # Validate Permission
        # -------------------------------

        permission = permission_repository.get_by_id(
            db,
            permission_id,
        )

        if permission is None:
            raise NotFoundException(
                "Permission",
                str(permission_id),
            )

        # -------------------------------
        # Duplicate Check
        # -------------------------------

        if role_permission_repository.permission_exists(
            db,
            role_id,
            permission_id,
        ):
            raise AlreadyExistsException(
                "Permission Assignment",
            )

        # -------------------------------
        # Assign
        # -------------------------------

        return role_permission_repository.assign_permission(
            db,
            role_id,
            permission_id,
        )

    def remove_permission(
        self,
        db: Session,
        role_id: UUID,
        permission_id: UUID,
    ):
        if not role_permission_repository.permission_exists(
            db,
            role_id,
            permission_id,
        ):
            raise NotFoundException(
                "Permission Assignment",
            )

        role_permission_repository.remove_permission(
            db,
            role_id,
            permission_id,
        )

    def get_permissions(
        self,
        db: Session,
        role_id: UUID,
    ):
        role = role_repository.get_by_id(
            db,
            role_id,
        )

        if role is None:
            raise NotFoundException(
                "Role",
                str(role_id),
            )

        return role_permission_repository.get_permissions(
            db,
            role_id,
        )


role_permission_service = IdentityRolePermissionService()
