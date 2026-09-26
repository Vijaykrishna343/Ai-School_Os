"""
Tests for Prometheus Observability & Metrics (Phase 30.8).
"""

import pytest
from fastapi.testclient import TestClient

from app.common.metrics import (
    PrometheusMetricsRegistry,
    normalize_route_path,
)
from app.main import app


from app.core.config import settings


class TestPrometheusMetrics:
    def test_normalize_route_path(self):
        # UUID normalization
        uuid_url = "/api/v1/students/a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
        assert normalize_route_path(uuid_url) == "/api/v1/students/{id}"

        uuid_nested = "/api/v1/schools/a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d/classes/12345"
        assert normalize_route_path(uuid_nested) == "/api/v1/schools/{id}/classes/{id}"

        # Numeric ID normalization
        numeric_url = "/api/v1/orders/12345/items"
        assert normalize_route_path(numeric_url) == "/api/v1/orders/{id}/items"

        # Query parameter stripping
        query_url = "/api/v1/students?page=1&limit=20&search=john"
        assert normalize_route_path(query_url) == "/api/v1/students"

        # Root and clean static paths
        assert normalize_route_path("/") == "/"
        assert normalize_route_path("/health/ready") == "/health/ready"

    def test_registry_metrics_generation(self):
        registry = PrometheusMetricsRegistry()
        registry.set_db_connected(True)
        registry.inc_active_requests()

        registry.record_http_request("GET", "/api/v1/students/123", 200, 0.045)
        registry.record_http_request("POST", "/api/v1/payments/webhooks/razorpay", 200, 0.082)
        registry.record_http_request("GET", "/api/v1/students/456", 404, 0.012)

        registry.dec_active_requests()

        output = registry.generate_prometheus_output(app_version="1.0.0", environment="production")

        assert "# HELP school_erp_http_requests_total" in output
        assert "# TYPE school_erp_http_requests_total counter" in output
        assert 'school_erp_http_requests_total{method="GET",endpoint="/api/v1/students/{id}",status="200"} 1' in output
        assert 'school_erp_http_requests_total{method="POST",endpoint="/api/v1/payments/webhooks/razorpay",status="200"} 1' in output
        assert 'school_erp_http_requests_total{method="GET",endpoint="/api/v1/students/{id}",status="404"} 1' in output

        assert "# HELP school_erp_http_request_duration_seconds" in output
        assert "# TYPE school_erp_http_request_duration_seconds histogram" in output
        assert 'school_erp_http_request_duration_seconds_count{method="GET",endpoint="/api/v1/students/{id}"} 2' in output

        assert "school_erp_database_connected 1" in output
        assert 'school_erp_app_info{version="1.0.0",environment="production"} 1' in output

    def test_metrics_endpoint_integration(self):
        client = TestClient(app)

        # Generate some traffic
        client.get("/")
        client.get("/health/live")

        # Anonymous access must be rejected (401)
        anon_resp = client.get("/metrics")
        assert anon_resp.status_code == 401

        # Invalid token must be rejected (401)
        invalid_resp = client.get("/metrics", headers={"Authorization": "Bearer wrong-token"})
        assert invalid_resp.status_code == 401

        # Valid monitoring credentials must succeed (200)
        auth_headers = {"Authorization": f"Bearer {settings.METRICS_AUTH_TOKEN}"}
        resp = client.get("/metrics", headers=auth_headers)
        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]
        assert "version=0.0.4" in resp.headers["content-type"]

        body = resp.text
        assert "school_erp_app_info" in body
        assert "school_erp_database_connected" in body
        assert "school_erp_http_requests_total" in body
        assert 'method="GET",endpoint="/"' in body or 'method="GET",endpoint="/health/live"' in body
