"""Escalation engine using truthound.checkpoint.escalation.

This module provides a multi-level escalation system for managing
alerts using truthound's escalation infrastructure.

Key Components from truthound.checkpoint.escalation:
    - EscalationEngine: Main escalation engine
    - EscalationEngineConfig: Engine configuration
    - EscalationPolicy: Policy definition
    - EscalationLevel: Level definition
    - EscalationTarget: Target definition
    - EscalationRecord: Escalation state record

Target Types from truthound:
    - USER: Individual user
    - TEAM: Team
    - CHANNEL: Channel (Slack, etc.)
    - SCHEDULE: On-call schedule
    - WEBHOOK: Webhook URL
    - EMAIL: Email
    - PHONE: Phone
    - CUSTOM: Custom

Escalation States from truthound:
    - PENDING: Initial state, waiting to start
    - ACTIVE: Currently notifying at level
    - ESCALATING: Escalating to next level
    - ACKNOWLEDGED: Responder acknowledged
    - RESOLVED: Issue resolved
    - CANCELLED: Manually cancelled
    - TIMED_OUT: Max escalation reached
    - FAILED: System error

Storage Backends from truthound:
    - InMemoryEscalationStore: Single-process storage
    - RedisEscalationStore: Distributed storage
    - SQLiteEscalationStore: Persistent storage

Example:
    from truthound.checkpoint.escalation import (
        EscalationEngine,
        EscalationEngineConfig,
        EscalationPolicy,
        EscalationLevel,
        EscalationTarget,
        EscalationTrigger,
    )

    # Define policy
    policy = EscalationPolicy(
        name="critical_alerts",
        levels=[
            EscalationLevel(
                level=1,
                delay_minutes=0,
                targets=[EscalationTarget.user("team-lead", "Team Lead")],
                repeat_count=2,
                repeat_interval_minutes=5,
            ),
            EscalationLevel(
                level=2,
                delay_minutes=15,
                targets=[EscalationTarget.user("manager", "Manager")],
            ),
        ],
        triggers=[EscalationTrigger.UNACKNOWLEDGED],
        severity_filter=["critical", "high"],
    )

    # Create engine
    config = EscalationEngineConfig(store_type="memory")
    engine = EscalationEngine(config)
    engine.register_policy(policy)

    # Trigger escalation
    await engine.start()
    result = await engine.trigger(
        incident_id="incident-123",
        context={"severity": "critical"},
        policy_name="critical_alerts",
    )
"""

# Re-export from truthound.checkpoint.escalation
from truthound.checkpoint.escalation import (
    EscalationEngine,
    EscalationEngineConfig,
    EscalationPolicy,
    EscalationLevel,
    EscalationTarget,
    EscalationRecord,
    EscalationTrigger,
    EscalationState,
    TargetType,
    EscalationPolicyManager,
    EscalationPolicyConfig,
)

# Storage backends
from truthound.checkpoint.escalation import (
    InMemoryEscalationStore,
    create_store,
)

# Redis/SQLite stores (optional)
try:
    from truthound.checkpoint.escalation import RedisEscalationStore
    REDIS_AVAILABLE = True
except ImportError:
    RedisEscalationStore = None  # type: ignore
    REDIS_AVAILABLE = False

try:
    from truthound.checkpoint.escalation import SQLiteEscalationStore
    SQLITE_AVAILABLE = True
except ImportError:
    SQLiteEscalationStore = None  # type: ignore
    SQLITE_AVAILABLE = False

# Routing integration
from truthound.checkpoint.escalation import (
    EscalationRule,
    EscalationRuleConfig,
    EscalationAction,
    create_escalation_route,
)

# Dashboard-specific adapters
from .engine import (
    DashboardEscalationService,
    create_policy_from_db,
)

__all__ = [
    # truthound core
    "EscalationEngine",
    "EscalationEngineConfig",
    "EscalationPolicy",
    "EscalationLevel",
    "EscalationTarget",
    "EscalationRecord",
    "EscalationTrigger",
    "EscalationState",
    "TargetType",
    "EscalationPolicyManager",
    "EscalationPolicyConfig",
    # Storage
    "InMemoryEscalationStore",
    "create_store",
    "RedisEscalationStore",
    "SQLiteEscalationStore",
    "REDIS_AVAILABLE",
    "SQLITE_AVAILABLE",
    # Routing integration
    "EscalationRule",
    "EscalationRuleConfig",
    "EscalationAction",
    "create_escalation_route",
    # Dashboard adapters
    "DashboardEscalationService",
    "create_policy_from_db",
]
