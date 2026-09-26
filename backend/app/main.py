"""
Main Application Module.

Configures the FastAPI application instance, middleware, exception handlers,
lifespan management, API routes, and health/readiness endpoints.
"""

import logging
import time
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool

from app.api.v1.api import api_router
from app.common.exceptions import register_exception_handlers
from app.common.logger.logger import get_logger, setup_logging
from app.common.metrics import metrics_registry
from app.common.metrics_auth import verify_metrics_access
from app.core.config import settings


logger = get_logger(__name__)


# -------------------------------------------------------
# Constants
# -------------------------------------------------------

DEFAULT_DEBUG_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
]

DEFAULT_PRODUCTION_ORIGINS = [
    "https://app.schoolos.com",
]

ALLOWED_METHODS = [
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "PATCH",
    "OPTIONS",
]

ALLOWED_HEADERS = [
    "Authorization",
    "Content-Type",
    "X-Tenant-ID",
]


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------


def get_allowed_origins() -> list[str]:
    """
    Normalize the configured CORS origins into a list.

    Supports:
    - list[str]
    - comma-separated string
    - environment-specific defaults
    """
    configured_origins = settings.ALLOWED_ORIGINS

    if isinstance(configured_origins, list):
        return [
            origin.strip()
            for origin in configured_origins
            if isinstance(origin, str) and origin.strip()
        ]

    if isinstance(configured_origins, str):
        return [
            origin.strip()
            for origin in configured_origins.split(",")
            if origin.strip()
        ]

    return (
        DEFAULT_DEBUG_ORIGINS.copy()
        if settings.DEBUG
        else DEFAULT_PRODUCTION_ORIGINS.copy()
    )


async def check_database_connection() -> bool:
    """
    Check database connectivity without blocking the async event loop.

    The current SQLAlchemy engine uses a synchronous connection API, so the
    blocking operation is executed in a worker thread.
    """
    from app.database.session import engine

    def _check() -> bool:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            metrics_registry.set_db_connected(True)
            return True
        except Exception:
            metrics_registry.set_db_connected(False)
            logger.exception("Readiness DB probe failed")
            return False

    return await run_in_threadpool(_check)


