"""
Unit and Integration Tests for Phase L: Production Observability, Request Correlation,
Safe Logging, and Health/Readiness Semantics.
"""

import pytest
from fastapi.testclient import TestClient

from app.common.logger.logger import sanitize_log_data
from app.core.config import settings
from app.main import app


class TestObservabilityAndCorrelation:
    @pytest.fixture(autouse=True)
    def setup_client(self):
        self.client = TestClient(app)

    def test_request_generates_correlation_and_request_id(self):
        """When client does not provide correlation headers, new UUIDs are generated and returned."""
        response = self.client.get("/healthz")
        assert response.status_code == 200
        assert "X-Correlation-ID" in response.headers
        assert "X-Request-ID" in response.headers
        assert "X-Response-Time-MS" in response.headers

        cid = response.headers["X-Correlation-ID"]
        assert len(cid) > 10
        assert response.headers["X-Request-ID"] == cid

    def test_request_preserves_client_correlation_id(self):
        """When client supplies X-Correlation-ID, the server propagates it in response headers."""
        custom_cid = "client-trace-id-12345-67890"
        response = self.client.get("/healthz", headers={"X-Correlation-ID": custom_cid})
        assert response.status_code == 200
        assert response.headers["X-Correlation-ID"] == custom_cid
        assert response.headers["X-Request-ID"] == custom_cid

    def test_request_preserves_client_request_id_fallback(self):
        """When client supplies X-Request-ID without X-Correlation-ID, it is adopted as correlation ID."""
        custom_req_id = "req-id-abcde-998877"
        response = self.client.get("/healthz", headers={"X-Request-ID": custom_req_id})
        assert response.status_code == 200
        assert response.headers["X-Correlation-ID"] == custom_req_id
        assert response.headers["X-Request-ID"] == custom_req_id

    def test_liveness_probe_semantics(self):
        """Liveness probes (/health, /healthz, /health/live) return 200 OK without database query."""
        for path in ["/health", "/healthz", "/health/live"]:
            resp = self.client.get(path)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] in ("ok", "healthy")

    def test_readiness_probe_semantics(self):
        """Readiness probes (/readyz, /health/ready) verify database connectivity."""
        for path in ["/readyz", "/health/ready"]:
            resp = self.client.get(path)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ready"
            assert data["database"] == "connected"

    def test_metrics_endpoint_rejects_anonymous(self):
        """Metrics endpoint requires authentication and rejects anonymous scraping."""
        resp = self.client.get("/metrics")
        assert resp.status_code == 401

    def test_metrics_endpoint_accepts_valid_token(self):
        """Metrics endpoint returns Prometheus exposition format when presented with valid token."""
        headers = {"Authorization": f"Bearer {settings.METRICS_AUTH_TOKEN}"}
        resp = self.client.get("/metrics", headers=headers)
        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]
        assert "school_erp_http_requests_total" in resp.text

    def test_sanitize_log_data_redacts_sensitive_keys(self):
        """Sensitive dictionary keys and tokens are securely redacted before logging."""
        raw_payload = {
            "username": "teacher@school.edu",
            "password": "SuperSecretPassword123!",
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy",
            "api_key": "live_key_998877",
            "user_metadata": {
                "role": "TEACHER",
                "secret": "top_secret_value",
            },
            "allowed_notes": "Clean message",
        }

        sanitized = sanitize_log_data(raw_payload)
        assert sanitized["username"] == "teacher@school.edu"
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["access_token"] == "[REDACTED]"
        assert sanitized["api_key"] == "[REDACTED]"
        assert sanitized["user_metadata"]["role"] == "TEACHER"
        assert sanitized["user_metadata"]["secret"] == "[REDACTED]"
        assert sanitized["allowed_notes"] == "Clean message"

    def test_sanitize_log_data_redacts_bearer_string(self):
        """Raw strings containing Bearer tokens have token values redacted."""
        raw_string = "Request authorization failed with Authorization: Bearer abc123def456xyz"
        sanitized = sanitize_log_data(raw_string)
        assert "Bearer [REDACTED]" in sanitized
        assert "abc123def456xyz" not in sanitized
