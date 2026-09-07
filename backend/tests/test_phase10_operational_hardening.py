"""
Phase 10 Production Hardening & Operational Readiness Verification Tests.
Tests Liveness/Readiness Probes, Request Correlation IDs, Security Headers, and Rate Limiter.
"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.common.security.rate_limiter import rate_limiter

client = TestClient(app)


def test_liveness_and_readiness_probes():
    """Verify standard Kubernetes health probes (healthz, live, readyz, ready)."""
    # 1. Liveness
    live_res = client.get("/healthz")
    assert live_res.status_code == 200
    assert live_res.json()["status"] == "ok"

    live_alias = client.get("/health/live")
    assert live_alias.status_code == 200
    assert live_alias.json()["status"] == "ok"

    # 2. Readiness
    ready_res = client.get("/readyz")
    assert ready_res.status_code == 200
    assert ready_res.json()["status"] == "ready"
    assert ready_res.json()["database"] == "connected"

    ready_alias = client.get("/health/ready")
    assert ready_alias.status_code == 200
    assert ready_alias.json()["status"] == "ready"


def test_request_correlation_id_propagation():
    """Verify X-Correlation-ID and X-Request-ID are generated and returned in headers."""
    # Custom client correlation ID
    custom_cid = f"test-cid-{uuid4().hex}"
    res = client.get("/", headers={"X-Correlation-ID": custom_cid})
    assert res.status_code == 200
    assert res.headers.get("X-Correlation-ID") == custom_cid
    assert res.headers.get("X-Request-ID") == custom_cid
    assert "X-Response-Time-MS" in res.headers

    # Auto-generated correlation ID when client does not supply one
    auto_res = client.get("/")
    assert auto_res.status_code == 200
    assert "X-Correlation-ID" in auto_res.headers
    assert "X-Request-ID" in auto_res.headers


def test_http_security_headers():
    """Verify production HTTP security headers are injected into API responses."""
    res = client.get("/")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_rate_limiter_service():
    """Verify rate limiter tracks attempts and flags limit violations accurately."""
    test_key = f"test_user_{uuid4().hex[:6]}"

    # Reset state
    rate_limiter.reset_attempts(test_key)

    # Below limit (3 attempts allowed)
    is_limited, _ = rate_limiter.check_rate_limit(test_key, limit=3, window_seconds=60)
    assert is_limited is False

    # Record 3 failures
    for _ in range(3):
        rate_limiter.record_failure(test_key, window_seconds=60)

    # 4th check should be rate limited
    is_limited_now, retry_after = rate_limiter.check_rate_limit(test_key, limit=3, window_seconds=60)
    assert is_limited_now is True
    assert retry_after > 0

    # Reset
    rate_limiter.reset_attempts(test_key)
    is_limited_after_reset, _ = rate_limiter.check_rate_limit(test_key, limit=3, window_seconds=60)
    assert is_limited_after_reset is False