# -------------------------------------------------------
# Lifespan
# -------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application startup and shutdown lifecycle manager.
    """
    setup_logging(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
    )

    logger.info("🚀 AI School OS Starting...")

    try:
        from app.database.session import SessionLocal
        from app.repositories.job_repository import job_repository

        with SessionLocal() as db:
            count = job_repository.recover_orphaned_jobs(db)
            if count > 0:
                logger.info("🔄 Recovered %s orphaned background job(s) left in PROCESSING status.", count)
    except Exception as exc:
        logger.warning("Background job recovery check failed on startup: %s", exc)

    yield

    logger.info("🛑 AI School OS Stopped.")



# -------------------------------------------------------
# Application
# -------------------------------------------------------


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


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=ALLOWED_METHODS,
    allow_headers=ALLOWED_HEADERS,
)


@app.middleware("http")
async def correlation_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """
    Inject and propagate X-Correlation-ID and X-Request-ID.

    If the client supplies either header, its value is preserved.
    Otherwise, a UUID is generated.

    Response timing and correlation headers are applied whenever a response
    is successfully produced.
    """
    correlation_id = (
        request.headers.get("X-Correlation-ID")
        or request.headers.get("X-Request-ID")
        or str(uuid.uuid4())
    )

    request.state.correlation_id = correlation_id

    start_time = time.perf_counter()
    metrics_registry.inc_active_requests()

    try:
        response = await call_next(request)
    except Exception:
        duration = time.perf_counter() - start_time
        metrics_registry.dec_active_requests()
        metrics_registry.record_http_request(
            method=request.method,
            path=request.url.path,
            status_code=500,
            duration_seconds=duration,
        )

        process_time_ms = round(duration * 1000, 2)
        logger.exception(
            "HTTP %s %s -> unhandled exception (%sms)",
            request.method,
            request.url.path,
            process_time_ms,
            extra={"correlation_id": correlation_id},
        )

        raise

    duration = time.perf_counter() - start_time
    metrics_registry.dec_active_requests()
    metrics_registry.record_http_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_seconds=duration,
    )

    process_time_ms = round(duration * 1000, 2)
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Request-ID"] = correlation_id
    response.headers["X-Response-Time-MS"] = str(process_time_ms)

    logger.info(
        "HTTP %s %s -> %s (%sms)",
        request.method,
        request.url.path,
        response.status_code,
        process_time_ms,
        extra={"correlation_id": correlation_id},
    )

    return response


CSRF_PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
CSRF_EXEMPT_PATHS = {
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
}


@app.middleware("http")
async def csrf_origin_validation_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """
    CSRF Defense: For state-changing requests carrying cookie authentication,
    validate Origin and Referer headers against trusted origins.
    """
    if request.method in CSRF_PROTECTED_METHODS and request.url.path not in CSRF_EXEMPT_PATHS:
        has_auth_cookie = bool(
            request.cookies.get("access_token") or request.cookies.get("refresh_token")
        )
        if has_auth_cookie:
            origin = request.headers.get("origin")
            referer = request.headers.get("referer")
            sec_fetch_site = request.headers.get("sec-fetch-site")

            # Check explicit cross-site indicator
            if sec_fetch_site == "cross-site":
                logger.warning(
                    "CSRF blocked: Sec-Fetch-Site is cross-site for path %s",
                    request.url.path,
                )
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF verification failed: Cross-site request rejected."},
                )

            allowed = set(get_allowed_origins())
            # Add request's own origin
            server_origin = f"{request.url.scheme}://{request.url.netloc}"
            allowed.add(server_origin)

            request_origin = None
            if origin:
                request_origin = origin.rstrip("/")
            elif referer:
                parsed = urlparse(referer)
                if parsed.scheme and parsed.netloc:
                    request_origin = f"{parsed.scheme}://{parsed.netloc}"

            if request_origin is not None:
                # Compare against allowed origins (normalized without trailing slashes)
                normalized_allowed = {o.rstrip("/") for o in allowed if o}
                if request_origin not in normalized_allowed:
                    logger.warning(
                        "CSRF blocked: Origin '%s' not in allowed origins for path %s",
                        request_origin,
                        request.url.path,
                    )
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "CSRF verification failed: Untrusted Origin."},
                    )

    return await call_next(request)


@app.middleware("http")
async def add_security_headers(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """
    Inject HTTP security headers into responses.
    """
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

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
    Detailed health status endpoint returning application status.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get(
    "/healthz",
    tags=["Health"],
    summary="Liveness Probe",
)
async def healthz() -> dict[str, object]:
    """
    Standard Kubernetes/container liveness probe.
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get(
    "/health/live",
    tags=["Health"],
    summary="Liveness Probe Alias",
)
async def health_live() -> dict[str, object]:
    """
    Kubernetes/container liveness probe alias.
    """
    return await healthz()


@app.get(
    "/readyz",
    tags=["Health"],
    summary="Readiness Probe",
)
async def readyz() -> JSONResponse:
    """
    Standard Kubernetes/container readiness probe.

    Returns 200 only when the application can successfully communicate
    with the database.
    """
    db_ok = await check_database_connection()

    if db_ok:
        return JSONResponse(
            status_code=200,
            content={
                "status": "ready",
                "database": "connected",
            },
        )

    return JSONResponse(
        status_code=503,
        content={
            "status": "not_ready",
            "database": "disconnected",
        },
    )


@app.get(
    "/health/ready",
    tags=["Health"],
    summary="Readiness Probe Alias",
)
async def health_ready() -> JSONResponse:
    """
    Readiness probe alias.
    """
    return await readyz()


# -------------------------------------------------------
# Observability & Metrics
# -------------------------------------------------------


@app.get(
    "/metrics",
    tags=["Observability"],
    summary="Prometheus Metrics Endpoint",
    response_class=Response,
    dependencies=[Depends(verify_metrics_access)],
)
async def prometheus_metrics() -> Response:
    """
    Expose application metrics in standard Prometheus exposition format (version 0.0.4).
    Provides request counts, duration histograms, active requests, DB health, and app info.
    All endpoint labels are normalized to prevent label explosion and PII leakage.
    """
    output = metrics_registry.generate_prometheus_output(
        app_version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )
    return Response(
        content=output,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )