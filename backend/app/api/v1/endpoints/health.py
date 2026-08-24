"""
Production Health & Readiness Probes — Phase 3 Workstream 1.

Provides /healthz (liveness probe) and /readyz (readiness probe with DB ping).
"""

import os
from typing import Any
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dependencies import get_db

router = APIRouter()


@router.get(
    "/healthz",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
)
def liveness_probe() -> dict[str, Any]:
    """
    Lightweight liveness check for container orchestrators (Kubernetes / ECS).
    Returns HTTP 200 if process is running.
    """
    return {
        "status": "ok",
        "app": "AI School OS",
        "version": "1.0.0",
        "service": "backend",
    }


@router.get(
    "/readyz",
    response_model=dict[str, Any],
    summary="Readiness Probe",
)
def readiness_probe(
    response: Response,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Deep readiness check for container orchestrators.
    Performs database ping (SELECT 1) and verifies storage access.
    Returns HTTP 200 when ready, HTTP 503 Service Unavailable when DB is unreachable.
    """
    # 1. Database Connectivity Check
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unreachable: {str(exc)}"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    # 2. Storage Directory Check
    storage_path = os.getenv("STORAGE_PATH", "./storage/documents")
    storage_status = "ok"
    try:
        if not os.path.exists(storage_path):
            os.makedirs(storage_path, exist_ok=True)
    except Exception as exc:
        storage_status = f"error: {str(exc)}"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    is_ready = db_status == "ok" and storage_status == "ok"
    overall_status = "ready" if is_ready else "not_ready"

    return {
        "status": overall_status,
        "database": db_status,
        "storage": storage_status,
    }
