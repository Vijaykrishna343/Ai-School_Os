from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
)
from app.common.logger.logger import get_logger
from app.identity.models.permission import IdentityPermission
from app.identity.repositories import permission_repository
from app.identity.schemas.permission import (
    PermissionCreate,
    PermissionUpdate,
)

logger = get_logger(__name__)


class IdentityPermissionService:
    """
    Business logic for Permissions.
    """

    def create_permission(
        self,
        db: Session,
        data: PermissionCreate,
    ) -> IdentityPermission:
        """
        Create a new permission.
        """
        logger.info("Creating permission '%s' for module '%s'", data.name, data.module)

        if permission_repository.exists_by_name(
            db,
            data.name,
        ):
            logger.warning("Validation failure: Permission name '%s' already exists", data.name)
            raise AlreadyExistsException(
                "Permission",
                data.name,
            )

        permission = IdentityPermission(
            name=data.name,
            description=data.description,
            module=data.module,
            action=data.action,
        )

        created = permission_repository.create(
            db,
            permission,
        )
        logger.info("Permission '%s' created successfully with ID: %s", created.name, created.id)
        return created

    def get_permission(
        self,
        db: Session,
        permission_id: UUID,
    ) -> IdentityPermission:
        """
        Get a permission by ID.
        """
        permission = permission_repository.get_by_id(
            db,
            permission_id,
        )

        if permission is None:
            logger.warning("Validation failure: Permission ID '%s' not found", permission_id)
            raise NotFoundException(
                "Permission",
                str(permission_id),
            )

        return permission

    def list_permissions(
        self,
        db: Session,
    ) -> list[IdentityPermission]:
        """
        List all permissions.
        """
        permissions, _, _ = (
            permission_repository.get_paginated(
                db=db,
                page=1,
                page_size=1000,
            )
        )

        return permissions

    def list_by_module(
        self,
        db: Session,
        module: str,
    ) -> list[IdentityPermission]:
        """
        List all permissions for a module.
        """
        return permission_repository.get_by_module(
            db,
            module,
        )

    def update_permission(
        self,
        db: Session,
        permission_id: UUID,
        data: PermissionUpdate,
    ) -> IdentityPermission:
        """
        Update an existing permission.
        """
        logger.info("Updating permission ID: %s", permission_id)
        permission = self.get_permission(
            db,
            permission_id,
        )

        updates = data.model_dump(
            exclude_unset=True,
        )

        if (
            "name" in updates
            and permission_repository.exists_by_name(
                db=db,
                name=updates["name"],
                exclude_id=permission.id,
            )
        ):
            logger.warning("Validation failure: Permission name '%s' already exists", updates["name"])
            raise AlreadyExistsException(
                "Permission",
                updates["name"],
            )

        for field, value in updates.items():
            setattr(
                permission,
                field,
                value,
            )

        updated = permission_repository.update(
            db,
            permission,
        )
        logger.info("Permission ID: %s updated successfully", permission_id)
        return updated

    def delete_permission(
        self,
        db: Session,
        permission_id: UUID,
    ) -> None:
        """
        Soft delete a permission.
        """
        logger.info("Soft deleting permission ID: %s", permission_id)
        permission = self.get_permission(
            db,
            permission_id,
        )

        permission_repository.delete(
            db,
            permission,
        )
        logger.info("Permission ID: %s soft deleted successfully", permission_id)


permission_service = IdentityPermissionService()