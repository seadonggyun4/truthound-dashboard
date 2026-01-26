"""Data quality backend implementations.

This module provides backend implementations for data quality operations.
The backends abstract away the specific library (truthound) and provide
a unified interface for the dashboard services.

Architecture:
    BackendFactory
        ↓
    BaseDataQualityBackend (ABC)
        ↓
    ┌─────────────────────────────┐
    │  TruthoundBackend  │ MockBackend │
    └─────────────────────────────┘

Usage:
    from truthound_dashboard.core.backends import BackendFactory

    # Get the default backend (truthound)
    backend = BackendFactory.get_backend()

    # Check if backend is available
    if backend.is_available():
        result = await backend.check("data.csv")

    # Use a specific backend
    backend = BackendFactory.get_backend("mock")
"""

from .base import BaseDataQualityBackend
from .errors import (
    BackendError,
    BackendOperationError,
    BackendUnavailableError,
    BackendVersionError,
)
from .factory import (
    BackendFactory,
    get_backend,
    reset_backend,
    get_truthound_version,
    get_backend_capabilities,
    get_backend_info,
)
from .mock_backend import MockBackend
from .truthound_backend import TruthoundBackend

__all__ = [
    # Base class
    "BaseDataQualityBackend",
    # Backend implementations
    "TruthoundBackend",
    "MockBackend",
    # Factory
    "BackendFactory",
    "get_backend",
    "reset_backend",
    # Capability detection
    "get_truthound_version",
    "get_backend_capabilities",
    "get_backend_info",
    # Errors
    "BackendError",
    "BackendUnavailableError",
    "BackendVersionError",
    "BackendOperationError",
]
