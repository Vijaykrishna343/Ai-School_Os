from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
)
from app.common.logger.logger import get_logger
from app.identity.models.user import IdentityUser
from app.identity.repositories import (
    identity_user_repository,
    role_repository,
    user_role_repository,
)
from app.identity.schemas.user import (
    UserCreate,
    UserFilter,
    UserListResponse,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.identity.security.password import hash_password
from app.identity.services.base_identity_service import (
    BaseIdentityService,
)
from app.repositories.school.school_repository import school_repository

logger = get_logger(__name__)


class IdentityUserService(BaseIdentityService):
    """
    Business logic for Identity Users.
    """

    def create_user(
        self,
        db: Session,
        user: UserCreate,
        current_user: IdentityUser | None = None,
    ) -> IdentityUser:
        """
        Create a new identity user with tenant scoping.
        """
        if current_user and not current_user.is_super_admin:
            user.school_id = current_user.school_id

        logger.info(
            "Creating identity user email '%s' for school ID: %s",
            user.email,
            user.school_id,
        )

        school = school_repository.get_by_id(
            db,
            user.school_id,
        )


        if school is None:
            logger.warning(
                "Validation failure: School ID '%s' not found for user creation",
                user.school_id,
            )
            raise NotFoundException(
                "School not found."
            )

        if identity_user_repository.exists_by_email(
            db,
            user.school_id,
            user.email,
        ):
            logger.warning(
                "Validation failure: User email '%s' already exists for school ID: %s",
                user.email,
                user.school_id,
            )
            raise AlreadyExistsException(
                "Email",
                user.email,
            )

        if (
            user.username
            and identity_user_repository.exists_by_username(
                db,
                user.school_id,
                user.username,
            )
        ):
            logger.warning(
                "Validation failure: Username '%s' already exists for school ID: %s",
                user.username,
                user.school_id,
            )
            raise AlreadyExistsException(
                "Username",
                user.username,
            )

        # Count active users for the given school prior to user creation
        active_user_count = identity_user_repository.count_by_school(
            db,
            user.school_id,
        )

        db_user = IdentityUser(
            school_id=user.school_id,
            email=user.email,
            username=user.username,
            password_hash=hash_password(user.password),
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
        )

        created_user = identity_user_repository.create(
            db,
            db_user,
        )

        logger.info(
            "Identity user '%s' created successfully with ID: %s",
            created_user.email,
            created_user.id,
        )

        # Automatic bootstrap role assignment for the first user of the school
        if active_user_count == 0:
            logger.info("First active user detected for school %s: Assigning School Admin role", user.school_id)
            admin_role = role_repository.get_by_name(
                db,
                user.school_id,
                "School Admin",
            )
            if admin_role is None:
                admin_role = role_repository.get_by_name(
                    db,
                    None,
                    "School Admin",
                )

            if admin_role is not None:
                if not user_role_repository.role_exists(
                    db,
                    created_user.id,
                    admin_role.id,
                ):
                    user_role_repository.assign_role(
                        db,
                        created_user.id,
                        admin_role.id,
                    )
                    logger.info("Assigned School Admin role to user ID: %s", created_user.id)

        return created_user

    def get_user(
        self,
        db: Session,
        user_id: UUID,
        current_user: IdentityUser | None = None,
    ) -> IdentityUser:
        """
        Get an identity user by ID with tenant verification.
        """
        user = identity_user_repository.get_by_id(
            db,
            user_id,
        )

        if user is None or (current_user and not current_user.is_super_admin and user.school_id != current_user.school_id):
            logger.warning("Validation failure: User ID '%s' not found", user_id)
            raise NotFoundException(
                "User not found."
            )

        return user

    def get_users(
        self,
        db: Session,
        filters: UserFilter,
        current_user: IdentityUser | None = None,
    ) -> UserListResponse:
        """
        Get paginated list of users scoped to current_user's school.
        """
        effective_school_id = (
            filters.school_id
            if (current_user and current_user.is_super_admin and filters.school_id)
            else (current_user.school_id if current_user else filters.school_id)
        )

        users, total = identity_user_repository.list_users(
            db=db,
            school_id=effective_school_id,
            email=filters.email,
            username=filters.username,
            first_name=filters.first_name,
            is_active=filters.is_active,
            page=filters.page,
            page_size=filters.page_size,
        )

        total_pages = (total + filters.page_size - 1) // filters.page_size if total > 0 else 0

        return UserListResponse(
            items=[
                UserResponse.model_validate(user)
                for user in users
            ],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
        )

    def update_user(
        self,
        db: Session,
        user_id: UUID,
        data: UserUpdate,
        current_user: IdentityUser | None = None,
    ) -> IdentityUser:
        """
        Update an identity user.
        """
        logger.info("Updating identity user ID: %s", user_id)
        user = self.get_user(
            db,
            user_id,
            current_user=current_user,
        )

        updates = data.model_dump(
            exclude_unset=True,
        )

        for field, value in updates.items():
            setattr(
                user,
                field,
                value,
            )

        updated_user = identity_user_repository.update(
            db,
            user,
        )
        logger.info("Identity user ID: %s updated successfully", user_id)
        return updated_user

    def update_user_status(
        self,
        db: Session,
        user_id: UUID,
        status_data: UserStatusUpdate,
        current_user: IdentityUser | None = None,
    ) -> IdentityUser:
        """
        Suspend or reactivate a user account with security guards.
        """
        from datetime import datetime, timezone
        from app.common.exceptions import ForbiddenException

        user = self.get_user(db, user_id, current_user=current_user)

        if current_user:
            if user.id == current_user.id:
                raise ForbiddenException("Users cannot alter their own account status.")
            if user.is_super_admin and not current_user.is_super_admin:
                raise ForbiddenException("School administrators cannot suspend Super Admin accounts.")

        new_status = status_data.status.upper()
        user.status = new_status
        user.is_active = (new_status == "ACTIVE")
        user.suspension_reason = status_data.suspension_reason

        if new_status in ("SUSPENDED", "INACTIVE"):
            user.suspended_at = datetime.now(timezone.utc)
        elif new_status == "ACTIVE":
            user.suspended_at = None
            user.suspension_reason = None

        return identity_user_repository.update(db, user)


    def delete_user(
        self,
        db: Session,
        user_id: UUID,
        current_user: IdentityUser | None = None,
    ) -> None:
        """
        Soft delete an identity user.
        """
        logger.info("Soft deleting identity user ID: %s", user_id)
        user = self.get_user(
            db,
            user_id,
            current_user=current_user,
        )

        identity_user_repository.delete(
            db,
            user,
        )
        logger.info("Identity user ID: %s soft deleted successfully", user_id)


identity_user_service = IdentityUserService()