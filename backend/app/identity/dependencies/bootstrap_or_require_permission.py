import logging
from typing import Callable

from fastapi import Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.identity.dependencies.require_permission import (
    require_permission,
)
from app.identity.models.user import IdentityUser
from app.identity.security.current_user import get_current_user
from app.identity.security.oauth2 import get_token, http_bearer

logger = logging.getLogger(__name__)


def bootstrap_or_require_permission(
    permission_name: str,
) -> Callable:
    """
    Returns a FastAPI dependency that allows bootstrapping the first active user
    without authentication/authorization if active user count in identity_users is 0.
    Otherwise, delegates to require_permission(permission_name).
    """
    perm_checker = require_permission(permission_name)

    async def _check_bootstrap_or_permission(
        request: Request,
        db: Session = Depends(get_db),
    ) -> IdentityUser | None:
        stmt = select(func.count(IdentityUser.id)).where(
            IdentityUser.is_active.is_(True),
            IdentityUser.is_deleted.is_(False),
        )
        active_count = db.scalar(stmt) or 0

        if active_count == 0:
            logger.info(
                "Bootstrapping mode active (0 active users): bypassing authentication for user creation"
            )
            return None

        credentials = await http_bearer(request)
        token = get_token(credentials)
        current_user = get_current_user(token=token, db=db)
        return perm_checker(current_user=current_user, db=db)

    return _check_bootstrap_or_permission
