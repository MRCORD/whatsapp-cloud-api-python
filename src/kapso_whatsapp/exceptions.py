"""
Kapso WhatsApp SDK Exceptions

Custom exception hierarchy for handling WhatsApp Cloud API errors with
detailed error information, retry guidance, and error categorization.

Ported from flowers-backend with enhancements from TypeScript SDK.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class ErrorCategory(str, Enum):
    """Error category for classification and handling."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    VALIDATION = "validation"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    SERVER_ERROR = "server_error"
    NETWORK = "network"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class RetryAction(str, Enum):
    """Recommended retry action."""

    RETRY_IMMEDIATELY = "retry_immediately"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    RETRY_AFTER_DELAY = "retry_after_delay"
    DO_NOT_RETRY = "do_not_retry"


class WhatsAppAPIError(Exception):
    """
    Base exception for all WhatsApp Cloud API errors.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code (if applicable)
        error_code: Meta/Kapso error code
        error_subcode: Meta error subcode (for detailed classification)
        response: Full API response body
        category: Error category for handling logic
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: str | int | None = None,
        error_subcode: int | None = None,
        response: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.error_subcode = error_subcode
        self.response = response or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"status={self.status_code}")
        if self.error_code:
            parts.append(f"code={self.error_code}")
        if self.error_subcode:
            parts.append(f"subcode={self.error_subcode}")
        return " | ".join(parts)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code}, "
            f"error_code={self.error_code})"
        )

    @property
    def category(self) -> ErrorCategory:
        """Categorize the error for handling logic."""
        if self.status_code == 401:
            return ErrorCategory.AUTHENTICATION
        if self.status_code == 403:
            return ErrorCategory.AUTHORIZATION
        if self.status_code == 404:
            return ErrorCategory.NOT_FOUND
        if self.status_code == 409:
            return ErrorCategory.CONFLICT
        if self.status_code == 429:
            return ErrorCategory.RATE_LIMIT
        if self.status_code == 400:
            return ErrorCategory.VALIDATION
        if self.status_code and 500 <= self.status_code < 600:
            return ErrorCategory.SERVER_ERROR
        return ErrorCategory.UNKNOWN

    @property
    def is_retryable(self) -> bool:
        """Check if this error is retryable."""
        return self.retry_action != RetryAction.DO_NOT_RETRY

    @property
    def retry_action(self) -> RetryAction:
        """Get recommended retry action."""
        if self.status_code in (500, 502, 503, 504):
            return RetryAction.RETRY_WITH_BACKOFF
        if self.status_code == 429:
            return RetryAction.RETRY_AFTER_DELAY
        if self.category in (ErrorCategory.NETWORK, ErrorCategory.TIMEOUT):
            return RetryAction.RETRY_WITH_BACKOFF
        return RetryAction.DO_NOT_RETRY


class AuthenticationError(WhatsAppAPIError):
    """
    Authentication failed - invalid or expired token.

    This error is not retryable without obtaining new credentials.
    """

    def __init__(self, message: str = "Authentication failed", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)

    @property
    def category(self) -> ErrorCategory:
        return ErrorCategory.AUTHENTICATION

    @property
    def retry_action(self) -> RetryAction:
        return RetryAction.DO_NOT_RETRY


class AuthorizationError(WhatsAppAPIError):
    """
    Authorization failed - insufficient permissions.

    Check that the token has the required scopes/permissions.
    """

    def __init__(self, message: str = "Authorization failed", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)

    @property
    def category(self) -> ErrorCategory:
        return ErrorCategory.AUTHORIZATION

    @property
    def retry_action(self) -> RetryAction:
        return RetryAction.DO_NOT_RETRY


class RateLimitError(WhatsAppAPIError):
    """
    Rate limit exceeded.

    Attributes:
        retry_after: Seconds to wait before retrying (from Retry-After header)
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: int | None = None,
        status_code: int | None = None,
        error_code: str | int | None = None,
        error_subcode: int | None = None,
        response: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            error_code=error_code,
            error_subcode=error_subcode,
            response=response,
        )
        self.retry_after = retry_after

    @property
    def category(self) -> ErrorCategory:
        return ErrorCategory.RATE_LIMIT

    @property
    def retry_action(self) -> RetryAction:
        return RetryAction.RETRY_AFTER_DELAY


