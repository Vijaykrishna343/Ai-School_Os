"""
Reusable permission enforcement dependency.

Usage in API routes:
    @router.post(
        "",
        dependencies=[Depends(require_permission("role.create"))],
    )
    def create_role(...):
        ...
"""

from typing import Callable

from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.enums.school import SchoolStatus
from app.common.exceptions import ForbiddenException
from app.common.logger.logger import get_logger
from app.dependencies import get_db
from app.identity.models.user import IdentityUser
from app.identity.security.current_user import get_current_user

logger = get_logger(__name__)


def require_permission(
    permission_name: str,
) -> Callable:
    """
    Returns a FastAPI dependency that enforces the
    given permission on the current user.

    Supports:
    - Super Admin global platform bypass
    - School suspension/block authorization checks
    - Soft-delete exclusion for roles & permissions
    - Wildcard permission matching ('*', 'module.*')
    """

    def _check_permission(
        current_user: IdentityUser = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> IdentityUser:
        # 1. Super Admin Bypass (Level 1 Platform Owner)
        if current_user.is_super_admin:
            return current_user

        # 2. School Lifecycle & Suspension Authorization Check (PART 11 / FIX 20)
        school = getattr(current_user, "school", None)
        if school and getattr(school, "status", None) in (
            SchoolStatus.SUSPENDED,
            SchoolStatus.BLOCKED,
            SchoolStatus.INACTIVE,
            SchoolStatus.CANCELLED,
        ):
            logger.warning(
                "School access suspended/blocked for user=%s school_id=%s status=%s",
                current_user.id,
                school.id,
                school.status,
            )
            raise ForbiddenException(
                "Your school's access is currently suspended. Please contact your school administrator."
            )

        # 3. Collect active, non-deleted permissions from non-deleted roles (FIX 16 & FIX 17)
        user_permissions: set[str] = set()

        for role in current_user.roles:
            if getattr(role, "is_deleted", False):
                continue

            for perm in role.permissions:
                if getattr(perm, "is_deleted", False):
                    continue
                user_permissions.add(perm.name)

        # 4. Evaluate exact match or wildcard match
        has_permission = (
            "*" in user_permissions
            or permission_name in user_permissions
        )

        if not has_permission and "." in permission_name:
            module = permission_name.split(".", 1)[0]
            if f"{module}.*" in user_permissions:
                has_permission = True

        if not has_permission:
            logger.warning(
                "Permission denied: user=%s required=%s granted=%s",
                current_user.id,
                permission_name,
                user_permissions,
            )
            raise ForbiddenException(
                f"Permission '{permission_name}' required."
            )

        return current_user

    return _check_permission

