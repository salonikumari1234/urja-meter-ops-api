from typing import Any, Optional
from fastapi import status


class AppException(Exception):
    """Base exception for all application errors."""
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Any] = None
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class AuthenticationError(AppException):
    def __init__(self, message: str = "Invalid or missing API key", details: Optional[Any] = None):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class ResourceNotFoundError(AppException):
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=f"{resource} with identifier '{identifier}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )


class UpstreamServiceError(AppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            code="UPSTREAM_SERVICE_ERROR",
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )


class UpstreamTimeoutError(AppException):
    def __init__(self, message: str = "Upstream Urja portal timed out responding to request."):
        super().__init__(
            code="UPSTREAM_TIMEOUT",
            message=message,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT
        )


class ValidationError(AppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class RateLimitExceededError(AppException):
    def __init__(self, message: str = "Rate limit exceeded. Please retry after some time."):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )
