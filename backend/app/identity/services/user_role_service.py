from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    BadRequestException,
    NotFoundException,
)
from app.identity.repositories import (
    identity_user_repository,
    role_repository,
    user_role_repository,
)


class IdentityUserRoleService:
    """
    Business logic for User ↔ Role assignments.
    """

    def assign_role(
        self,
        db: Session,
        user_id: UUID,
        role_id: UUID,
    ):
        # -------------------------------
        # Validate User
        # -------------------------------

        user = identity_user_repository.get_by_id(
            db,
            user_id,
        )

        if user is None:
            raise NotFoundException(
                "User",
                str(user_id),
            )

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
        # Multi-tenant Validation
        # -------------------------------

        if (
            role.school_id is not None
            and user.school_id != role.school_id
        ):
            raise BadRequestException(
                "User and Role belong to different schools."
            )

        # -------------------------------
        # Duplicate Check
        # -------------------------------

        if user_role_repository.role_exists(
            db,
            user_id,
            role_id,
        ):
            raise AlreadyExistsException(
                "Role Assignment",
            )

        # -------------------------------
        # Assign
        # -------------------------------

        return user_role_repository.assign_role(
            db,
            user_id,
            role_id,
        )

    def remove_role(
        self,
        db: Session,
        user_id: UUID,
        role_id: UUID,
    ):
        if not user_role_repository.role_exists(
            db,
            user_id,
            role_id,
        ):
            raise NotFoundException(
                "Role Assignment",
            )

        user_role_repository.remove_role(
            db,
            user_id,
            role_id,
        )

    def get_roles(
        self,
        db: Session,
        user_id: UUID,
    ):
        user = identity_user_repository.get_by_id(
            db,
            user_id,
        )

        if user is None:
            raise NotFoundException(
                "User",
                str(user_id),
            )

        return user_role_repository.get_roles(
            db,
            user_id,
        )


user_role_service = IdentityUserRoleService()