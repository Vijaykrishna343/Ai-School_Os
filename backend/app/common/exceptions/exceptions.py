from fastapi import status

from app.common.exceptions.api_exception import APIException
from app.common.exceptions.error_codes import ErrorCode


class BadRequestException(APIException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.BAD_REQUEST,
            message=message,
        )


class ValidationException(APIException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
        )


class UnauthorizedException(APIException):
    def __init__(
        self,
        message: str = "Authentication required.",
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.UNAUTHORIZED,
            message=message,
        )


class ForbiddenException(APIException):
    def __init__(
        self,
        message: str = "Permission denied.",
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.FORBIDDEN,
            message=message,
        )


class NotFoundException(APIException):
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found."
        if identifier:
            message = f"{resource} with identifier '{identifier}' not found."
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.NOT_FOUND,
            message=message,
        )


class AlreadyExistsException(APIException):
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} already exists."
        if identifier:
            message = f"{resource} with identifier '{identifier}' already exists."
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.ALREADY_EXISTS,
            message=message,
        )


class InternalServerException(APIException):
    def __init__(
        self,
        message: str = "Internal server error.",
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=message,
        )