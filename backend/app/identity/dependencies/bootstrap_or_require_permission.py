from typing import Callable

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.common.logger.logger import get_logger
from app.dependencies import get_db
from app.identity.dependencies.require_permission import (
    require_permission,
)
from app.identity.models.user import IdentityUser
from app.identity.repositories import identity_bootstrap_repository
from app.identity.security.current_user import get_current_user
from app.identity.security.oauth2 import get_token, http_bearer

logger = get_logger(__name__)


def bootstrap_or_require_permission(
    permission_name: str,
) -> Callable:
    """
    Returns a FastAPI dependency that allows bootstrapping the first user
    without authentication/authorization ONLY IF the persistent platform bootstrap
    state is not yet completed.

    Once platform bootstrap is completed (is_completed=True in identity_bootstrap_states),
    unauthenticated bootstrap is permanently closed and all requests must provide valid
    credentials with the requested permission.
    """
    perm_checker = require_permission(permission_name)

    async def _check_bootstrap_or_permission(
        request: Request,
        db: Session = Depends(get_db),
    ) -> IdentityUser | None:
        if not identity_bootstrap_repository.is_platform_bootstrapped(db):
            logger.info(
                "Platform bootstrap mode active (setup not completed): bypassing authentication for user creation"
            )
            return None

        credentials = await http_bearer(request)
        token = get_token(request=request, credentials=credentials)
        current_user = get_current_user(token=token, db=db)
        return perm_checker(current_user=current_user, db=db)

    return _check_bootstrap_or_permission
