"""Domain-oriented service entrypoints.

These modules provide stable import boundaries for the dashboard's core
business domains while the public `truthound_dashboard.core` namespace remains
backward compatible.
"""

from .drift import DriftComparisonRepository, DriftService
from .history import HistoryService
from .privacy import DataMaskRepository, MaskService, PIIScanRepository, PIIScanService
from .profiles import ProfileRepository, ProfileService
from .rules import RuleRepository, RuleService
from .schedules import ScheduleRepository, ScheduleService
from .schemas import SchemaRepository, SchemaService
from .source_io import (
    get_async_data_input_from_source,
    get_data_input_from_source,
    get_source_data_input,
)
from .sources import SourceRepository, SourceService
from .validations import ValidationRepository, ValidationService

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
