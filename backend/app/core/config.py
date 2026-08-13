from pathlib import Path
from typing import Union

from pydantic import model_validator
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

INSECURE_DEFAULT_SECRETS = {
    "secret",
    "secretkey",
    "changeme",
    "qyz6bedgrvih90lujit5xplucdvpeiq1mkwgf0f4mt1oekyb934vuz9jtw_shwscuh53iigb8g4drqoa_ipfq",
    "change_this_to_a_secure_32_byte_random_secret_in_production",
}


class Settings(BaseSettings):
    APP_NAME: str = "AI School OS"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    ALLOWED_ORIGINS: Union[list[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_hardening(self) -> "Settings":
        env_lower = self.ENVIRONMENT.lower()
        if env_lower in ("production", "prod"):
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production environment.")

            secret_clean = self.SECRET_KEY.strip().lower()
            if secret_clean in INSECURE_DEFAULT_SECRETS or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY is insecure or using default placeholder in production environment."
                )

        return self


settings = Settings()