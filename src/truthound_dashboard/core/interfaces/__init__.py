"""Interface definitions for data quality operations.

This module defines protocols (interfaces) for loose coupling between
the dashboard and data quality backends like truthound.

The protocols enable:
- Backend abstraction: Switch between different data quality libraries
- Testability: Mock backends for unit testing without dependencies
- Extensibility: Add custom backends without modifying core code

Architecture:
    Dashboard Services
           ↓
    Abstract Interfaces (this module)
           ↓
    Concrete Implementations (backends/, actions/, etc.)
           ↓
    truthound library (external)

Key Interfaces:
    - DataSourceProtocol: Abstract data source
    - ActionProtocol: Post-validation actions (notifications, storage)
    - TriggerProtocol: Validation trigger mechanisms
    - RoutingRuleProtocol: Rule-based action routing
    - CheckpointProtocol: Validation pipeline orchestration
    - ReporterProtocol: Report generation
"""

# Base interfaces
from .base import (
    ColumnSchema,
    ColumnType,
    DataInput,
    DataSourceCapability,
    DataSourceProtocol,
    ExecutionContext,
    ResultProtocol,
    TableSchema,
)

# Legacy protocols (for backward compatibility)
from .protocols import (
    ICheckResult,
    IColumnProfile,
    ICompareResult,
    IDataQualityBackend,
    IDataSource,
    IDataSourceConfig,
    IGenerateSuiteResult,
    ILearnResult,
    IMaskResult,
    IProfileResult,
    IScanResult,
    IValidationIssue,
)

# Action interfaces
from .actions import (
    ActionConfig,
    ActionContext,
    ActionProtocol,
    ActionRegistry,
    ActionResult,
    ActionStatus,
    AsyncActionProtocol,
    AsyncBaseAction,
    BaseAction,
    CompensatableActionProtocol,
    NotifyCondition,
    get_action_registry,
    register_action,
)

# Trigger interfaces
from .triggers import (
    BaseTrigger,
    CronTriggerConfig,
    DataArrivalTriggerConfig,
    EventTriggerConfig,
    FileWatchTriggerConfig,
    TriggerConfig,
    TriggerProtocol,
    TriggerRegistry,
    TriggerResult,
    TriggerStatus,
    TriggerType,
    WebhookTriggerConfig,
    get_trigger_registry,
    register_trigger,
)

# Routing interfaces
from .routing import (
    AllOf,
    AlwaysRule,
    AnyOf,
    BaseRoutingRule,
    Jinja2Rule,
    NeverRule,
    NotRule,
    Route,
    RouteContext,
    RouteMode,
    RoutePriority,
    Router,
    RouterProtocol,
    RoutingRuleProtocol,
)

# Checkpoint interfaces
from .checkpoint import (
    CheckpointConfig,
    CheckpointProtocol,
    CheckpointRegistry,
    CheckpointResult,
    CheckpointRunnerProtocol,
    CheckpointStatus,
    get_checkpoint_registry,
    register_checkpoint,
)

# Reporter interfaces
from .reporters import (
    AsyncBaseReporter,
    AsyncReporterProtocol,
    BaseReporter,
    ReportData,
    ReporterConfig,
    ReporterProtocol,
    ReporterRegistry,
    ReportFormat,
    ReportOutput,
    get_reporter_registry,
    register_reporter,
)

__all__ = [
    # Base interfaces
    "DataInput",
    "DataSourceProtocol",
    "DataSourceCapability",
    "ColumnType",
    "ColumnSchema",
    "TableSchema",
    "ExecutionContext",
    "ResultProtocol",
    # Legacy protocols (backward compatibility)
    "IDataQualityBackend",
    "IDataSource",
    "IDataSourceConfig",
    "ICheckResult",
    "ILearnResult",
    "IProfileResult",
    "IColumnProfile",
    "ICompareResult",
    "IScanResult",
    "IMaskResult",
    "IGenerateSuiteResult",
    "IValidationIssue",
    # Action interfaces
    "ActionProtocol",
    "AsyncActionProtocol",
    "CompensatableActionProtocol",
    "BaseAction",
    "AsyncBaseAction",
    "ActionConfig",
    "ActionResult",
    "ActionStatus",
    "ActionContext",
    "ActionRegistry",
    "NotifyCondition",
    "get_action_registry",
    "register_action",
    # Trigger interfaces
    "TriggerProtocol",
    "BaseTrigger",
    "TriggerConfig",
    "CronTriggerConfig",
    "FileWatchTriggerConfig",
    "WebhookTriggerConfig",
    "EventTriggerConfig",
    "DataArrivalTriggerConfig",
    "TriggerResult",
    "TriggerStatus",
    "TriggerType",
    "TriggerRegistry",
    "get_trigger_registry",
    "register_trigger",
    # Routing interfaces
    "RoutingRuleProtocol",
    "RouterProtocol",
    "BaseRoutingRule",
    "Jinja2Rule",
    "AllOf",
    "AnyOf",
    "NotRule",
    "AlwaysRule",
    "NeverRule",
    "Route",
    "Router",
    "RouteContext",
    "RouteMode",
    "RoutePriority",
    # Checkpoint interfaces
    "CheckpointProtocol",
    "CheckpointRunnerProtocol",
    "CheckpointConfig",
    "CheckpointResult",
    "CheckpointStatus",
    "CheckpointRegistry",
    "get_checkpoint_registry",
    "register_checkpoint",
    # Reporter interfaces
    "ReporterProtocol",
    "AsyncReporterProtocol",
    "BaseReporter",
    "AsyncBaseReporter",
    "ReporterConfig",
    "ReportData",
    "ReportOutput",
    "ReportFormat",
    "ReporterRegistry",
    "get_reporter_registry",
    "register_reporter",
]
