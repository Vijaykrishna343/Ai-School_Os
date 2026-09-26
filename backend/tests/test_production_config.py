"""
Tests for Phase 4C.4 Production Configuration Hardening:
- Rejection of DEBUG=True in production environment
- Rejection of default/insecure SECRET_KEY in production environment
- Acceptance of valid production configuration
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_app_main_imports_successfully():
    """Verify that app.main module imports successfully without any missing dependency or NameError."""
    import app.main
    assert app.main.app is not None


def test_production_env_rejects_docker_compose_default_secret_key():
    """Settings must raise ValidationError in production when using the docker-compose.yml default SECRET_KEY."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            APP_NAME="AI School OS",
            APP_VERSION="1.0.0",
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql://produser:ProdPass987%21@dbserver:5432/school_prod",
            SECRET_KEY="change_this_to_a_secure_random_secret_in_production",
        )
    assert "SECRET_KEY is insecure" in str(exc_info.value)


def test_production_env_rejects_docker_compose_default_db_credentials():
    """Settings must raise ValidationError in production when using the docker-compose.yml default database credentials."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            APP_NAME="AI School OS",
            APP_VERSION="1.0.0",
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql://school_user:change_me_in_prod@db:5432/school_erp",
            SECRET_KEY="a_very_secure_and_random_production_secret_key_1234567890",
        )
    assert "DATABASE_URL contains default/placeholder credentials" in str(exc_info.value)


def test_production_env_rejects_env_example_placeholders():
    """Settings must raise ValidationError in production when using .env.example placeholder secrets or passwords."""
    with pytest.raises(ValidationError):
        Settings(
            APP_NAME="AI School OS",
            APP_VERSION="1.0.0",
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql://school_user:YOUR_SECURE_DATABASE_PASSWORD_HERE@db:5432/school_erp",
            SECRET_KEY="a_very_secure_and_random_production_secret_key_1234567890",
        )

    with pytest.raises(ValidationError):
        Settings(
            APP_NAME="AI School OS",
            APP_VERSION="1.0.0",
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql://produser:ProdPass987%21@dbserver:5432/school_prod",
            SECRET_KEY="YOUR_SECURE_64_CHARACTER_RANDOM_SECRET_KEY_HERE",
        )


def test_production_env_rejects_debug_true():
    """Settings must raise ValidationError if ENVIRONMENT is production and DEBUG is True."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            APP_NAME="AI School OS",
            APP_VERSION="1.0.0",
            ENVIRONMENT="production",
            DEBUG=True,
            DATABASE_URL="postgresql://user:pass@localhost:5432/school_db",
            SECRET_KEY="super_secret_32_character_long_production_key_12345",
        )
    assert "DEBUG must be False in production" in str(exc_info.value)


def test_production_env_rejects_insecure_secret_key():
    """Settings must raise ValidationError if ENVIRONMENT is production and SECRET_KEY is default/insecure."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            APP_NAME="AI School OS",
            APP_VERSION="1.0.0",
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql://user:pass@localhost:5432/school_db",
            SECRET_KEY="changeme",
        )
    assert "SECRET_KEY is insecure" in str(exc_info.value)


def test_production_env_rejects_default_db_credentials():
    """Settings must raise ValidationError if ENVIRONMENT is production and DATABASE_URL uses placeholder credentials."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            APP_NAME="AI School OS",
            APP_VERSION="1.0.0",
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql://postgres:postgres@localhost:5432/school_db",
            SECRET_KEY="super_secret_32_character_long_production_key_12345",
        )
    assert "DATABASE_URL contains default/placeholder credentials" in str(exc_info.value)


def test_production_env_rejects_wildcard_cors():
    """Settings must raise ValidationError if ENVIRONMENT is production and ALLOWED_ORIGINS has wildcard '*'."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            APP_NAME="AI School OS",
            APP_VERSION="1.0.0",
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql://produser:ProdPass987%21@dbserver:5432/school_prod",
            SECRET_KEY="super_secret_32_character_long_production_key_12345",
            ALLOWED_ORIGINS=["*"],
        )
    assert "Wildcard '*' ALLOWED_ORIGINS is prohibited" in str(exc_info.value)


def test_production_env_rejects_insecure_cookie():
    """Settings must raise ValidationError if ENVIRONMENT is production and COOKIE_SECURE is False."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            APP_NAME="AI School OS",
            APP_VERSION="1.0.0",
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql://produser:ProdPass987%21@dbserver:5432/school_prod",
            SECRET_KEY="a_very_secure_and_random_production_secret_key_1234567890",
            ALLOWED_ORIGINS=["https://app.schoolos.com"],
            COOKIE_SECURE=False,
        )
    assert "COOKIE_SECURE must be True in production" in str(exc_info.value)


