"""Backend-specific error types.

This module defines errors that can occur during backend operations.
These errors provide meaningful context for troubleshooting and
enable graceful degradation when backends are unavailable.
"""

from __future__ import annotations

from truthound_dashboard.core.exceptions import (
    ErrorCode,
    TruthoundDashboardError,
)


class BackendError(TruthoundDashboardError):
    """Base error for backend operations.

    All backend-specific errors inherit from this class.
    """

    code = ErrorCode.INTERNAL_ERROR
    http_status = 500

    def __init__(
        self,
        message: str,
        *,
        backend_name: str | None = None,
        operation: str | None = None,
        **kwargs,
    ) -> None:
        """Initialize backend error.

        Args:
            message: Error message.
            backend_name: Name of the backend that failed.
            operation: Operation that was being performed.
            **kwargs: Additional context.
        """
        super().__init__(message, **kwargs)
        self.backend_name = backend_name
        self.operation = operation


class BackendUnavailableError(BackendError):
    """Backend library is not installed or unavailable.

    This error is raised when the required backend library (e.g., truthound)
    is not installed or cannot be imported.

    Example:
        try:
            import truthound
        except ImportError:
            raise BackendUnavailableError("truthound", "Library not installed")
    """

    code = ErrorCode.INTERNAL_ERROR
    http_status = 503  # Service Unavailable

    def __init__(
        self,
        backend_name: str,
        message: str | None = None,
        **kwargs,
    ) -> None:
        """Initialize unavailable error.

        Args:
            backend_name: Name of the unavailable backend.
            message: Optional additional message.
            **kwargs: Additional context.
        """
        msg = f"Backend '{backend_name}' is not available"
        if message:
            msg = f"{msg}: {message}"
        super().__init__(msg, backend_name=backend_name, **kwargs)


class BackendVersionError(BackendError):
    """Backend version is incompatible.

    This error is raised when the installed backend library version
    is incompatible with the dashboard's expected API.

    Example:
        if truthound.__version__ < "2.0":
            raise BackendVersionError("truthound", "2.0", truthound.__version__)
    """

    code = ErrorCode.INTERNAL_ERROR
    http_status = 500

    def __init__(
        self,
        backend_name: str,
        required_version: str | None = None,
        current_version: str | None = None,
        message: str | None = None,
        **kwargs,
    ) -> None:
        """Initialize version error.

        Args:
            backend_name: Name of the backend.
            required_version: Minimum required version.
            current_version: Currently installed version.
            message: Optional additional message.
            **kwargs: Additional context.
        """
        msg = f"Backend '{backend_name}' version incompatibility"
        if required_version and current_version:
            msg = f"{msg}: requires >={required_version}, found {current_version}"
        elif message:
            msg = f"{msg}: {message}"
        super().__init__(msg, backend_name=backend_name, **kwargs)
        self.required_version = required_version
        self.current_version = current_version


class BackendOperationError(BackendError):
    """Backend operation failed.

    This error wraps exceptions that occur during backend operations,
    providing context about what operation was being performed.

    Example:
        try:
            result = th.check(data)
        except Exception as e:
            raise BackendOperationError("truthound", "check", str(e))
    """

    code = ErrorCode.INTERNAL_ERROR
    http_status = 500

    def __init__(
        self,
        backend_name: str,
        operation: str,
        message: str,
        *,
        original_error: Exception | None = None,
        **kwargs,
    ) -> None:
        """Initialize operation error.

        Args:
            backend_name: Name of the backend.
            operation: Operation that failed.
            message: Error message.
            original_error: Original exception if available.
            **kwargs: Additional context.
        """
        msg = f"Backend '{backend_name}' operation '{operation}' failed: {message}"
        super().__init__(msg, backend_name=backend_name, operation=operation, **kwargs)
        self.original_error = original_error


class BackendConfigError(BackendError):
    """Backend configuration is invalid.

    This error is raised when backend configuration is missing or invalid.
    """

    code = ErrorCode.VALIDATION_ERROR
    http_status = 400

    def __init__(
        self,
        backend_name: str,
        config_key: str | None = None,
        message: str | None = None,
        **kwargs,
    ) -> None:
        """Initialize config error.

        Args:
            backend_name: Name of the backend.
            config_key: Configuration key that's invalid.
            message: Optional additional message.
            **kwargs: Additional context.
        """
        msg = f"Backend '{backend_name}' configuration error"
        if config_key:
            msg = f"{msg}: invalid '{config_key}'"
        if message:
            msg = f"{msg}: {message}"
        super().__init__(msg, backend_name=backend_name, **kwargs)
        self.config_key = config_key
