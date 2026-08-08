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
    Detailed health status endpoint returning app version and debug status.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
    }