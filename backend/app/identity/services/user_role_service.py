from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    BadRequestException,
    NotFoundException,
)
from app.common.logger.logger import get_logger
from app.identity.repositories import (
    identity_user_repository,
    role_repository,
    user_role_repository,
)

logger = get_logger(__name__)


class IdentityUserRoleService:
    """
    Business logic for User ↔ Role assignments.
    """

    # ------------------------------------------------------------------
    # Create Methods
    # ------------------------------------------------------------------

    def assign_role(
        self,
        db: Session,
        user_id: UUID,
        role_id: UUID,
    ) -> Any:
        """
        Assign a role to a user.
        """
        logger.info("Assigning role ID %s to user ID %s", role_id, user_id)

        # -------------------------------
        # Validate User
        # -------------------------------

        user = identity_user_repository.get_by_id(
            db,
            user_id,
        )

        if user is None:
            logger.warning("Validation failure: User ID '%s' not found for role assignment", user_id)
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
            logger.warning("Validation failure: Role ID '%s' not found for user assignment", role_id)
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
            logger.warning(
                "Validation failure: User school (%s) and Role school (%s) mismatch",
                user.school_id,
                role.school_id,
            )
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
            logger.warning("Validation failure: Role ID %s already assigned to user ID %s", role_id, user_id)
            raise AlreadyExistsException(
                "Role Assignment",
            )

        # -------------------------------
        # Assign
        # -------------------------------

        result = user_role_repository.assign_role(
            db,
            user_id,
            role_id,
        )
        logger.info("Role ID %s assigned to user ID %s successfully", role_id, user_id)
        return result

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_roles(
        self,
        db: Session,
        user_id: UUID,
    ) -> Any:
        """
        Get all assigned roles for a user.
        """
        user = identity_user_repository.get_by_id(
            db,
            user_id,
        )

        if user is None:
            logger.warning("Validation failure: User ID '%s' not found", user_id)
            raise NotFoundException(
                "User",
                str(user_id),
            )

        return user_role_repository.get_roles(
            db,
            user_id,
        )

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
        Remove a role from a user.
        """
        logger.info("Removing role ID %s from user ID %s", role_id, user_id)
        if not user_role_repository.role_exists(
            db,
            user_id,
            role_id,
        ):
            logger.warning("Validation failure: Role assignment between user ID %s and role ID %s not found", user_id, role_id)
            raise NotFoundException(
                "Role Assignment",
            )

        user_role_repository.remove_role(
            db,
            user_id,
            role_id,
        )
        logger.info("Role ID %s removed from user ID %s successfully", role_id, user_id)


user_role_service = IdentityUserRoleService()