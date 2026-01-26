"""Core business logic module.

This module contains the core business logic for the dashboard,
including services, adapters, backends, and domain models.

Exports:
    - Backends: BackendFactory, BaseDataQualityBackend, TruthoundBackend, MockBackend
    - Interfaces: IDataQualityBackend, DataInput, ICheckResult, etc.
    - Converters: TruthoundResultConverter
    - Adapter (legacy): TruthoundAdapter, get_adapter
    - DataSource Factory: DataSourceFactory, SourceConfig, SourceType, create_datasource
    - Services: SourceService, ValidationService, SchemaService, RuleService, ProfileService,
                HistoryService, DriftService, ScheduleService
    - Result types: CheckResult, LearnResult, ProfileResult, ColumnProfileResult,
                    CompareResult, ScanResult, MaskResult, GenerateSuiteResult
    - Scheduler: ValidationScheduler, get_scheduler, start_scheduler, stop_scheduler
    - Notifications: NotificationDispatcher, create_dispatcher, get_dispatcher
    - Cache: CacheBackend, MemoryCache, FileCache, get_cache, get_cache_manager
    - Maintenance: MaintenanceManager, get_maintenance_manager, cleanup_old_validations
    - Sampling: DataSampler, SamplingStrategy, get_sampler (Large Dataset Handling)
    - Exceptions: TruthoundDashboardError, SourceNotFoundError, ValidationError, etc.
    - Encryption: encrypt_value, decrypt_value, encrypt_config, decrypt_config
    - Logging: setup_logging, get_logger, get_audit_logger

Note:
    The profiler module now supports the new truthound profiler API with:
    - ProfilerConfig for fine-grained control over profiling behavior
    - TableProfile and ColumnProfile for comprehensive data profiling
    - generate_suite() for automatic validation rule generation from profiles

Architecture:
    The backend abstraction layer provides loose coupling with truthound:

    API Endpoints → Services → BackendFactory → IDataQualityBackend
                                                    ↓
                                    ┌───────────────┴───────────────┐
                                    │  TruthoundBackend  │  MockBackend  │
                                    └───────────────────────────────┘
"""

# Backend abstraction (loose coupling with truthound)
from .backends import (
    BackendError,
    BackendFactory,
    BackendOperationError,
    BackendUnavailableError,
    BackendVersionError,
    BaseDataQualityBackend,
    MockBackend,
    TruthoundBackend,
    get_backend,
    reset_backend,
)
from .base import BaseService, CRUDService
from .converters import TruthoundResultConverter
from .datasource_factory import (
    DataSourceFactory,
    SourceConfig,
    SourceType,
    create_datasource,
    create_datasource_async,
    get_datasource_auto,
    get_datasource_factory,
    get_source_capabilities,
    get_source_path_or_datasource,
    test_connection,
)
from .cache import (
    CacheBackend,
    CacheManager,
    FileCache,
    MemoryCache,
    get_cache,
    get_cache_manager,
    reset_cache,
)
from .encryption import (
    EncryptionError,
    Encryptor,
    decrypt_config,
    decrypt_value,
    encrypt_config,
    encrypt_value,
    get_encryptor,
    is_sensitive_field,
    mask_sensitive_value,
)
from .exceptions import (
    AuthenticationFailedError,
    AuthenticationRequiredError,
    AuthorizationError,
    DatabaseConnectionError,
    DatabaseError,
    DatabaseIntegrityError,
    ErrorCode,
    NotificationChannelNotFoundError,
    NotificationError,
    NotificationInvalidConfigError,
    NotificationRuleNotFoundError,
    NotificationSendError,
    RateLimitExceededError,
    RuleError,
    RuleInvalidError,
    RuleNotFoundError,
    RuleParseError,
    ScheduleConflictError,
    ScheduleError,
    ScheduleInvalidCronError,
    ScheduleNotFoundError,
    SchemaError,
    SchemaInvalidError,
    SchemaNotFoundError,
    SchemaParseError,
    SecurityError,
    SourceAccessDeniedError,
    SourceConnectionError,
    SourceError,
    SourceInvalidConfigError,
    SourceNotFoundError,
    TruthoundDashboardError,
    ValidationError,
    ValidationFailedError,
    ValidationNotFoundError,
    ValidationTimeoutError,
    get_error_message,
)
from .logging import (
    AuditLogger,
    LogConfig,
    LoggerAdapter,
    get_audit_logger,
    get_logger,
    setup_logging,
)
from .maintenance import (
    CleanupResult,
    CleanupStrategy,
    MaintenanceConfig,
    MaintenanceManager,
    MaintenanceReport,
    cleanup_notification_logs,
    cleanup_old_profiles,
    cleanup_old_validations,
    get_maintenance_manager,
    reset_maintenance_manager,
    vacuum_database,
)
from .notifications import (
    NotificationDispatcher,
    create_dispatcher,
    get_dispatcher,
)
from .sampling import (
    DataSampler,
    HeadSamplingStrategy,
    RandomSamplingStrategy,
    SamplingConfig,
    SamplingMethod,
    SamplingResult,
    SamplingStrategy,
    StratifiedSamplingStrategy,
    TailSamplingStrategy,
    get_sampler,
    reset_sampler,
)
from .validation_limits import (
    DeduplicationLimits,
    EscalationLimits,
    ThrottlingLimits,
    TimeWindowLimits,
    ValidationLimitError,
    clear_limits_cache,
    get_deduplication_limits,
    get_escalation_limits,
    get_throttling_limits,
    get_time_window_limits,
    validate_positive_float,
    validate_positive_int,
)
from .scheduler import (
    ValidationScheduler,
    get_scheduler,
    start_scheduler,
    stop_scheduler,
)
from .services import (
    DriftService,
    HistoryService,
    MaskService,
    PIIScanService,
    ProfileService,
    RuleService,
    ScheduleService,
    SchemaService,
    SourceService,
    ValidationService,
    get_data_input_from_source,
    get_async_data_input_from_source,
)
from .truthound_adapter import (
    CheckResult,
    ColumnProfileResult,
    CompareResult,
    GenerateSuiteResult,
    LearnResult,
    MaskResult,
    ProfileResult,
    ScanResult,
    TruthoundAdapter,
    get_adapter,
    reset_adapter,
)
# Phase 5 Services
from .phase5 import (
    ActivityLogger,
    CatalogService,
    CollaborationService,
    GlossaryService,
)

