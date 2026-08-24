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
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        }
        if correlation_id:
            payload["error"]["correlation_id"] = correlation_id
        return payload