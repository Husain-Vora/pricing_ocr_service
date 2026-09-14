"""
Common error model.

Every error response this API returns follows the frozen contract:

{
  "error": {
    "code": "S3_OBJECT_NOT_FOUND",
    "message": "Receipt object was not found.",
    "request_id": "uuid",
    "details": {}
  }
}

Routes/services raise AppError (or a subclass); a single exception handler
in main.py converts it to that JSON shape. No AWS credentials, local file
paths, raw stack traces or model internals are ever placed in `message`
or `details`.
"""
from typing import Any, Dict, Optional

from fastapi import status


class AppError(Exception):
    """Base application error. Carries an HTTP status and a stable code."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ValidationAppError(AppError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class S3ObjectNotFoundError(AppError):
    def __init__(self, message: str = "Receipt object was not found.") -> None:
        super().__init__(
            code="S3_OBJECT_NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class UnsupportedFileTypeError(AppError):
    def __init__(self, message: str = "Object content type is not supported.") -> None:
        super().__init__(
            code="UNSUPPORTED_FILE_TYPE",
            message=message,
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )


class ObjectTooLargeError(AppError):
    def __init__(self, message: str = "Object exceeds the configured size limit.") -> None:
        super().__init__(
            code="OBJECT_TOO_LARGE",
            message=message,
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )


class NotImplementedYetError(AppError):
    """Used by stub services for phases not yet built."""

    def __init__(self, phase_hint: str) -> None:
        super().__init__(
            code="NOT_IMPLEMENTED",
            message=f"Not implemented yet ({phase_hint}).",
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
        )
