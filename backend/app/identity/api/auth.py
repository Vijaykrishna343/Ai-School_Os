from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.identity.dependencies import (
    get_authentication_service,
)
from app.identity.models.user import IdentityUser
from app.identity.schemas.user import (
    CurrentUser,
    RefreshToken,
    UserLogin,
    UserLoginResponse,
)
from app.identity.security import get_current_user
from app.identity.services.authentication_service import (
    AuthenticationService,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=UserLoginResponse,
    summary="Login",
)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
    auth_service: AuthenticationService = Depends(
        get_authentication_service,
    ),
) -> UserLoginResponse:
    """Authenticate a user and return tokens."""
    return auth_service.login(
        db,
        credentials,
    )


@router.post(
    "/refresh",
    response_model=UserLoginResponse,
    summary="Refresh Token",
)
def refresh_token(
    data: RefreshToken,
    db: Session = Depends(get_db),
    auth_service: AuthenticationService = Depends(
        get_authentication_service,
    ),
) -> UserLoginResponse:
    """Issue new tokens using a valid refresh token."""
    return auth_service.refresh_token(
        db,
        data,
    )


@router.get(
    "/me",
    response_model=CurrentUser,
    summary="Current User",
)
def me(
    current_user: IdentityUser = Depends(
        get_current_user,
    ),
) -> CurrentUser:
    """Return the currently authenticated user."""
    return current_user