"""Truthound Dashboard.

Truthound Dashboard is the operational UI for Truthound 3.0. It exposes
the Truthound validation, profiling, drift, privacy, checkpoint, reporter,
plugin, observability, and lineage workflows without adding dashboard-only
validation semantics.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("truthound-dashboard")
except PackageNotFoundError:
    # Package not installed (e.g., running from source without pip install -e)
    __version__ = "3.0.0.dev"

__all__ = ["__version__"]
