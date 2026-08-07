from typing import Any

from app.common.exceptions.error_codes import ErrorCode


class ErrorResponse:
    """
    Builds a standardized error response.
    """

    @staticmethod
    def build(
        *,
        code: ErrorCode,
        message: str,
    ) -> dict[str, Any]:
        return {
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        }