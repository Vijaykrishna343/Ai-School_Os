"""
Centralized logging configuration for AI School OS.
Provides structured logging, correlation ID tracking, and sensitive data redaction.
"""

import logging
import sys
import re
from typing import Any

SENSITIVE_KEYS = {
    "password", "password_hash", "token", "access_token", "refresh_token",
    "secret", "api_key", "authorization", "credit_card", "cvv", "salary", "ssn"
}


def sanitize_log_data(data: Any) -> Any:
    """
    Recursively sanitize sensitive key-value pairs in logging dictionaries or strings.
    """
    if isinstance(data, dict):
        sanitized = {}
        for key, val in data.items():
            if any(sens in key.lower() for sens in SENSITIVE_KEYS):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_log_data(val)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_log_data(item) for item in data]
    elif isinstance(data, str):
        # Redact Bearer tokens in raw strings
        return re.sub(r'Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*', 'Bearer [REDACTED]', data)
    return data


class CorrelationIdFilter(logging.Filter):
    """
    Logging filter that injects correlation_id into log records.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "correlation_id"):
            record.correlation_id = getattr(record, "correlation_id", "-")
        return True


def setup_logging(
    level: int = logging.INFO,
) -> None:
    """
    Configure structured production logging for the application.
    """

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | %(levelname)-8s | "
            "[cid:%(correlation_id)s] | "
            "%(name)s | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationIdFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Quieten noisy third-party loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger.
    """
    return logging.getLogger(name)

