"""
Thread-safe Prometheus Metrics Collector & Registry — Phase 30.8.

Provides Prometheus exposition format metrics (/metrics) for HTTP request counts,
latency histograms, active requests gauge, database connectivity, and application info.
Enforces strict route path normalization to eliminate high-cardinality label explosion and PII leakage.
"""

import re
import threading
import time
from collections import defaultdict
from typing import Dict, List, Tuple

# Standard Prometheus histogram latency buckets (in seconds)
LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

# UUID and Numeric regex patterns for route normalization
UUID_PATTERN = re.compile(
    r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
NUMERIC_ID_PATTERN = re.compile(r"/\d+(?=/|$)")


def normalize_route_path(path: str) -> str:
    """
    Normalize route paths to prevent high cardinality and PII exposure in metric labels.
    Replaces UUIDs and numeric IDs with '{id}'.
    """
    if not path or path == "/":
        return "/"

    # Strip query parameters if present
    path = path.split("?")[0]

    # Replace UUIDs
    normalized = UUID_PATTERN.sub("/{id}", path)
    # Replace Numeric IDs
    normalized = NUMERIC_ID_PATTERN.sub("/{id}", normalized)

    return normalized


class PrometheusMetricsRegistry:
    """Thread-safe collector for application Prometheus metrics."""

    def __init__(self):
        self._lock = threading.Lock()
        # (method, endpoint, status) -> count
        self._http_requests_total: Dict[Tuple[str, str, str], int] = defaultdict(int)
        # (method, endpoint, bucket_le) -> count
        self._http_request_duration_buckets: Dict[Tuple[str, str, float], int] = defaultdict(int)
        # (method, endpoint) -> (sum_duration, count)
        self._http_request_duration_sum: Dict[Tuple[str, str], float] = defaultdict(float)
        self._http_request_duration_count: Dict[Tuple[str, str], int] = defaultdict(int)
        self._active_requests: int = 0
        self._db_connected: int = 1

    def inc_active_requests(self) -> None:
        with self._lock:
            self._active_requests += 1

    def dec_active_requests(self) -> None:
        with self._lock:
            self._active_requests = max(0, self._active_requests - 1)

    def set_db_connected(self, is_connected: bool) -> None:
        with self._lock:
            self._db_connected = 1 if is_connected else 0

    def record_http_request(
        self, method: str, path: str, status_code: int, duration_seconds: float
    ) -> None:
        endpoint = normalize_route_path(path)
        status_str = str(status_code)
        method_str = method.upper()

        with self._lock:
            self._http_requests_total[(method_str, endpoint, status_str)] += 1
            self._http_request_duration_sum[(method_str, endpoint)] += duration_seconds
            self._http_request_duration_count[(method_str, endpoint)] += 1

            for le in LATENCY_BUCKETS:
                if duration_seconds <= le:
                    self._http_request_duration_buckets[(method_str, endpoint, le)] += 1

    def generate_prometheus_output(
        self, app_version: str = "1.0.0", environment: str = "production"
    ) -> str:
        """Serialize all collected metrics into Prometheus text exposition format (version 0.0.4)."""
        lines: List[str] = []

        with self._lock:
            # 1. App Info Gauge
            lines.append("# HELP school_erp_app_info Application build and runtime environment information.")
            lines.append("# TYPE school_erp_app_info gauge")
            lines.append(
                f'school_erp_app_info{{version="{app_version}",environment="{environment}"}} 1'
            )

            # 2. Database Connectivity Gauge
            lines.append("# HELP school_erp_database_connected Database connectivity health indicator (1=connected, 0=disconnected).")
            lines.append("# TYPE school_erp_database_connected gauge")
            lines.append(f"school_erp_database_connected {self._db_connected}")

            # 3. Active Requests Gauge
            lines.append("# HELP school_erp_http_requests_in_progress Number of currently executing HTTP requests.")
            lines.append("# TYPE school_erp_http_requests_in_progress gauge")
            lines.append(f"school_erp_http_requests_in_progress {self._active_requests}")

            # 4. Total HTTP Requests Counter
            lines.append("# HELP school_erp_http_requests_total Total number of HTTP requests processed by endpoint and status code.")
            lines.append("# TYPE school_erp_http_requests_total counter")
            for (method, endpoint, status), count in sorted(self._http_requests_total.items()):
                lines.append(
                    f'school_erp_http_requests_total{{method="{method}",endpoint="{endpoint}",status="{status}"}} {count}'
                )

            # 5. HTTP Request Duration Histogram
            lines.append("# HELP school_erp_http_request_duration_seconds Latency histogram of HTTP request processing in seconds.")
            lines.append("# TYPE school_erp_http_request_duration_seconds histogram")
            for (method, endpoint), total_count in sorted(self._http_request_duration_count.items()):
                sum_duration = self._http_request_duration_sum[(method, endpoint)]
                running_bucket_count = 0
                for le in LATENCY_BUCKETS:
                    b_count = self._http_request_duration_buckets.get((method, endpoint, le), 0)
                    running_bucket_count = b_count
                    lines.append(
                        f'school_erp_http_request_duration_seconds_bucket{{le="{le}",method="{method}",endpoint="{endpoint}"}} {running_bucket_count}'
                    )
                lines.append(
                    f'school_erp_http_request_duration_seconds_bucket{{le="+Inf",method="{method}",endpoint="{endpoint}"}} {total_count}'
                )
                lines.append(
                    f'school_erp_http_request_duration_seconds_sum{{method="{method}",endpoint="{endpoint}"}} {sum_duration:.6f}'
                )
                lines.append(
                    f'school_erp_http_request_duration_seconds_count{{method="{method}",endpoint="{endpoint}"}} {total_count}'
                )

        lines.append("")  # trailing newline per Prometheus spec
        return "\n".join(lines)


# Global Singleton Metrics Registry
metrics_registry = PrometheusMetricsRegistry()
