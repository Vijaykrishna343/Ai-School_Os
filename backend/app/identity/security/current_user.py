from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.enums.identity.token_type import TokenType
from app.common.exceptions import UnauthorizedException
from app.dependencies import get_db
from app.identity.models.user import IdentityUser
from app.identity.repositories import identity_user_repository
from app.identity.security.jwt_manager import jwt_manager
from app.identity.security.oauth2 import get_token


def get_current_user(
    token: str = Depends(get_token),
    db: Session = Depends(get_db),
) -> IdentityUser:
    """
    FastAPI dependency that extracts and validates the
    current user from the JWT access token.

    Rejects refresh tokens to prevent token type confusion.
    """

    payload = jwt_manager.verify_token(token)

    if payload is None:
        raise UnauthorizedException(
            "Invalid or expired token."
        )

    # -----------------------------------------------
    # Reject non-access tokens
    # -----------------------------------------------

    token_type = payload.get("type")

    if token_type != TokenType.ACCESS:
        raise UnauthorizedException(
            "Invalid token type. Access token required."
        )

    # -----------------------------------------------
    # Retrieve user
    # -----------------------------------------------

    user_id = UUID(payload["sub"])

    user = identity_user_repository.get_by_id(
        db,
        user_id,
    )

    if user is None or user.is_deleted:
        raise UnauthorizedException(
            "User not found."
        )

    if not user.is_active:
        raise UnauthorizedException(
            "User is inactive."
        )

    return user