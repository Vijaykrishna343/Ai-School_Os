from datetime import datetime, timezone
from uuid import UUID, uuid4

from jose import JWTError, jwt

from app.common.enums.identity.token_type import TokenType
from app.identity.security.jwt_config import jwt_settings


class JWTManager:
    """
    Handles JWT token generation and validation.
    """

    def create_access_token(
        self,
        user_id: UUID,
        school_id: UUID,
    ) -> str:

        now = datetime.now(timezone.utc)

        payload = {
            "sub": str(user_id),
            "school_id": str(school_id),
            "type": TokenType.ACCESS.value,
            "iat": now,
            "exp": now + jwt_settings.access_token_expiry,
            "jti": str(uuid4()),
        }

        return jwt.encode(
            payload,
            jwt_settings.SECRET_KEY,
            algorithm=jwt_settings.ALGORITHM,
        )

    def create_refresh_token(
        self,
        user_id: UUID,
        school_id: UUID,
    ) -> str:

        now = datetime.now(timezone.utc)

        payload = {
            "sub": str(user_id),
            "school_id": str(school_id),
            "type": TokenType.REFRESH.value,
            "iat": now,
            "exp": now + jwt_settings.refresh_token_expiry,
            "jti": str(uuid4()),
        }

        return jwt.encode(
            payload,
            jwt_settings.SECRET_KEY,
            algorithm=jwt_settings.ALGORITHM,
        )

    def decode_token(
        self,
        token: str,
    ) -> dict:

        return jwt.decode(
            token,
            jwt_settings.SECRET_KEY,
            algorithms=[jwt_settings.ALGORITHM],
        )

    def verify_token(
        self,
        token: str,
    ) -> dict | None:

        try:
            return self.decode_token(token)

        except JWTError:
            return None


jwt_manager = JWTManager()