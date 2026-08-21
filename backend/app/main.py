"""
Main Application Module.

Configures FastAPI application instance, CORS middleware, global exception handlers,
lifespan event management, and root health check endpoints.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.common.exceptions import register_exception_handlers
from app.common.logger.logger import get_logger, setup_logging
from app.core.config import settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application startup and shutdown events lifecycle manager.
    """

    setup_logging(
        level=(
            logging.DEBUG
            if settings.DEBUG
            else logging.INFO
        ),
    )

    logger.info("🚀 AI School OS Starting...")

    yield

    logger.info("🛑 AI School OS Stopped.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# -------------------------------------------------------
# Middleware
# -------------------------------------------------------

if isinstance(settings.ALLOWED_ORIGINS, list):
    allowed_origins = settings.ALLOWED_ORIGINS
elif isinstance(settings.ALLOWED_ORIGINS, str):
    allowed_origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
else:
    allowed_origins = (
        ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"]
        if settings.DEBUG
        else ["https://app.schoolos.com"]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Tenant-ID"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """Inject production HTTP security headers into all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# -------------------------------------------------------
# Exception Handlers
# -------------------------------------------------------

register_exception_handlers(app)

# -------------------------------------------------------
# API Routes
# -------------------------------------------------------

app.include_router(
    api_router,
    prefix="/api/v1",
)


# -------------------------------------------------------
# Health Check
# -------------------------------------------------------


@app.get(
    "/",
    tags=["Health"],
    summary="Health Check",
)
async def root() -> dict[str, object]:
    """
    Root health check endpoint returning welcome message.
    """
    return {
        "success": True,
        "message": "Welcome to AI School OS 🚀",
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Detailed Health Check",
)
async def health() -> dict[str, object]:
    """
    Detailed health status endpoint returning app status.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get(
    "/health/live",
    tags=["Health"],
    summary="Liveness Probe",
)
async def health_live() -> dict[str, object]:
    """
    K8s / Container Liveness probe.
    """
    return {"status": "alive"}


@app.get(
    "/health/ready",
    tags=["Health"],
    summary="Readiness Probe",
)
async def health_ready() -> JSONResponse:
    """
    K8s / Container Readiness probe checking DB connectivity.
    """
    from sqlalchemy import text
    from app.database.session import engine

    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception as e:
        logger.error("Readiness DB probe failed", error=str(e))

    if db_ok:
        return JSONResponse(
            status_code=200,
            content={"status": "ready", "database": "connected"},
        )
    else:
        return JSONResponse(
            status_code=530 if False else 503,
            content={"status": "not_ready", "database": "disconnected"},
        )