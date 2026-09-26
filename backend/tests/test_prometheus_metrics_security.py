"""
Prometheus Metrics Endpoint Security Tests — Phase F.

Tests:
1. Anonymous GET /metrics is rejected (401 Unauthorized).
2. Missing Authorization header is rejected (401 Unauthorized).
3. Invalid Bearer token is rejected (401 Unauthorized).
4. Invalid Basic Auth credentials rejected (401 Unauthorized).
5. Malformed Authorization header rejected (401 Unauthorized).
6. Valid Bearer token authentication succeeds (200 OK).
7. Valid Basic Auth authentication succeeds (200 OK).
8. Successful response delivers valid Prometheus exposition format (version 0.0.4).
9. Authentication failure response does not leak internal secrets or stack traces.
10. Ordinary application user JWT without metrics credential is rejected (401 Unauthorized).
11. Public health probes (/health/live, /health/ready, /healthz) remain unauthenticated and operational (200 OK).
12. Production config validation rejects missing metrics secret.
13. Production config validation rejects insecure/placeholder metrics secrets (e.g. changeme, admin, metrics, dev-metrics).
14. Production config validation accepts valid strong metrics secret.
15. Adversarial internet attack simulation against /metrics.
"""

import base64
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.main import app


client = TestClient(app)


def test_01_anonymous_metrics_request_rejected():
    """Public anonymous requests to /metrics must be rejected with 401 Unauthorized."""
    resp = client.get("/metrics")
    assert resp.status_code == 401
    assert "WWW-Authenticate" in resp.headers
    assert "Authentication required" in resp.json().get("detail", "")


def test_02_invalid_bearer_token_rejected():
    """Requests with incorrect Bearer tokens must be rejected with 401 Unauthorized."""
    resp = client.get("/metrics", headers={"Authorization": "Bearer totally_wrong_secret_token_value"})
    assert resp.status_code == 401
    assert "WWW-Authenticate" in resp.headers
    assert "Invalid monitoring credentials" in resp.json().get("detail", "")


def test_03_invalid_basic_auth_rejected(monkeypatch):
    """Requests with incorrect Basic Auth credentials must be rejected with 401 Unauthorized."""
    monkeypatch.setattr(settings, "METRICS_USERNAME", "prom_admin")
    monkeypatch.setattr(settings, "METRICS_PASSWORD", "SuperSecurePassword123!")

    # Wrong password
    bad_creds = base64.b64encode(b"prom_admin:wrong_password").decode("utf-8")
    resp = client.get("/metrics", headers={"Authorization": f"Basic {bad_creds}"})
    assert resp.status_code == 401

    # Wrong username
    bad_user = base64.b64encode(b"wrong_user:SuperSecurePassword123!").decode("utf-8")
    resp = client.get("/metrics", headers={"Authorization": f"Basic {bad_user}"})
    assert resp.status_code == 401


def test_04_malformed_auth_header_rejected():
    """Requests with malformed Authorization headers must be rejected safely with 401."""
    resp = client.get("/metrics", headers={"Authorization": "NotAScheme"})
    assert resp.status_code == 401

    resp = client.get("/metrics", headers={"Authorization": "Basic not_valid_base64==="})
    assert resp.status_code == 401


def test_05_valid_bearer_token_succeeds():
    """Authorized scraper with valid Bearer token receives 200 OK and Prometheus metrics."""
    resp = client.get("/metrics", headers={"Authorization": f"Bearer {settings.METRICS_AUTH_TOKEN}"})
    assert resp.status_code == 200
    assert "text/plain" in resp.headers.get("content-type", "")
    assert "version=0.0.4" in resp.headers.get("content-type", "")

    body = resp.text
    assert "# HELP school_erp_app_info" in body
    assert "# TYPE school_erp_app_info gauge" in body
    assert "school_erp_database_connected" in body
    assert "school_erp_http_requests_total" in body


