from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    BadRequestException,
    NotFoundException,
)
from app.identity.models.role import IdentityRole
from app.identity.repositories import (
    permission_repository,
    role_repository,
)
from app.identity.schemas.role import (
    RoleCreate,
    RoleUpdate,
)


class IdentityRoleService:
    """
    Business logic for Roles.
    """

    def create_role(
        self,
        db: Session,
        role_data: RoleCreate,
    ) -> IdentityRole:

        if role_repository.exists_by_name(
            db=db,
            school_id=role_data.school_id,
            name=role_data.name,
        ):
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

        return role_repository.create(
            db,
            role,
        )

    def get_role(
        self,
        db: Session,
        role_id: UUID,
    ) -> IdentityRole:

        role = role_repository.get_by_id(
            db,
            role_id,
        )

        if role is None:
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

        return role_repository.get_school_roles(
            db,
            school_id,
        )

    def list_system_roles(
        self,
        db: Session,
    ) -> list[IdentityRole]:

        return role_repository.get_system_roles(
            db,
        )

    def update_role(
        self,
        db: Session,
        role_id: UUID,
        data: RoleUpdate,
    ) -> IdentityRole:

        role = self.get_role(
            db,
            role_id,
        )

        if role.is_system:
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

        return role_repository.update(
            db,
            role,
        )

    def delete_role(
        self,
        db: Session,
        role_id: UUID,
    ) -> None:

        role = self.get_role(
            db,
            role_id,
        )

        if role.is_system:
            raise BadRequestException(
                "System roles cannot be deleted."
            )

        role_repository.delete(
            db,
            role,
        )

    def assign_permission(
        self,
        db: Session,
        role_id: UUID,
        permission_id: UUID,
    ) -> IdentityRole:

        role = self.get_role(
            db,
            role_id,
        )

        permission = permission_repository.get_by_id(
            db,
            permission_id,
        )

        if permission is None:
            raise NotFoundException(
                "Permission",
                str(permission_id),
            )

        if permission not in role.permissions:
            role.permissions.append(permission)

        return role_repository.update(
            db,
            role,
        )

    def remove_permission(
        self,
        db: Session,
        role_id: UUID,
        permission_id: UUID,
    ) -> IdentityRole:

        role = self.get_role(
            db,
            role_id,
        )

        role.permissions = [
            permission
            for permission in role.permissions
            if permission.id != permission_id
        ]

        return role_repository.update(
            db,
            role,
        )


role_service = IdentityRoleService()