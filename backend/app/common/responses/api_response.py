from typing import Any


class ApiResponse:
    """
    Standard API response helper.
    """

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
    ) -> dict:

        return {
            "success": True,
            "message": message,
            "data": data,
        }

    @staticmethod
    def error(
        message: str,
        data: Any = None,
    ) -> dict:

        return {
            "success": False,
            "message": message,
            "data": data,
        }