def test_06_valid_basic_auth_succeeds(monkeypatch):
    """Authorized scraper with valid HTTP Basic credentials receives 200 OK."""
    monkeypatch.setattr(settings, "METRICS_USERNAME", "prometheus_scraper")
    monkeypatch.setattr(settings, "METRICS_PASSWORD", "SuperSecretScraperPassword456!")

    valid_creds = base64.b64encode(b"prometheus_scraper:SuperSecretScraperPassword456!").decode("utf-8")
    resp = client.get("/metrics", headers={"Authorization": f"Basic {valid_creds}"})
    assert resp.status_code == 200
    assert "school_erp_app_info" in resp.text


def test_07_auth_failure_does_not_leak_secrets_or_stack_traces():
    """Authentication failures return clean JSON and do not expose server secrets or tracebacks."""
    resp = client.get("/metrics", headers={"Authorization": "Bearer bad-token-attempt"})
    assert resp.status_code == 401
    data = resp.json()
    assert "detail" in data
    # Ensure no secret strings or internal paths are in the response
    assert settings.METRICS_AUTH_TOKEN not in resp.text
    assert settings.SECRET_KEY not in resp.text
    assert "Traceback" not in resp.text
    assert "File \"" not in resp.text


def test_08_ordinary_user_token_rejected_at_metrics():
    """An ordinary user access token (e.g. from a student/teacher/admin) cannot access /metrics."""
    fake_user_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3OC11c2VyIiwiZXhwIjo5OTk5OTk5OTk5fQ.fake_signature"
    resp = client.get("/metrics", headers={"Authorization": f"Bearer {fake_user_jwt}"})
    assert resp.status_code == 401


def test_09_public_health_probes_remain_unauthenticated():
    """Health probes must remain accessible without authentication for orchestrators/load balancers."""
    res_live = client.get("/health/live")
    assert res_live.status_code == 200
    assert res_live.json().get("status") in ("ok", "healthy")

    res_ready = client.get("/health/ready")
    assert res_ready.status_code in (200, 503)

    res_healthz = client.get("/healthz")
    assert res_healthz.status_code == 200


def test_10_production_config_rejects_missing_metrics_secret():
    """Production configuration must fail validation if METRICS credentials are not configured."""
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
            METRICS_AUTH_TOKEN="",
            METRICS_USERNAME="",
            METRICS_PASSWORD="",
        )
    assert "METRICS authentication credential" in str(exc_info.value)


def test_11_production_config_rejects_insecure_default_metrics_tokens():
    """Production configuration must reject default/insecure placeholder metrics secrets."""
    insecure_tokens = [
        "changeme",
        "change_this_to_a_secure_token",
        "replace_with_secure_random_value",
        "dev-metrics-token-secure-32chars",
        "admin",
        "metrics",
        "prometheus",
        "short_token_123",  # < 32 chars
    ]

    for bad_token in insecure_tokens:
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
                METRICS_AUTH_TOKEN=bad_token,
            )
        assert "METRICS authentication credential" in str(exc_info.value)


def test_12_production_config_accepts_valid_metrics_secret():
    """Production configuration validates cleanly with a 32+ char secure metrics auth token."""
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
        REDIS_URL="redis://prod-redis:6379/0",
    )
    assert cfg.ENVIRONMENT == "production"
    assert cfg.METRICS_AUTH_TOKEN == "a_very_secure_and_random_metrics_token_1234567890"
    assert cfg.REDIS_URL == "redis://prod-redis:6379/0"


def test_13_adversarial_metrics_scraping_attempt():
    """
    Adversarial Attack Simulation:
    Attacker tries:
    1. Unauthenticated scraping
    2. Guessing dictionary passwords
    3. Forged Bearer tokens
    All must be rejected with 401 Unauthorized.
    """
    attacker_attempts = [
        {},
        {"Authorization": "Bearer admin"},
        {"Authorization": "Bearer 123456"},
        {"Authorization": "Bearer secret"},
        {"Authorization": "Bearer prometheus"},
        {"Authorization": "Basic " + base64.b64encode(b"admin:admin").decode("utf-8")},
        {"Authorization": "Basic " + base64.b64encode(b"root:root").decode("utf-8")},
    ]

    for headers in attacker_attempts:
        resp = client.get("/metrics", headers=headers)
        assert resp.status_code == 401, f"Expected 401 for headers {headers}, got {resp.status_code}"
