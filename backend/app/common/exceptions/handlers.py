from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.common.exceptions.api_exception import APIException
from app.common.exceptions.error_codes import ErrorCode
from app.common.exceptions.error_response import ErrorResponse
from app.common.logger.logger import get_logger, sanitize_log_data

logger = get_logger(__name__)


def register_exception_handlers(
    app: FastAPI,
) -> None:
    """
    Register standardized production exception handlers.
    Injects X-Correlation-ID headers and response payloads.
    Guarantees no internal stack traces or secrets leak to callers.
    """

    @app.exception_handler(APIException)
    async def api_exception_handler(
        request: Request,
        exc: APIException,
    ) -> JSONResponse:
        cid = getattr(request.state, "correlation_id", None)
        logger.warning(
            "API Exception [cid:%s] [%s %s] Status: %s Code: %s Message: %s",
            cid or "-",
            request.method,
            request.url.path,
            exc.status_code,
            exc.code,
            exc.message,
            extra={"correlation_id": cid or "-"},
        )
        headers = dict(exc.headers or {})
        if cid:
            headers["X-Correlation-ID"] = cid
            headers["X-Request-ID"] = cid

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse.build(
                code=exc.code,
                message=exc.message,
                correlation_id=cid,
            ),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        cid = getattr(request.state, "correlation_id", None)
        sanitized_errors = sanitize_log_data(exc.errors())
        logger.warning(
            "Validation Failure [cid:%s] [%s %s]: %s",
            cid or "-",
            request.method,
            request.url.path,
            str(sanitized_errors),
            extra={"correlation_id": cid or "-"},
        )
        headers = {}
        if cid:
            headers["X-Correlation-ID"] = cid
            headers["X-Request-ID"] = cid

        return JSONResponse(
            status_code=422,
            content=ErrorResponse.build(
                code=ErrorCode.VALIDATION_ERROR,
                message="Validation failed.",
                correlation_id=cid,
            ),
            headers=headers,
        )

    @app.exception_handler(Exception)
    async def unknown_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        cid = getattr(request.state, "correlation_id", None)
        logger.error(
            "Unexpected Exception [cid:%s] [%s %s]: %s",
            cid or "-",
            request.method,
            request.url.path,
            str(exc),
            exc_info=True,
            extra={"correlation_id": cid or "-"},
        )
        headers = {}
        if cid:
            headers["X-Correlation-ID"] = cid
            headers["X-Request-ID"] = cid

        return JSONResponse(
            status_code=500,
            content=ErrorResponse.build(
                code=ErrorCode.UNKNOWN_ERROR,
                message="Unexpected server error.",
                correlation_id=cid,
            ),
            headers=headers,
        )