class ValidationError(WhatsAppAPIError):
    """
    Request validation failed.

    The request payload is malformed or contains invalid data.
    Fix the request before retrying.
    """

    def __init__(
        self,
        message: str = "Validation failed",
        *,
        field: str | None = None,
        status_code: int | None = None,
        error_code: str | int | None = None,
        error_subcode: int | None = None,
        response: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            error_code=error_code,
            error_subcode=error_subcode,
            response=response,
        )
        self.field = field

    @property
    def category(self) -> ErrorCategory:
        return ErrorCategory.VALIDATION

    @property
    def retry_action(self) -> RetryAction:
        return RetryAction.DO_NOT_RETRY


class NotFoundError(WhatsAppAPIError):
    """
    Resource not found.

    The requested resource (message, template, media, etc.) does not exist.
    """

    def __init__(self, message: str = "Resource not found", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)

    @property
    def category(self) -> ErrorCategory:
        return ErrorCategory.NOT_FOUND

    @property
    def retry_action(self) -> RetryAction:
        return RetryAction.DO_NOT_RETRY


class NetworkError(WhatsAppAPIError):
    """
    Network connectivity error.

    Failed to connect to the API. Check network connectivity.
    """

    def __init__(self, message: str = "Network error", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)

    @property
    def category(self) -> ErrorCategory:
        return ErrorCategory.NETWORK

    @property
    def retry_action(self) -> RetryAction:
        return RetryAction.RETRY_WITH_BACKOFF


class TimeoutError(WhatsAppAPIError):
    """
    Request timeout.

    The request took too long to complete.
    """

    def __init__(self, message: str = "Request timeout", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)

    @property
    def category(self) -> ErrorCategory:
        return ErrorCategory.TIMEOUT

    @property
    def retry_action(self) -> RetryAction:
        return RetryAction.RETRY_WITH_BACKOFF


class KapsoProxyRequiredError(WhatsAppAPIError):
    """
    Operation requires Kapso proxy.

    Some operations (conversations, contacts, calls, message history)
    are only available when using the Kapso proxy.
    """

    def __init__(
        self,
        message: str = "This operation requires Kapso proxy. Set base_url and kapso_api_key.",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)

    @property
    def category(self) -> ErrorCategory:
        return ErrorCategory.VALIDATION

    @property
    def retry_action(self) -> RetryAction:
        return RetryAction.DO_NOT_RETRY


class MessageWindowError(WhatsAppAPIError):
    """
    Outside 24-hour messaging window.

    Free-form messages can only be sent within 24 hours of user's last message.
    Use a template message instead.
    """

    def __init__(
        self,
        message: str = "Outside 24-hour messaging window. Use a template message.",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)

    @property
    def category(self) -> ErrorCategory:
        return ErrorCategory.VALIDATION

    @property
    def retry_action(self) -> RetryAction:
        return RetryAction.DO_NOT_RETRY


def categorize_error(
    status_code: int,
    response: dict[str, Any] | None = None,
) -> WhatsAppAPIError:
    """
    Create appropriate exception based on status code and response.

    Args:
        status_code: HTTP status code
        response: API response body

    Returns:
        Appropriate WhatsAppAPIError subclass instance
    """
    response = response or {}
    error_data = response.get("error", {})

    # Handle case where error is a string
    if isinstance(error_data, str):
        message = error_data
        error_code = None
        error_subcode = None
    else:
        message = error_data.get("message", f"Request failed with status {status_code}")
        error_code = error_data.get("code")
        error_subcode = error_data.get("error_subcode")

    # Check for 24-hour window error
    if status_code == 422 and "24-hour" in message.lower():
        return MessageWindowError(
            message,
            status_code=status_code,
            error_code=error_code,
            error_subcode=error_subcode,
            response=response,
        )

    # Map status codes to exceptions
    if status_code == 401:
        return AuthenticationError(
            message,
            status_code=status_code,
            error_code=error_code,
            error_subcode=error_subcode,
            response=response,
        )
    if status_code == 403:
        return AuthorizationError(
            message,
            status_code=status_code,
            error_code=error_code,
            error_subcode=error_subcode,
            response=response,
        )
    if status_code == 404:
        return NotFoundError(
            message,
            status_code=status_code,
            error_code=error_code,
            error_subcode=error_subcode,
            response=response,
        )
    if status_code == 429:
        return RateLimitError(
            message,
            status_code=status_code,
            error_code=error_code,
            error_subcode=error_subcode,
            response=response,
        )
    if status_code == 400 or status_code == 422:
        return ValidationError(
            message,
            status_code=status_code,
            error_code=error_code,
            error_subcode=error_subcode,
            response=response,
        )

    return WhatsAppAPIError(
        message,
        status_code=status_code,
        error_code=error_code,
        error_subcode=error_subcode,
        response=response,
    )
