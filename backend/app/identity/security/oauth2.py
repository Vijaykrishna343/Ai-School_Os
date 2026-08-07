from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

http_bearer = HTTPBearer(
    bearerFormat="JWT",
)

# Alias for backward compatibility if any module references oauth2_scheme
oauth2_scheme = http_bearer


def get_token(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> str:
    """
    FastAPI dependency that extracts the HTTP Bearer access token
    from the Authorization header. Returns raw JWT token string.
    """
    return credentials.credentials
