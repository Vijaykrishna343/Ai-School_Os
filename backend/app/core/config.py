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
    "change_this_to_a_secure_random_secret_in_production",
    "your_secure_64_character_random_secret_key_here",
}

INSECURE_DEFAULT_DB_PATTERNS = {
    "postgres:postgres",
    "user:pass",
    "user:password",
    "change_me_in_prod",
    "change_me",
    "your_secure_database_password_here",
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
    LOGIN_RATE_LIMIT: int = 5
    LOGIN_RATE_WINDOW_SECONDS: int = 60
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 60
    PASSWORD_RESET_RATE_LIMIT: int = 5
    PASSWORD_RESET_RATE_WINDOW_SECONDS: int = 300
    REDIS_URL: Union[str, None] = None
    DOCUMENT_STORAGE_PATH: str = str(BASE_DIR / "storage" / "documents")
    DOCUMENT_MAX_SIZE_MB: int = 10
    STORAGE_PROVIDER: str = "local"
    TRUST_PROXY: bool = False

    # Cookie Security Settings (Phase E)
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: Union[str, None] = None

    # Payment Gateway Settings (Phase 25.2)
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Meta WhatsApp Cloud API Settings (Phase 27.3)
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = "school_erp_whatsapp_verify_token_secure"
    WHATSAPP_APP_SECRET: str = ""

    # Prometheus Metrics Authentication Settings (Phase F)
    METRICS_AUTH_TOKEN: str = "dev-metrics-token-secure-32chars"
    METRICS_USERNAME: str = ""
    METRICS_PASSWORD: str = ""

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
            if (
                secret_clean in INSECURE_DEFAULT_SECRETS
                or "change_this" in secret_clean
                or "changeme" in secret_clean
                or "your_secure" in secret_clean
                or len(self.SECRET_KEY) < 32
            ):
                raise ValueError(
                    "SECRET_KEY is insecure or using default placeholder in production environment."
                )

            db_url_clean = self.DATABASE_URL.strip().lower()
            if any(pattern in db_url_clean for pattern in INSECURE_DEFAULT_DB_PATTERNS):
                raise ValueError("DATABASE_URL contains default/placeholder credentials in production environment.")

            origins = self.ALLOWED_ORIGINS
            if isinstance(origins, str):
                origins = [o.strip() for o in origins.split(",") if o.strip()]
            if "*" in origins:
                raise ValueError("Wildcard '*' ALLOWED_ORIGINS is prohibited in production environment.")

            if not self.COOKIE_SECURE:
                raise ValueError("COOKIE_SECURE must be True in production environment.")

            if self.COOKIE_SAMESITE.lower() not in ("lax", "strict"):
                raise ValueError("COOKIE_SAMESITE must be 'lax' or 'strict' in production environment.")

            # Metrics Authentication Production Hardening (Phase F)
            metrics_token = self.METRICS_AUTH_TOKEN.strip()
            metrics_user = self.METRICS_USERNAME.strip()
            metrics_pass = self.METRICS_PASSWORD.strip()

            has_valid_token = bool(
                metrics_token
                and metrics_token.lower() not in INSECURE_DEFAULT_SECRETS
                and "change_this" not in metrics_token.lower()
                and "changeme" not in metrics_token.lower()
                and "replace_with" not in metrics_token.lower()
                and "dev-metrics" not in metrics_token.lower()
                and len(metrics_token) >= 32
            )

            has_valid_basic = bool(
                metrics_user
                and metrics_pass
                and metrics_user.lower() not in INSECURE_DEFAULT_SECRETS
                and metrics_pass.lower() not in INSECURE_DEFAULT_SECRETS
                and "change_this" not in metrics_pass.lower()
                and "changeme" not in metrics_pass.lower()
                and "replace_with" not in metrics_pass.lower()
                and len(metrics_pass) >= 16
            )

            if not (has_valid_token or has_valid_basic):
                raise ValueError(
                    "METRICS authentication credential (METRICS_AUTH_TOKEN or METRICS_USERNAME/METRICS_PASSWORD) "
                    "must be securely configured in production environment."
                )

            # Distributed Rate Limiting & Redis Production Hardening (Phase G)
            redis_url_clean = (self.REDIS_URL or "").strip().lower()
            if not redis_url_clean:
                raise ValueError(
                    "REDIS_URL must be configured in production environment for distributed rate limiting."
                )

            if not (redis_url_clean.startswith("redis://") or redis_url_clean.startswith("rediss://")):
                raise ValueError(
                    "REDIS_URL must be a valid redis:// or rediss:// connection URI in production environment."
                )

            if any(
                pattern in redis_url_clean
                for pattern in (
                    "change_me",
                    "changeme",
                    "placeholder",
                    "your_secure",
                    "user:password",
                    "user:pass",
                )
            ):
                raise ValueError(
                    "REDIS_URL contains default/placeholder credentials in production environment."
                )

        return self


settings = Settings()