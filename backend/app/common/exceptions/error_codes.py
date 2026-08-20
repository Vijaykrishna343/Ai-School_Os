from enum import StrEnum


class ErrorCode(StrEnum):
    """
    Standard error codes used throughout AI School OS.

    These codes provide machine-readable identifiers that
    frontend applications can rely on regardless of the
    displayed message.
    """

    BAD_REQUEST = "BAD_REQUEST"

    VALIDATION_ERROR = "VALIDATION_ERROR"

    NOT_FOUND = "NOT_FOUND"

    ALREADY_EXISTS = "ALREADY_EXISTS"

    UNAUTHORIZED = "UNAUTHORIZED"

    FORBIDDEN = "FORBIDDEN"

    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"

    DATABASE_ERROR = "DATABASE_ERROR"

    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"

    UNKNOWN_ERROR = "UNKNOWN_ERROR"