def test_production_env_rejects_insecure_metrics_token():
    """Settings must raise ValidationError if ENVIRONMENT is production and METRICS_AUTH_TOKEN is placeholder."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            APP_NAME="AI School OS",
            APP_VERSION="1.0.0",
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql://produser:ProdPass987%21@dbserver:5432/school_prod",
            SECRET_KEY="a_very_secure_and_random_production_secret_key_1234567890",
            ALLOWED_ORIGINS=["https://app.schoolos.com"],
            COOKIE_SECURE=True,
            METRICS_AUTH_TOKEN="changeme",
            REDIS_URL="redis://prod-redis:6379/0",
        )
    assert "METRICS authentication credential" in str(exc_info.value)


def test_production_env_rejects_missing_redis_url():
    """Settings must raise ValidationError in production if REDIS_URL is missing."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            APP_NAME="AI School OS",
            APP_VERSION="1.0.0",
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql://produser:ProdPass987%21@dbserver:5432/school_prod",
            SECRET_KEY="a_very_secure_and_random_production_secret_key_1234567890",
            ALLOWED_ORIGINS=["https://app.schoolos.com"],
            COOKIE_SECURE=True,
            METRICS_AUTH_TOKEN="a_very_secure_and_random_metrics_token_1234567890",
            REDIS_URL=None,
        )
    assert "REDIS_URL must be configured" in str(exc_info.value)


def test_production_env_rejects_insecure_redis_url():
    """Settings must raise ValidationError in production if REDIS_URL contains placeholder credentials or invalid scheme."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            APP_NAME="AI School OS",
            APP_VERSION="1.0.0",
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql://produser:ProdPass987%21@dbserver:5432/school_prod",
            SECRET_KEY="a_very_secure_and_random_production_secret_key_1234567890",
            ALLOWED_ORIGINS=["https://app.schoolos.com"],
            COOKIE_SECURE=True,
            METRICS_AUTH_TOKEN="a_very_secure_and_random_metrics_token_1234567890",
            REDIS_URL="redis://user:pass@redis:6379/0",
        )
    assert "REDIS_URL contains default/placeholder credentials" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        Settings(
            APP_NAME="AI School OS",
            APP_VERSION="1.0.0",
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql://produser:ProdPass987%21@dbserver:5432/school_prod",
            SECRET_KEY="a_very_secure_and_random_production_secret_key_1234567890",
            ALLOWED_ORIGINS=["https://app.schoolos.com"],
            COOKIE_SECURE=True,
            METRICS_AUTH_TOKEN="a_very_secure_and_random_metrics_token_1234567890",
            REDIS_URL="http://redis:6379/0",
        )
    assert "REDIS_URL must be a valid redis://" in str(exc_info.value)


def test_production_env_accepts_valid_config():
    """Settings must validate cleanly with ENVIRONMENT=production, DEBUG=False, valid secret, DB URL, secure cookies, metrics secret and Redis URL."""
    cfg = Settings(
        APP_NAME="AI School OS",
        APP_VERSION="1.0.0",
        ENVIRONMENT="production",
        DEBUG=False,
        DATABASE_URL="postgresql://produser:ProdPass987%21@dbserver:5432/school_prod",
        SECRET_KEY="a_very_secure_and_random_production_secret_key_1234567890",
        ALLOWED_ORIGINS=["https://app.schoolos.com"],
        COOKIE_SECURE=True,
        METRICS_AUTH_TOKEN="a_very_secure_and_random_metrics_token_1234567890",
        REDIS_URL="redis://prod-redis.internal:6379/0",
    )
    assert cfg.ENVIRONMENT == "production"
    assert cfg.DEBUG is False
    assert cfg.COOKIE_SECURE is True
    assert cfg.METRICS_AUTH_TOKEN == "a_very_secure_and_random_metrics_token_1234567890"
    assert cfg.REDIS_URL == "redis://prod-redis.internal:6379/0"


def test_development_env_usable():
    """Development environment defaults remain usable."""
    cfg = Settings(
        APP_NAME="AI School OS",
        APP_VERSION="1.0.0",
        ENVIRONMENT="development",
        DEBUG=True,
        DATABASE_URL="sqlite:///:memory:",
        SECRET_KEY="development_secret",
    )
    assert cfg.ENVIRONMENT == "development"
    assert cfg.DEBUG is True


def test_security_headers_injected(client):
    """Security headers must be present in responses."""
    res = client.get("/healthz")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

