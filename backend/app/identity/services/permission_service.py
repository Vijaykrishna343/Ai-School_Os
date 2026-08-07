from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
)
from app.identity.models.permission import IdentityPermission
from app.identity.repositories import permission_repository
from app.identity.schemas.permission import (
    PermissionCreate,
    PermissionUpdate,
)


class IdentityPermissionService:
    """
    Business logic for Permissions.
    """

    def create_permission(
        self,
        db: Session,
        data: PermissionCreate,
    ) -> IdentityPermission:

        if permission_repository.exists_by_name(
            db,
            data.name,
        ):
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

        return permission_repository.create(
            db,
            permission,
        )

    def get_permission(
        self,
        db: Session,
        permission_id: UUID,
    ) -> IdentityPermission:

        permission = permission_repository.get_by_id(
            db,
            permission_id,
        )

        if permission is None:
            raise NotFoundException(
                "Permission",
                str(permission_id),
            )

        return permission

    def list_permissions(
        self,
        db: Session,
    ) -> list[IdentityPermission]:

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

        return permission_repository.update(
            db,
            permission,
        )

    def delete_permission(
        self,
        db: Session,
        permission_id: UUID,
    ) -> None:

        permission = self.get_permission(
            db,
            permission_id,
        )

        permission_repository.delete(
            db,
            permission,
        )


permission_service = IdentityPermissionService()