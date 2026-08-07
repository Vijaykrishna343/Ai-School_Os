"""
Centralized logging configuration for AI School OS.
"""

import logging
import sys


def setup_logging(
    level: int = logging.INFO,
) -> None:
    """
    Configure structured logging for the application.

    Call this once during application startup.
    """

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | %(levelname)-8s | "
            "%(name)s | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Quieten noisy third-party loggers
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.WARNING
    )
    logging.getLogger("uvicorn.access").setLevel(
        logging.INFO
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger.

    Usage:
        from app.common.logger.logger import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)