__all__ = [
    # Backend abstraction (loose coupling with truthound)
    "BackendFactory",
    "BaseDataQualityBackend",
    "TruthoundBackend",
    "MockBackend",
    "get_backend",
    "reset_backend",
    "BackendError",
    "BackendUnavailableError",
    "BackendVersionError",
    "BackendOperationError",
    # Converters
    "TruthoundResultConverter",
    # Base classes
    "BaseService",
    "CRUDService",
    # DataSource Factory
    "DataSourceFactory",
    "SourceConfig",
    "SourceType",
    "create_datasource",
    "create_datasource_async",
    "get_datasource_auto",
    "get_datasource_factory",
    "get_source_capabilities",
    "get_source_path_or_datasource",
    "test_connection",
    # Services
    "SourceService",
    "ValidationService",
    "SchemaService",
    "RuleService",
    "ProfileService",
    "HistoryService",
    "DriftService",
    "ScheduleService",
    "PIIScanService",
    "MaskService",
    "get_data_input_from_source",
    "get_async_data_input_from_source",
    # Adapter
    "TruthoundAdapter",
    "get_adapter",
    "reset_adapter",
    # Result types
    "CheckResult",
    "LearnResult",
    "ProfileResult",
    "ColumnProfileResult",
    "CompareResult",
    "ScanResult",
    "MaskResult",
    "GenerateSuiteResult",
    # Scheduler
    "ValidationScheduler",
    "get_scheduler",
    "start_scheduler",
    "stop_scheduler",
    # Notifications
    "NotificationDispatcher",
    "create_dispatcher",
    "get_dispatcher",
    # Cache (Phase 4)
    "CacheBackend",
    "MemoryCache",
    "FileCache",
    "CacheManager",
    "get_cache",
    "get_cache_manager",
    "reset_cache",
    # Maintenance (Phase 4)
    "MaintenanceManager",
    "MaintenanceConfig",
    "MaintenanceReport",
    "CleanupResult",
    "CleanupStrategy",
    "get_maintenance_manager",
    "reset_maintenance_manager",
    "cleanup_old_validations",
    "cleanup_old_profiles",
    "cleanup_notification_logs",
    "vacuum_database",
    # Exceptions (Phase 4)
    "TruthoundDashboardError",
    "ErrorCode",
    "get_error_message",
    "SourceError",
    "SourceNotFoundError",
    "SourceConnectionError",
    "SourceInvalidConfigError",
    "SourceAccessDeniedError",
    "SchemaError",
    "SchemaNotFoundError",
    "SchemaInvalidError",
    "SchemaParseError",
    "RuleError",
    "RuleNotFoundError",
    "RuleInvalidError",
    "RuleParseError",
    "ValidationError",
    "ValidationNotFoundError",
    "ValidationFailedError",
    "ValidationTimeoutError",
    "ScheduleError",
    "ScheduleNotFoundError",
    "ScheduleInvalidCronError",
    "ScheduleConflictError",
    "NotificationError",
    "NotificationChannelNotFoundError",
    "NotificationRuleNotFoundError",
    "NotificationSendError",
    "NotificationInvalidConfigError",
    "SecurityError",
    "AuthenticationRequiredError",
    "AuthenticationFailedError",
    "AuthorizationError",
    "RateLimitExceededError",
    "DatabaseError",
    "DatabaseConnectionError",
    "DatabaseIntegrityError",
    # Encryption (Phase 4)
    "Encryptor",
    "EncryptionError",
    "get_encryptor",
    "encrypt_value",
    "decrypt_value",
    "encrypt_config",
    "decrypt_config",
    "is_sensitive_field",
    "mask_sensitive_value",
    # Logging (Phase 4)
    "LogConfig",
    "LoggerAdapter",
    "AuditLogger",
    "setup_logging",
    "get_logger",
    "get_audit_logger",
    # Sampling (Phase 4 - Large Dataset Handling)
    "DataSampler",
    "SamplingConfig",
    "SamplingMethod",
    "SamplingResult",
    "SamplingStrategy",
    "RandomSamplingStrategy",
    "HeadSamplingStrategy",
    "TailSamplingStrategy",
    "StratifiedSamplingStrategy",
    "get_sampler",
    "reset_sampler",
    # Phase 5 Services
    "GlossaryService",
    "CatalogService",
    "CollaborationService",
    "ActivityLogger",
    # Validation Limits (DoS Prevention)
    "ValidationLimitError",
    "DeduplicationLimits",
    "ThrottlingLimits",
    "EscalationLimits",
    "TimeWindowLimits",
    "get_deduplication_limits",
    "get_throttling_limits",
    "get_escalation_limits",
    "get_time_window_limits",
    "clear_limits_cache",
    "validate_positive_int",
    "validate_positive_float",
]
