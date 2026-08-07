import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.common.exceptions import register_exception_handlers
from app.common.logger.logger import setup_logging
from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
async def root():
    return {
        "success": True,
        "message": "Welcome to AI School OS 🚀",
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Detailed Health Check",
)
async def health():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
    }