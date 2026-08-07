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

import logging
from typing import Callable

from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.exceptions import ForbiddenException
from app.dependencies import get_db
from app.identity.models.user import IdentityUser
from app.identity.security.current_user import (
    get_current_user,
)

logger = logging.getLogger(__name__)


def require_permission(
    permission_name: str,
) -> Callable:
    """
    Returns a FastAPI dependency that enforces the
    given permission on the current user.

    Checks all roles assigned to the user and verifies
    that at least one role grants the required permission.
    """

    def _check_permission(
        current_user: IdentityUser = Depends(
            get_current_user,
        ),
        db: Session = Depends(get_db),
    ) -> IdentityUser:

        # Collect all permission names from user roles
        user_permissions: set[str] = set()

        for role in current_user.roles:
            for perm in role.permissions:
                user_permissions.add(perm.name)

        if permission_name not in user_permissions:
            logger.warning(
                "Permission denied: user=%s "
                "required=%s granted=%s",
                current_user.id,
                permission_name,
                user_permissions,
            )

            raise ForbiddenException(
                f"Permission '{permission_name}' required."
            )

        return current_user

    return _check_permission
