from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.common.exceptions.api_exception import APIException
from app.common.exceptions.error_codes import ErrorCode
from app.common.exceptions.error_response import ErrorResponse
from app.common.logger.logger import get_logger

logger = get_logger(__name__)


def register_exception_handlers(
    app: FastAPI,
) -> None:
    """
    Register global exception handlers.
    """

    @app.exception_handler(APIException)
    async def api_exception_handler(
        request: Request,
        exc: APIException,
    ) -> JSONResponse:
        logger.warning(
            "API Exception [%s %s] Status: %s Code: %s Message: %s",
            request.method,
            request.url.path,
            exc.status_code,
            exc.code,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse.build(
                code=exc.code,
                message=exc.message,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        logger.warning(
            "Validation Failure [%s %s]: %s",
            request.method,
            request.url.path,
            str(exc.errors()),
        )
        return JSONResponse(
            status_code=422,
            content=ErrorResponse.build(
                code=ErrorCode.VALIDATION_ERROR,
                message="Validation failed.",
            ),
        )

    @app.exception_handler(Exception)
    async def unknown_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.error(
            "Unexpected Exception [%s %s]: %s",
            request.method,
            request.url.path,
            str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content=ErrorResponse.build(
                code=ErrorCode.UNKNOWN_ERROR,
                message="Unexpected server error.",
            ),
        )