"""
Prometheus Metrics Authentication Dependency — Phase F.

Secures the Prometheus /metrics endpoint against unauthorized public access.
Supports HTTP Bearer token and HTTP Basic authentication for Prometheus scrapers.
Uses constant-time comparison (secrets.compare_digest) to prevent timing side-channel attacks.
"""

import base64
import secrets

from fastapi import HTTPException, Request, status

from app.core.config import settings


def verify_metrics_access(request: Request) -> bool:
    """
    FastAPI dependency that enforces authentication for Prometheus metrics scraping.
    Validates either:
      1. HTTP Bearer Token against settings.METRICS_AUTH_TOKEN
      2. HTTP Basic Auth against settings.METRICS_USERNAME & settings.METRICS_PASSWORD
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for metrics endpoint.",
            headers={"WWW-Authenticate": 'Bearer realm="metrics", Basic realm="metrics"'},
        )

    scheme, _, credentials = auth_header.partition(" ")
    scheme = scheme.lower()

    # 1. HTTP Bearer Token Authentication
    if scheme == "bearer" and settings.METRICS_AUTH_TOKEN:
        if secrets.compare_digest(credentials, settings.METRICS_AUTH_TOKEN):
            return True

    # 2. HTTP Basic Authentication
    elif scheme == "basic" and settings.METRICS_USERNAME and settings.METRICS_PASSWORD:
        try:
            decoded = base64.b64decode(credentials).decode("utf-8")
            username, _, password = decoded.partition(":")
            if secrets.compare_digest(
                username, settings.METRICS_USERNAME
            ) and secrets.compare_digest(password, settings.METRICS_PASSWORD):
                return True
        except Exception:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid monitoring credentials.",
        headers={"WWW-Authenticate": 'Bearer realm="metrics", Basic realm="metrics"'},
    )
