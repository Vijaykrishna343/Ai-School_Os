from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.exceptions import UnauthorizedException

http_bearer = HTTPBearer(
    bearerFormat="JWT",
    auto_error=False,
)

# Alias for backward compatibility if any module references oauth2_scheme
oauth2_scheme = http_bearer


def get_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
) -> str:
    """
    FastAPI dependency that extracts the access token.
    1. Checks HTTP Bearer in Authorization header (API clients / test fixtures).
    2. Falls back to HttpOnly cookie 'access_token' (browser requests).
    """
    if credentials and credentials.credentials:
        return credentials.credentials

    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token

    raise UnauthorizedException("Not authenticated.")
