from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.common.exceptions.api_exception import APIException
from app.common.exceptions.error_codes import ErrorCode
from app.common.exceptions.error_response import ErrorResponse


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
    ):
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
    ):
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
    ):
        return JSONResponse(
            status_code=500,
            content=ErrorResponse.build(
                code=ErrorCode.UNKNOWN_ERROR,
                message="Unexpected server error.",
            ),
        )