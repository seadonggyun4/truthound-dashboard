"""Dashboard-specific escalation service using truthound.

This module provides adapters that integrate truthound's escalation
system with the Dashboard's database configuration.
"""

from __future__ import annotations

import logging
from typing import Any

from truthound.checkpoint.escalation import (
    EscalationEngine,
    EscalationEngineConfig,
    EscalationPolicy,
    EscalationLevel,
    EscalationTarget,
    EscalationTrigger,
    EscalationState,
    TargetType,
    InMemoryEscalationStore,
)

logger = logging.getLogger(__name__)


class DashboardEscalationService:
    """Dashboard-specific escalation service.

    Wraps truthound's EscalationEngine and provides integration
    with the Dashboard's database configuration.

    Example:
        service = DashboardEscalationService()
        await service.start()

        await service.trigger(
            incident_id="incident-123",
            policy_name="critical_alerts",
            context={"severity": "critical"},
        )
    """

    def __init__(self) -> None:
        """Initialize the service."""
        self._engine: EscalationEngine | None = None
        self._policies: dict[str, EscalationPolicy] = {}

    @property
    def engine(self) -> EscalationEngine:
        """Get the underlying truthound engine."""
        if self._engine is None:
            config = EscalationEngineConfig(
                check_interval_seconds=60,
                max_retries=3,
            )
            self._engine = EscalationEngine(
                config=config,
                store=InMemoryEscalationStore(),
            )
        return self._engine

    async def start(self) -> None:
        """Start the escalation engine."""
        await self.engine.start()

    async def stop(self) -> None:
        """Stop the escalation engine."""
        await self.engine.stop()

    def register_policy(self, policy: EscalationPolicy) -> None:
        """Register an escalation policy."""
        self._policies[policy.name] = policy
        self.engine.register_policy(policy)

    async def trigger(
        self,
        incident_id: str,
        policy_name: str,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Trigger an escalation for an incident.

        Args:
            incident_id: Unique incident identifier.
            policy_name: Name of the escalation policy.
            context: Context data for the incident.

        Returns:
            Escalation record.
        """
        return await self.engine.trigger(
            incident_id=incident_id,
            policy_name=policy_name,
            context=context or {},
        )

    async def acknowledge(
        self,
        incident_id: str,
        *,
        responder: str | None = None,
        note: str | None = None,
    ) -> bool:
        """Acknowledge an escalation.

        Args:
            incident_id: Incident identifier.
            responder: Name/ID of responder.
            note: Optional note.

        Returns:
            True if acknowledged successfully.
        """
        return await self.engine.acknowledge(
            incident_id=incident_id,
            responder=responder,
            note=note,
        )

    async def resolve(
        self,
        incident_id: str,
        *,
        responder: str | None = None,
        note: str | None = None,
    ) -> bool:
        """Resolve an escalation.

        Args:
            incident_id: Incident identifier.
            responder: Name/ID of responder.
            note: Optional resolution note.

        Returns:
            True if resolved successfully.
        """
        return await self.engine.resolve(
            incident_id=incident_id,
            responder=responder,
            note=note,
        )

    async def cancel(
        self,
        incident_id: str,
        *,
        reason: str | None = None,
    ) -> bool:
        """Cancel an escalation.

        Args:
            incident_id: Incident identifier.
            reason: Optional cancellation reason.

        Returns:
            True if cancelled successfully.
        """
        return await self.engine.cancel(incident_id=incident_id, reason=reason)

    async def get_active_escalations(self) -> list[Any]:
        """Get all active escalations.

        Returns:
            List of active escalation records.
        """
        return await self.engine.list_active()

    def get_policy(self, name: str) -> EscalationPolicy | None:
        """Get a registered policy by name."""
        return self._policies.get(name)


def create_policy_from_db(db_config: dict[str, Any]) -> EscalationPolicy:
    """Create an EscalationPolicy from database configuration.

    Args:
        db_config: Configuration dictionary from database.

    Returns:
        EscalationPolicy for truthound's engine.
    """
    # Build targets
    def build_target(target_config: dict[str, Any]) -> EscalationTarget:
        target_type_map = {
            "user": TargetType.USER,
            "team": TargetType.TEAM,
            "channel": TargetType.CHANNEL,
            "schedule": TargetType.SCHEDULE,
            "webhook": TargetType.WEBHOOK,
            "email": TargetType.EMAIL,
            "phone": TargetType.PHONE,
            "custom": TargetType.CUSTOM,
        }
        return EscalationTarget(
            type=target_type_map.get(
                target_config.get("type", "user").lower(),
                TargetType.USER,
            ),
            identifier=target_config.get("identifier", ""),
            display_name=target_config.get("display_name"),
            channel=target_config.get("channel"),
            config=target_config.get("config", {}),
        )

    # Build levels
    levels = []
    for level_config in db_config.get("levels", []):
        level = EscalationLevel(
            level=level_config.get("level", 1),
            delay_minutes=level_config.get("delay_minutes", 0),
            targets=[build_target(t) for t in level_config.get("targets", [])],
            repeat_count=level_config.get("repeat_count", 1),
            repeat_interval_minutes=level_config.get("repeat_interval_minutes", 5),
        )
        levels.append(level)

    # Build triggers
    trigger_map = {
        "unacknowledged": EscalationTrigger.UNACKNOWLEDGED,
        "severity": EscalationTrigger.SEVERITY,
        "manual": EscalationTrigger.MANUAL,
        "failure": EscalationTrigger.FAILURE,
        "sla_breach": EscalationTrigger.SLA_BREACH,
    }
    triggers = [
        trigger_map.get(t.lower(), EscalationTrigger.UNACKNOWLEDGED)
        for t in db_config.get("triggers", ["unacknowledged"])
    ]

    return EscalationPolicy(
        name=db_config.get("name", "default"),
        levels=levels,
        triggers=triggers,
        description=db_config.get("description"),
        severity_filter=db_config.get("severity_filter"),
        auto_resolve_on_success=db_config.get("auto_resolve_on_success", True),
        metadata=db_config.get("metadata", {}),
    )
