"""Backend factory for data quality backends.

This module provides a factory for creating and managing data quality
backends. It supports registration of custom backends and automatic
fallback when the primary backend is unavailable.

Key Features:
- Lazy initialization of built-in backends
- Automatic fallback to mock backend when truthound unavailable
- Instance caching for efficiency
- Backend version detection
- Capability reporting for feature detection
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .errors import BackendUnavailableError

if TYPE_CHECKING:
    from .base import BaseDataQualityBackend

logger = logging.getLogger(__name__)


class BackendFactory:
    """Factory for creating data quality backends.

    The factory manages backend registration and instantiation with
    support for automatic fallback when backends are unavailable.

    Class Attributes:
        _backends: Registry of backend classes by name.
        _instances: Cached backend instances.
        _default_backend: Name of the default backend.

    Example:
        # Get the default backend
        backend = BackendFactory.get_backend()

        # Get a specific backend
        mock_backend = BackendFactory.get_backend("mock")

        # Register a custom backend
        BackendFactory.register("custom", MyCustomBackend)
    """

    _backends: dict[str, type["BaseDataQualityBackend"]] = {}
    _instances: dict[str, "BaseDataQualityBackend"] = {}
    _default_backend: str = "truthound"
    _fallback_backend: str = "mock"
    _initialized: bool = False

    @classmethod
    def _ensure_initialized(cls) -> None:
        """Ensure built-in backends are registered."""
        if cls._initialized:
            return

        # Import and register built-in backends
        from .mock_backend import MockBackend
        from .truthound_backend import TruthoundBackend

        cls._backends["truthound"] = TruthoundBackend
        cls._backends["mock"] = MockBackend
        cls._initialized = True

    @classmethod
    def register(
        cls,
        name: str,
        backend_class: type["BaseDataQualityBackend"],
    ) -> None:
        """Register a backend class.

        Args:
            name: Backend name for lookup.
            backend_class: Backend class to register.

        Example:
            class MyBackend(BaseDataQualityBackend):
                ...

            BackendFactory.register("my-backend", MyBackend)
        """
        cls._ensure_initialized()
        cls._backends[name] = backend_class
        logger.debug(f"Registered backend: {name}")

    @classmethod
    def unregister(cls, name: str) -> None:
        """Unregister a backend.

        Args:
            name: Backend name to unregister.
        """
        cls._ensure_initialized()
        if name in cls._backends:
            del cls._backends[name]
        if name in cls._instances:
            cls._instances[name].shutdown()
            del cls._instances[name]
        logger.debug(f"Unregistered backend: {name}")

    @classmethod
    def get_backend(
        cls,
        name: str | None = None,
        *,
        fallback: bool = True,
        max_workers: int = 4,
    ) -> "BaseDataQualityBackend":
        """Get a backend instance.

        Args:
            name: Backend name. If None, uses default backend.
            fallback: If True, fallback to mock when primary unavailable.
            max_workers: Maximum worker threads for the backend.

        Returns:
            Backend instance.

        Raises:
            BackendUnavailableError: If backend not available and no fallback.

        Example:
            # Get default backend with fallback
            backend = BackendFactory.get_backend()

            # Get specific backend without fallback
            backend = BackendFactory.get_backend("truthound", fallback=False)
        """
        cls._ensure_initialized()

        backend_name = name or cls._default_backend

        # Check if we have a cached instance
        if backend_name in cls._instances:
            instance = cls._instances[backend_name]
            if instance.is_available():
                return instance
            else:
                # Instance no longer available, remove from cache
                del cls._instances[backend_name]

        # Try to create the requested backend
        if backend_name in cls._backends:
            try:
                instance = cls._backends[backend_name](max_workers=max_workers)
                if instance.is_available():
                    cls._instances[backend_name] = instance
                    logger.info(f"Using backend: {backend_name}")
                    return instance
                else:
                    logger.warning(f"Backend '{backend_name}' not available")
            except Exception as e:
                logger.warning(f"Failed to create backend '{backend_name}': {e}")

        # Try fallback if enabled
        if fallback and cls._fallback_backend in cls._backends:
            fallback_name = cls._fallback_backend
            if fallback_name not in cls._instances:
                instance = cls._backends[fallback_name](max_workers=max_workers)
                cls._instances[fallback_name] = instance
            logger.info(f"Using fallback backend: {fallback_name}")
            return cls._instances[fallback_name]

        raise BackendUnavailableError(
            backend_name,
            f"Backend not available and no fallback. "
            f"Available backends: {list(cls._backends.keys())}"
        )

    @classmethod
    def get_available_backends(cls) -> list[str]:
        """Get list of available backend names.

        Returns:
            List of backend names that are currently available.
        """
        cls._ensure_initialized()

        available = []
        for name, backend_class in cls._backends.items():
            try:
                instance = backend_class()
                if instance.is_available():
                    available.append(name)
                instance.shutdown()
            except Exception:
                pass
        return available

    @classmethod
    def set_default_backend(cls, name: str) -> None:
        """Set the default backend.

        Args:
            name: Backend name to use as default.

        Raises:
            ValueError: If backend is not registered.
        """
        cls._ensure_initialized()

        if name not in cls._backends:
            raise ValueError(
                f"Backend '{name}' not registered. "
                f"Available: {list(cls._backends.keys())}"
            )
        cls._default_backend = name
        logger.info(f"Default backend set to: {name}")

    @classmethod
    def set_fallback_backend(cls, name: str | None) -> None:
        """Set the fallback backend.

        Args:
            name: Backend name for fallback, or None to disable fallback.
        """
        cls._ensure_initialized()

        if name and name not in cls._backends:
            raise ValueError(
                f"Backend '{name}' not registered. "
                f"Available: {list(cls._backends.keys())}"
            )
        cls._fallback_backend = name or ""
        logger.info(f"Fallback backend set to: {name or 'disabled'}")

    @classmethod
    def reset(cls) -> None:
        """Reset factory state (for testing).

        Shuts down all cached instances and clears registration.
        """
        for instance in cls._instances.values():
            instance.shutdown()
        cls._instances.clear()
        cls._backends.clear()
        cls._initialized = False
        cls._default_backend = "truthound"
        cls._fallback_backend = "mock"


# =============================================================================
# Module-level convenience functions
# =============================================================================

_default_backend: "BaseDataQualityBackend | None" = None


def get_backend(
    name: str | None = None,
    *,
    fallback: bool = True,
) -> "BaseDataQualityBackend":
    """Get a backend instance.

    Convenience function that uses BackendFactory.

    Args:
        name: Backend name. If None, uses default backend.
        fallback: If True, fallback to mock when primary unavailable.

    Returns:
        Backend instance.
    """
    global _default_backend

    if name is None and _default_backend is not None:
        return _default_backend

    backend = BackendFactory.get_backend(name, fallback=fallback)

    if name is None:
        _default_backend = backend

    return backend


def reset_backend() -> None:
    """Reset the cached default backend (for testing)."""
    global _default_backend
    _default_backend = None
    BackendFactory.reset()


# =============================================================================
# Truthound Version and Capability Detection
# =============================================================================


def get_truthound_version() -> str | None:
    """Get the installed truthound version.

    Returns:
        Version string or None if truthound not installed.
    """
    try:
        import truthound

        return getattr(truthound, "__version__", None)
    except ImportError:
        return None


def get_backend_capabilities() -> dict[str, bool]:
    """Get capabilities of the current backend.

    Returns a dictionary indicating which features are available
    in the current backend configuration.

    Returns:
        Dictionary mapping capability names to availability.
    """
    backend = get_backend(fallback=True)
    capabilities = {
        # Core validation
        "check": True,  # Always available
        "learn": True,  # Schema learning
        "profile": True,  # Data profiling
        "compare": True,  # Drift detection
        "scan": True,  # PII scanning
        "mask": True,  # Data masking
        # Advanced features
        "generate_suite": _has_method(backend, "generate_suite"),
        "parallel_execution": True,  # Thread pool executor
        "async_execution": True,  # Async/await support
        # Checkpoint features
        "checkpoint": _is_checkpoint_available(),
        "checkpoint_actions": _is_checkpoint_available(),
        "checkpoint_triggers": _is_checkpoint_available(),
        "checkpoint_ci_reporters": _is_ci_reporters_available(),
        # Reporter features
        "reporters": _is_reporters_available(),
        "ci_reporters": _is_ci_reporters_available(),
        # Version-specific features
        "truthound_2x_api": _is_truthound_2x_api(),
    }
    return capabilities


def _has_method(obj: object, method_name: str) -> bool:
    """Check if an object has a callable method."""
    attr = getattr(obj, method_name, None)
    return callable(attr)


def _is_checkpoint_available() -> bool:
    """Check if truthound checkpoint module is available."""
    try:
        from truthound.checkpoint import Checkpoint  # noqa: F401

        return True
    except ImportError:
        return False


def _is_reporters_available() -> bool:
    """Check if truthound reporters module is available."""
    try:
        from truthound.reporters import get_reporter  # noqa: F401

        return True
    except ImportError:
        return False


def _is_ci_reporters_available() -> bool:
    """Check if truthound CI reporters are available."""
    try:
        from truthound.checkpoint.ci import detect_ci_platform  # noqa: F401

        return True
    except ImportError:
        return False


def _is_truthound_2x_api() -> bool:
    """Check if truthound 2.x API is available (explicit imports)."""
    try:
        # Check for new explicit import pattern
        from truthound.datasources.sql.postgresql import (  # noqa: F401
            PostgreSQLDataSource,
        )

        return True
    except ImportError:
        return False


def get_backend_info() -> dict[str, any]:
    """Get comprehensive information about the current backend.

    Returns:
        Dictionary with backend information including:
        - name: Backend name
        - version: Truthound version (if applicable)
        - available: Whether backend is available
        - capabilities: Feature capabilities dict
        - registered_backends: List of registered backend names
    """
    backend_name = BackendFactory._default_backend
    try:
        backend = get_backend(fallback=False)
        available = backend.is_available()
        version = backend.get_version()
    except Exception:
        available = False
        version = None

    return {
        "name": backend_name,
        "version": version or get_truthound_version(),
        "available": available,
        "capabilities": get_backend_capabilities(),
        "registered_backends": list(BackendFactory._backends.keys()) if BackendFactory._initialized else ["truthound", "mock"],
        "fallback_enabled": bool(BackendFactory._fallback_backend),
        "fallback_backend": BackendFactory._fallback_backend or None,
    }
