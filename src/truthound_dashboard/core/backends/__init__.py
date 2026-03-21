"""Data quality backend implementations.

This module provides backend implementations for data quality operations.
Truthound 3.0 is the canonical execution backend for the dashboard.

Architecture:
    BackendFactory
        ↓
    BaseDataQualityBackend (ABC)
        ↓
    ┌──────────────────────┐
    │  TruthoundBackend    │
    └──────────────────────┘

Usage:
    from truthound_dashboard.core.backends import BackendFactory

    # Get the default backend (truthound)
    backend = BackendFactory.get_backend()

    # Check if backend is available
    if backend.is_available():
        result = await backend.check("data.csv")

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
from .truthound_backend import TruthoundBackend

__all__ = [
    # Base class
    "BaseDataQualityBackend",
    # Backend implementations
    "TruthoundBackend",
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
