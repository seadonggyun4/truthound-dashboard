"""Result converters for data quality backends.

This module provides converters that transform backend-specific result
objects into dashboard-standard result models.

The converter pattern isolates backend-specific code and makes it easy
to support multiple backends or handle API changes.
"""

from .truthound import TruthoundResultConverter

__all__ = [
    "TruthoundResultConverter",
]
