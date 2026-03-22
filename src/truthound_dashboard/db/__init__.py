"""Database module.

This module provides database connectivity, models, and repository patterns
for the truthound dashboard.

Exports:
    - Database connection: get_session, get_db_session, init_db
    - Base classes: Base, UUIDMixin, TimestampMixin
    - Models: Source, Schema, Rule, Validation, Profile, Schedule, DriftComparison, AppSettings
    - Repository: BaseRepository
"""

from .base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from .database import (
    get_db_session,
    get_engine,
    get_session,
    get_session_factory,
    init_db,
    reset_connection,
    reset_db,
)
from .control_plane_models import (
    ArtifactRecord,
    Domain,
    IncidentQueue,
    IncidentQueueMembership,
    Membership,
    Permission,
    Role,
    RolePermission,
    SavedView,
    SecretRef,
    Session,
    SourceOwnership,
    Team,
    TeamMembership,
    User,
    Workspace,
)
from .models import (
    # Phase 1-4 Models
    AppSettings,
    DataMask,
    DriftComparison,
    MaskingStrategy,
    NotificationChannel,
    NotificationLog,
    NotificationRule,
    PIIScan,
    Profile,
    Rule,
    Schedule,
    Schema,
    Source,
    Validation,
    TriggerType,
    # Anomaly Detection Models
    AnomalyDetection,
    # Scheduler Job Models
    SchedulerJob,
    SchedulerJobState,
)
from .repository import BaseRepository

__all__ = [
    # Base classes
    "Base",
    "UUIDMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    # Database functions
    "get_session",
    "get_db_session",
    "get_engine",
    "get_session_factory",
    "init_db",
    "reset_db",
    "reset_connection",
    # Control-plane models
    "Workspace",
    "Role",
    "Permission",
    "RolePermission",
    "User",
    "Membership",
    "Session",
    "SavedView",
    "ArtifactRecord",
    "SecretRef",
    "Team",
    "TeamMembership",
    "Domain",
    "SourceOwnership",
    "IncidentQueue",
    "IncidentQueueMembership",
    # Models
    "Source",
    "Schema",
    "Rule",
    "Validation",
    "Profile",
    "Schedule",
    "DriftComparison",
    "DataMask",
    "MaskingStrategy",
    "PIIScan",
    "AppSettings",
    # Notification models (Phase 3)
    "NotificationChannel",
    "NotificationRule",
    "NotificationLog",
    "TriggerType",
    # Anomaly Detection Models
    "AnomalyDetection",
    # Scheduler Job Models
    "SchedulerJob",
    "SchedulerJobState",
    # Repository
    "BaseRepository",
]
