"""
Tests for Phase 4C.4 Production Configuration Hardening:
- Rejection of DEBUG=True in production environment
- Rejection of default/insecure SECRET_KEY in production environment
- Acceptance of valid production configuration
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


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


def test_production_env_accepts_valid_config():
    """Settings must validate cleanly with ENVIRONMENT=production, DEBUG=False, valid secret and DB URL."""
    cfg = Settings(
        APP_NAME="AI School OS",
        APP_VERSION="1.0.0",
        ENVIRONMENT="production",
        DEBUG=False,
        DATABASE_URL="postgresql://produser:ProdPass987%21@dbserver:5432/school_prod",
        SECRET_KEY="a_very_secure_and_random_production_secret_key_1234567890",
        ALLOWED_ORIGINS=["https://app.schoolos.com"],
    )
    assert cfg.ENVIRONMENT == "production"
    assert cfg.DEBUG is False


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
