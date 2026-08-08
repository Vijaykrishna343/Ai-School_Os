from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
)
from app.common.logger.logger import get_logger
from app.identity.repositories import (
    permission_repository,
    role_permission_repository,
    role_repository,
)

logger = get_logger(__name__)


class IdentityRolePermissionService:
    """
    Business logic for Role ↔ Permission assignments.
    """

    # ------------------------------------------------------------------
    # Create Methods
    # ------------------------------------------------------------------

    def assign_permission(
        self,
        db: Session,
        role_id: UUID,
        permission_id: UUID,
    ) -> Any:
        """
        Assign a permission to a role.
        """
        logger.info("Assigning permission ID %s to role ID %s", permission_id, role_id)

        # -------------------------------
        # Validate Role
        # -------------------------------

        role = role_repository.get_by_id(
            db,
            role_id,
        )

        if role is None:
            logger.warning("Validation failure: Role ID '%s' not found for permission assignment", role_id)
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
            logger.warning("Validation failure: Permission ID '%s' not found for role assignment", permission_id)
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
            logger.warning("Validation failure: Permission ID %s already assigned to role ID %s", permission_id, role_id)
            raise AlreadyExistsException(
                "Permission Assignment",
            )

        # -------------------------------
        # Assign
        # -------------------------------

        result = role_permission_repository.assign_permission(
            db,
            role_id,
            permission_id,
        )
        logger.info("Permission ID %s assigned to role ID %s successfully", permission_id, role_id)
        return result

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_permissions(
        self,
        db: Session,
        role_id: UUID,
    ) -> Any:
        """
        Get all assigned permissions for a role.
        """
        role = role_repository.get_by_id(
            db,
            role_id,
        )

        if role is None:
            logger.warning("Validation failure: Role ID '%s' not found", role_id)
            raise NotFoundException(
                "Role",
                str(role_id),
            )

        return role_permission_repository.get_permissions(
            db,
            role_id,
        )

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
        Remove a permission from a role.
        """
        logger.info("Removing permission ID %s from role ID %s", permission_id, role_id)
        if not role_permission_repository.permission_exists(
            db,
            role_id,
            permission_id,
        ):
            logger.warning("Validation failure: Permission assignment between role ID %s and permission ID %s not found", role_id, permission_id)
            raise NotFoundException(
                "Permission Assignment",
            )

        role_permission_repository.remove_permission(
            db,
            role_id,
            permission_id,
        )
        logger.info("Permission ID %s removed from role ID %s successfully", permission_id, role_id)


role_permission_service = IdentityRolePermissionService()
