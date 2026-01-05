"""Pydantic schemas for API request/response validation.

This module exports all schemas used in the API layer.
Schemas follow consistent naming conventions:
- *Base: Common fields
- *Create: POST request bodies
- *Update: PUT/PATCH request bodies
- *Response: Response bodies
- *ListResponse: Paginated list responses
"""

from .base import (
    BaseSchema,
    ErrorResponse,
    IDMixin,
    ListResponseWrapper,
    MessageResponse,
    ResponseWrapper,
    TimestampMixin,
)
from .drift import (
    ColumnDriftResult,
    DriftCompareRequest,
    DriftComparisonListItem,
    DriftComparisonListResponse,
    DriftComparisonResponse,
    DriftResult,
    DriftSourceSummary,
)
from .history import (
    FailureFrequencyItem,
    HistoryQueryParams,
    HistoryResponse,
    HistorySummary,
    RecentValidation,
    TrendDataPoint,
)
from .profile import ColumnProfile, ProfileResponse
from .rule import (
    RuleBase,
    RuleCreate,
    RuleListItem,
    RuleListResponse,
    RuleResponse,
    RuleSummary,
    RuleUpdate,
)
from .schedule import (
    ScheduleActionResponse,
    ScheduleBase,
    ScheduleCreate,
    ScheduleListItem,
    ScheduleListResponse,
    ScheduleResponse,
    ScheduleUpdate,
)
from .schema import (
    ColumnSchema,
    SchemaLearnRequest,
    SchemaResponse,
    SchemaSummary,
    SchemaUpdateRequest,
)
from .source import (
    SourceBase,
    SourceCreate,
    SourceListResponse,
    SourceResponse,
    SourceSummary,
    SourceType,
    SourceUpdate,
)
from .validation import (
    IssueSeverity,
    ValidationIssue,
    ValidationListItem,
    ValidationListResponse,
    ValidationResponse,
    ValidationRunRequest,
    ValidationStatus,
    ValidationSummary,
)

__all__ = [
    # Base
    "BaseSchema",
    "IDMixin",
    "TimestampMixin",
    "ResponseWrapper",
    "ListResponseWrapper",
    "ErrorResponse",
    "MessageResponse",
    # Source
    "SourceType",
    "SourceBase",
    "SourceCreate",
    "SourceUpdate",
    "SourceResponse",
    "SourceListResponse",
    "SourceSummary",
    # Rule
    "RuleBase",
    "RuleCreate",
    "RuleUpdate",
    "RuleResponse",
    "RuleListItem",
    "RuleListResponse",
    "RuleSummary",
    # Validation
    "ValidationStatus",
    "IssueSeverity",
    "ValidationIssue",
    "ValidationRunRequest",
    "ValidationSummary",
    "ValidationResponse",
    "ValidationListItem",
    "ValidationListResponse",
    # Schema
    "ColumnSchema",
    "SchemaLearnRequest",
    "SchemaUpdateRequest",
    "SchemaResponse",
    "SchemaSummary",
    # Profile
    "ColumnProfile",
    "ProfileResponse",
    # History
    "TrendDataPoint",
    "FailureFrequencyItem",
    "RecentValidation",
    "HistorySummary",
    "HistoryResponse",
    "HistoryQueryParams",
    # Drift
    "DriftCompareRequest",
    "ColumnDriftResult",
    "DriftResult",
    "DriftSourceSummary",
    "DriftComparisonResponse",
    "DriftComparisonListItem",
    "DriftComparisonListResponse",
    # Schedule
    "ScheduleBase",
    "ScheduleCreate",
    "ScheduleUpdate",
    "ScheduleResponse",
    "ScheduleListItem",
    "ScheduleListResponse",
    "ScheduleActionResponse",
]
