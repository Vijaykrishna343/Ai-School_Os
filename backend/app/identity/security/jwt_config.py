from datetime import timedelta

from app.core.config import settings


class JWTSettings:
    """
    JWT configuration.

    Reads token expiry values from application settings
    rather than hardcoding them.
    """

    SECRET_KEY = settings.SECRET_KEY

    ALGORITHM = settings.ALGORITHM

    ACCESS_TOKEN_EXPIRE_MINUTES = (
        settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    REFRESH_TOKEN_EXPIRE_DAYS = (
        settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    @property
    def access_token_expiry(self) -> timedelta:
        return timedelta(
            minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    @property
    def refresh_token_expiry(self) -> timedelta:
        return timedelta(
            days=self.REFRESH_TOKEN_EXPIRE_DAYS
        )


jwt_settings = JWTSettings()