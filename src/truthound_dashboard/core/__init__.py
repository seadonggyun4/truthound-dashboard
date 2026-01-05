"""Core business logic module.

This module contains the core business logic for the dashboard,
including services, adapters, and domain models.

Exports:
    - Adapter: TruthoundAdapter, get_adapter
    - Services: SourceService, ValidationService, SchemaService, RuleService, ProfileService,
                HistoryService, DriftService, ScheduleService
    - Result types: CheckResult, LearnResult, ProfileResult, CompareResult
"""

from .base import BaseService, CRUDService
from .services import (
    DriftService,
    HistoryService,
    ProfileService,
    RuleService,
    ScheduleService,
    SchemaService,
    SourceService,
    ValidationService,
)
from .truthound_adapter import (
    CheckResult,
    CompareResult,
    LearnResult,
    ProfileResult,
    TruthoundAdapter,
    get_adapter,
    reset_adapter,
)

__all__ = [
    # Base classes
    "BaseService",
    "CRUDService",
    # Services
    "SourceService",
    "ValidationService",
    "SchemaService",
    "RuleService",
    "ProfileService",
    "HistoryService",
    "DriftService",
    "ScheduleService",
    # Adapter
    "TruthoundAdapter",
    "get_adapter",
    "reset_adapter",
    # Result types
    "CheckResult",
    "LearnResult",
    "ProfileResult",
    "CompareResult",
]
