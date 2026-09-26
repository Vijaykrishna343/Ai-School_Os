from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.common.exceptions import UnauthorizedException
from app.common.security.rate_limiter import (
    enforce_login_rate_limit,
    enforce_password_reset_rate_limit,
    get_client_ip,
)
from app.core.config import settings
from app.dependencies import get_db
from app.identity.dependencies import (
    get_authentication_service,
)
from app.identity.models.user import IdentityUser
from app.identity.schemas.user import (
    CurrentUser,
    ForgotPassword,
    ForgotPasswordResponse,
    RefreshToken,
    ResetPassword,
    ResetPasswordResponse,
    UserLogin,
    UserLoginResponse,
    UserLogout,
    UserLogoutResponse,
)
from app.identity.security import get_current_user
from app.identity.services.authentication_service import (
    AuthenticationService,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Helper to attach secure HttpOnly access and refresh token cookies."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path="/",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path="/",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


def _clear_auth_cookies(response: Response) -> None:
    """Helper to clear authentication cookies with matching scope."""
    response.delete_cookie(
        key="access_token",
        path="/",
        domain=settings.COOKIE_DOMAIN,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        httponly=True,
    )
    response.delete_cookie(
        key="refresh_token",
        path="/",
        domain=settings.COOKIE_DOMAIN,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        httponly=True,
    )


@router.post(
    "/login",
    response_model=UserLoginResponse,
    summary="Login",
    dependencies=[Depends(enforce_login_rate_limit)],
)
def login(
    credentials: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    auth_service: AuthenticationService = Depends(
        get_authentication_service,
    ),
) -> UserLoginResponse:
    """Authenticate a user, issue secure HttpOnly cookies, and return tokens."""
    client_ip = get_client_ip(request)
    result = auth_service.login(
        db,
        credentials,
        client_ip=client_ip,
    )
    _set_auth_cookies(response, result.access_token, result.refresh_token)
    return result


@router.post(
    "/refresh",
    response_model=UserLoginResponse,
    summary="Refresh Token",
)
def refresh_token(
    request: Request,
    response: Response,
    data: RefreshToken = RefreshToken(),
    db: Session = Depends(get_db),
    auth_service: AuthenticationService = Depends(
        get_authentication_service,
    ),
) -> UserLoginResponse:
    """Issue new tokens using a valid refresh token from cookie or request body."""
    raw_token = data.refresh_token or request.cookies.get("refresh_token")
    if not raw_token:
        raise UnauthorizedException("Refresh token required.")

    result = auth_service.refresh_token(
        db,
        RefreshToken(refresh_token=raw_token),
    )
    _set_auth_cookies(response, result.access_token, result.refresh_token)
    return result


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


@router.post(
    "/logout",
    response_model=UserLogoutResponse,
    summary="Logout",
)
def logout(
    request: Request,
    response: Response,
    data: UserLogout = UserLogout(),
    current_user: IdentityUser = Depends(
        get_current_user,
    ),
    db: Session = Depends(get_db),
    auth_service: AuthenticationService = Depends(
        get_authentication_service,
    ),
) -> UserLogoutResponse:
    """Revoke active refresh token session, clear authentication cookies, and logout current user."""
    raw_token = data.refresh_token or request.cookies.get("refresh_token")
    result = auth_service.logout(
        db,
        current_user,
        UserLogout(refresh_token=raw_token),
    )
    _clear_auth_cookies(response)
    return result


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="Forgot Password",
    dependencies=[Depends(enforce_password_reset_rate_limit)],
)
def forgot_password(
    data: ForgotPassword,
    request: Request,
    db: Session = Depends(get_db),
    auth_service: AuthenticationService = Depends(
        get_authentication_service,
    ),
) -> ForgotPasswordResponse:
    """Request password reset link/instructions."""
    client_ip = get_client_ip(request)
    return auth_service.forgot_password(
        db,
        data,
        client_ip=client_ip,
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    summary="Reset Password",
)
def reset_password(
    data: ResetPassword,
    db: Session = Depends(get_db),
    auth_service: AuthenticationService = Depends(
        get_authentication_service,
    ),
) -> ResetPasswordResponse:
    """Reset password using a valid single-use reset token."""
    return auth_service.reset_password(
        db,
        data,
    )