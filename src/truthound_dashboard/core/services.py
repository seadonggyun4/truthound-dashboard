"""Compatibility shim for legacy core service imports.

All service implementations now live under `truthound_dashboard.core.domains`.
This module intentionally contains no business logic.
"""

from .domains.drift import DriftComparisonRepository, DriftService
from .domains.history import HistoryService
from .domains.privacy import DataMaskRepository, MaskService, PIIScanRepository, PIIScanService
from .domains.profiles import ProfileRepository, ProfileService
from .domains.rules import RuleRepository, RuleService
from .domains.schedules import ScheduleRepository, ScheduleService
from .domains.schemas import SchemaRepository, SchemaService
from .domains.source_io import (
    get_async_data_input_from_source,
    get_data_input_from_source,
    get_source_data_input,
)
from .domains.sources import SourceRepository, SourceService
from .domains.validations import ValidationRepository, ValidationService

__all__ = [
    "DriftComparisonRepository",
    "DriftService",
    "HistoryService",
    "DataMaskRepository",
    "MaskService",
    "PIIScanRepository",
    "PIIScanService",
    "ProfileRepository",
    "ProfileService",
    "RuleRepository",
    "RuleService",
    "ScheduleRepository",
    "ScheduleService",
    "SchemaRepository",
    "SchemaService",
    "get_async_data_input_from_source",
    "get_data_input_from_source",
    "get_source_data_input",
    "SourceRepository",
    "SourceService",
    "ValidationRepository",
    "ValidationService",
]
