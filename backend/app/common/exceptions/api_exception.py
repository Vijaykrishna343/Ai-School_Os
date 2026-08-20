from fastapi import HTTPException

from app.common.exceptions.error_codes import ErrorCode


class APIException(HTTPException):
    """
    Base exception for all application exceptions.

    Every custom exception should inherit from this class.
    """

    def __init__(
        self,
        *,
        status_code: int,
        code: ErrorCode | str,
        message: str,
        headers: dict[str, str] | None = None,
    ):
        self.code = code
        self.message = message
        self.headers = headers

        super().__init__(
            status_code=status_code,
            detail=message,
            headers=headers,
        )