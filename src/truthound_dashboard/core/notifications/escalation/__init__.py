"""Escalation engine for notification management.

This module provides a multi-level escalation system for managing
alerts that require attention at different organizational levels.

Features:
    - Multi-level escalation policies
    - State machine for incident tracking
    - Configurable delay between escalation levels
    - Support for user, group, and on-call targets
    - Auto-resolution on success

State Machine:
    PENDING -> TRIGGERED -> ESCALATED -> RESOLVED
                  |             ^
                  v             |
             ACKNOWLEDGED ------+

Example:
    from truthound_dashboard.core.notifications.escalation import (
        EscalationEngine,
        EscalationPolicy,
        EscalationLevel,
        EscalationTarget,
        TargetType,
    )

    policy = EscalationPolicy(
        name="critical_alerts",
        levels=[
            EscalationLevel(
                level=1,
                delay_minutes=0,
                targets=[
                    EscalationTarget(type=TargetType.USER, identifier="team-lead", channel="slack")
                ],
            ),
            EscalationLevel(
                level=2,
                delay_minutes=15,
                targets=[
                    EscalationTarget(type=TargetType.GROUP, identifier="managers", channel="pagerduty")
                ],
            ),
        ],
    )

    engine = EscalationEngine(policy=policy)
    await engine.trigger("incident-123", context={"severity": "critical"})
"""

from .engine import EscalationEngine, EscalationEngineConfig
from .models import (
    EscalationEvent,
    EscalationIncident,
    EscalationLevel,
    EscalationPolicy,
    EscalationState,
    EscalationTarget,
    StateTransition,
    TargetType,
)
from .state_machine import EscalationStateMachine
from .stores import (
    BaseEscalationStore,
    InMemoryEscalationStore,
    SQLiteEscalationStore,
)

__all__ = [
    # Models
    "EscalationState",
    "TargetType",
    "EscalationTarget",
    "EscalationLevel",
    "EscalationPolicy",
    "EscalationIncident",
    "EscalationEvent",
    "StateTransition",
    # State Machine
    "EscalationStateMachine",
    # Stores
    "BaseEscalationStore",
    "InMemoryEscalationStore",
    "SQLiteEscalationStore",
    # Engine
    "EscalationEngine",
    "EscalationEngineConfig",
]
