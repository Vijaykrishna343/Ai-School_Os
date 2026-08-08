from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    BadRequestException,
    NotFoundException,
)
from app.common.logger.logger import get_logger
from app.identity.models.role import IdentityRole
from app.identity.repositories import (
    permission_repository,
    role_repository,
)
from app.identity.schemas.role import (
    RoleCreate,
    RoleUpdate,
)

logger = get_logger(__name__)


class IdentityRoleService:
    """
    Business logic for Roles.
    """

    def create_role(
        self,
        db: Session,
        role_data: RoleCreate,
    ) -> IdentityRole:
        """
        Create a new role.
        """
        logger.info(
            "Creating role '%s' for school ID: %s",
            role_data.name,
            role_data.school_id,
        )

        if role_repository.exists_by_name(
            db=db,
            school_id=role_data.school_id,
            name=role_data.name,
        ):
            logger.warning(
                "Validation failure: Role name '%s' already exists for school ID: %s",
                role_data.name,
                role_data.school_id,
            )
            raise AlreadyExistsException(
                "Role",
                role_data.name,
            )

        role = IdentityRole(
            school_id=role_data.school_id,
            name=role_data.name,
            description=role_data.description,
            is_system=False,
        )

        created = role_repository.create(
            db,
            role,
        )
        logger.info("Role '%s' created successfully with ID: %s", created.name, created.id)
        return created

    def get_role(
        self,
        db: Session,
        role_id: UUID,
    ) -> IdentityRole:
        """
        Get a role by ID.
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

        return role

    def list_school_roles(
        self,
        db: Session,
        school_id: UUID,
    ) -> list[IdentityRole]:
        """
        List all roles for a school.
        """
        return role_repository.get_school_roles(
            db,
            school_id,
        )

    def list_system_roles(
        self,
        db: Session,
    ) -> list[IdentityRole]:
        """
        List all system roles.
        """
        return role_repository.get_system_roles(
            db,
        )

    def update_role(
        self,
        db: Session,
        role_id: UUID,
        data: RoleUpdate,
    ) -> IdentityRole:
        """
        Update an existing role.
        """
        logger.info("Updating role ID: %s", role_id)
        role = self.get_role(
            db,
            role_id,
        )

        if role.is_system:
            logger.warning("Validation failure: Attempted to modify system role ID: %s", role_id)
            raise BadRequestException(
                "System roles cannot be modified."
            )

        updates = data.model_dump(
            exclude_unset=True,
        )

        if (
            "name" in updates
            and role_repository.exists_by_name(
                db=db,
                school_id=role.school_id,
                name=updates["name"],
                exclude_id=role.id,
            )
        ):
            logger.warning(
                "Validation failure: Role name '%s' already exists for school ID: %s",
                updates["name"],
                role.school_id,
            )
            raise AlreadyExistsException(
                "Role",
                updates["name"],
            )

        for field, value in updates.items():
            setattr(
                role,
                field,
                value,
            )

        updated = role_repository.update(
            db,
            role,
        )
        logger.info("Role ID: %s updated successfully", role_id)
        return updated

    def delete_role(
        self,
        db: Session,
        role_id: UUID,
    ) -> None:
        """
        Soft delete a role.
        """
        logger.info("Soft deleting role ID: %s", role_id)
        role = self.get_role(
            db,
            role_id,
        )

        if role.is_system:
            logger.warning("Validation failure: Attempted to delete system role ID: %s", role_id)
            raise BadRequestException(
                "System roles cannot be deleted."
            )

        role_repository.delete(
            db,
            role,
        )
        logger.info("Role ID: %s soft deleted successfully", role_id)

    def assign_permission(
        self,
        db: Session,
        role_id: UUID,
        permission_id: UUID,
    ) -> IdentityRole:
        """
        Assign a permission to a role.
        """
        logger.info("Assigning permission ID %s to role ID %s", permission_id, role_id)
        role = self.get_role(
            db,
            role_id,
        )

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

        if permission not in role.permissions:
            role.permissions.append(permission)

        updated = role_repository.update(
            db,
            role,
        )
        logger.info("Assigned permission ID %s to role ID %s successfully", permission_id, role_id)
        return updated

    def remove_permission(
        self,
        db: Session,
        role_id: UUID,
        permission_id: UUID,
    ) -> IdentityRole:
        """
        Remove a permission from a role.
        """
        logger.info("Removing permission ID %s from role ID %s", permission_id, role_id)
        role = self.get_role(
            db,
            role_id,
        )

        role.permissions = [
            permission
            for permission in role.permissions
            if permission.id != permission_id
        ]

        updated = role_repository.update(
            db,
            role,
        )
        logger.info("Removed permission ID %s from role ID %s successfully", permission_id, role_id)
        return updated


role_service = IdentityRoleService()