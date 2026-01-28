"""Truthound library integration adapter for notifications.

This module provides an adapter that bridges the dashboard's notification
system with the truthound library's checkpoint features:
- Routing (ActionRouter)
- Deduplication (NotificationDeduplicator)
- Throttling (NotificationThrottler)
- Escalation (EscalationEngine)

The adapter loads configurations from the database and constructs
truthound library objects to process notifications.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Truthound library imports
from truthound.checkpoint.deduplication import (
    DeduplicationConfig as TruthoundDeduplicationConfig,
    DeduplicationPolicy,
    InMemoryDeduplicationStore,
    NotificationDeduplicator,
    NotificationFingerprint,
    TimeWindow,
)
from truthound.checkpoint.escalation import (
    EscalationEngine,
    EscalationEngineConfig,
    EscalationLevel,
    EscalationPolicy,
    EscalationTarget,
    EscalationTrigger,
    TargetType,
)
from truthound.checkpoint.routing import ActionRouter, AllOf, AnyOf, NotRule, Route
from truthound.checkpoint.routing.base import RouteContext, RouteMode, RoutePriority
from truthound.checkpoint.routing.rules import (
    AlwaysRule,
    DataAssetRule,
    ErrorRule,
    IssueCountRule,
    MetadataRule,
    NeverRule,
    PassRateRule,
    SeverityRule,
    StatusRule,
    TagRule,
    TimeWindowRule,
)
from truthound.checkpoint.throttling import (
    NotificationThrottler,
    RateLimit,
    RateLimitScope,
    ThrottlerBuilder,
    ThrottlingConfig as TruthoundThrottlingConfig,
)

if TYPE_CHECKING:
    from truthound_dashboard.db.models import (
        DeduplicationConfig,
        EscalationIncidentModel,
        EscalationPolicyModel,
        RoutingRuleModel,
        ThrottlingConfig,
    )

from .base import NotificationEvent
from .events import ValidationFailedEvent, ScheduleFailedEvent, DriftDetectedEvent

logger = logging.getLogger(__name__)

# Thread pool for running synchronous truthound operations
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="truthound_notif_")


@dataclass
class TruthoundStats:
    """Aggregated stats from truthound library components."""

    routing: dict[str, Any] = field(default_factory=dict)
    deduplication: dict[str, Any] = field(default_factory=dict)
    throttling: dict[str, Any] = field(default_factory=dict)
    escalation: dict[str, Any] = field(default_factory=dict)


class TruthoundNotificationAdapter:
    """Adapter for integrating truthound library notification features.

    This adapter:
    1. Loads routing rules from DB and constructs truthound's ActionRouter
    2. Loads deduplication config from DB and constructs NotificationDeduplicator
    3. Loads throttling config from DB and constructs NotificationThrottler
    4. Loads escalation policies from DB and constructs EscalationEngine

    Usage:
        adapter = TruthoundNotificationAdapter(session)
        await adapter.initialize()

        # Check if notification should be sent
        if await adapter.should_send_notification(event, channel_id):
            # Send notification
            await adapter.mark_notification_sent(event, channel_id)
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the adapter.

        Args:
            session: Database session for loading configurations.
        """
        self.session = session
        self._router: ActionRouter | None = None
        self._deduplicator: NotificationDeduplicator | None = None
        self._throttler: NotificationThrottler | None = None
        self._escalation_engine: EscalationEngine | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all truthound components from database configs."""
        if self._initialized:
            return

        try:
            await self._build_router()
            await self._build_deduplicator()
            await self._build_throttler()
            await self._build_escalation_engine()
            self._initialized = True
            logger.info("TruthoundNotificationAdapter initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TruthoundNotificationAdapter: {e}")
            raise

    # =========================================================================
    # Router (Routing Rules)
    # =========================================================================

    async def _build_router(self) -> None:
        """Build ActionRouter from database routing rules."""
        from truthound_dashboard.db.models import RoutingRuleModel

        result = await self.session.execute(
            select(RoutingRuleModel)
            .where(RoutingRuleModel.is_active == True)
            .order_by(RoutingRuleModel.priority.desc())
        )
        rules = result.scalars().all()

        self._router = ActionRouter(mode=RouteMode.ALL_MATCHES)

        for rule_model in rules:
            try:
                truthound_rule = self._build_rule_from_config(rule_model.rule_config)
                route = Route(
                    name=rule_model.name,
                    rule=truthound_rule,
                    actions=rule_model.actions,  # Channel IDs
                    priority=rule_model.priority,
                )
                self._router.add_route(route)
                logger.debug(f"Added route: {rule_model.name}")
            except Exception as e:
                logger.warning(f"Failed to build route '{rule_model.name}': {e}")

        logger.info(f"Built router with {len(rules)} routes")

    def _build_rule_from_config(self, config: dict[str, Any]) -> Any:
        """Convert rule_config JSON to truthound Rule object.

        Args:
            config: Rule configuration dictionary.

        Returns:
            Truthound Rule object.

        Raises:
            ValueError: If rule type is unknown.
        """
        rule_type = config.get("type", "").lower()

        # Basic rules
        if rule_type == "always":
            return AlwaysRule()
        elif rule_type == "never":
            return NeverRule()

        # Severity rule
        elif rule_type == "severity":
            return SeverityRule(
                min_severity=config.get("min_severity", "low"),
                max_severity=config.get("max_severity"),
                min_count=config.get("min_count"),
                exact_count=config.get("exact_count"),
            )

        # Issue count rule
        elif rule_type == "issue_count":
            return IssueCountRule(
                min_issues=config.get("min_issues"),
                max_issues=config.get("max_issues"),
                count_type=config.get("count_type", "total"),
            )

        # Status rule
        elif rule_type == "status":
            return StatusRule(
                statuses=config.get("statuses", []),
                negate=config.get("negate", False),
            )

        # Tag rule
        elif rule_type == "tag":
            return TagRule(
                tags=config.get("tags", {}),
                match_all=config.get("match_all", True),
                negate=config.get("negate", False),
            )

        # Data asset rule
        elif rule_type == "data_asset":
            return DataAssetRule(
                pattern=config.get("pattern", "*"),
                is_regex=config.get("is_regex", False),
                case_sensitive=config.get("case_sensitive", True),
            )

        # Metadata rule
        elif rule_type == "metadata":
            return MetadataRule(
                key_path=config.get("key_path", ""),
                expected_value=config.get("expected_value"),
                comparator=config.get("comparator", "eq"),
            )

        # Time window rule
        elif rule_type == "time_window":
            return TimeWindowRule(
                start_time=config.get("start_time"),
                end_time=config.get("end_time"),
                days_of_week=config.get("days_of_week"),
                timezone=config.get("timezone", "UTC"),
            )

        # Pass rate rule
        elif rule_type == "pass_rate":
            return PassRateRule(
                min_rate=config.get("min_rate"),
                max_rate=config.get("max_rate"),
            )

        # Error rule
        elif rule_type == "error":
            return ErrorRule(
                pattern=config.get("pattern"),
                negate=config.get("negate", False),
            )

        # Combinators
        elif rule_type == "all_of":
            sub_rules = [
                self._build_rule_from_config(r)
                for r in config.get("rules", [])
            ]
            return AllOf(sub_rules)

        elif rule_type == "any_of":
            sub_rules = [
                self._build_rule_from_config(r)
                for r in config.get("rules", [])
            ]
            return AnyOf(sub_rules)

        elif rule_type == "not":
            inner_rule = self._build_rule_from_config(config.get("rule", {}))
            return NotRule(inner_rule)

        else:
            raise ValueError(f"Unknown rule type: {rule_type}")

    async def match_routes(self, event: NotificationEvent) -> list[str]:
        """Match event against routing rules and return channel IDs.

        Args:
            event: Notification event to match.

        Returns:
            List of channel IDs from matching routes.
        """
        if not self._router:
            await self._build_router()

        # Build RouteContext from event
        context = self._build_route_context(event)

        # Match routes
        matched_channels: set[str] = set()
        for route in self._router.routes:
            try:
                if route.rule.matches(context):
                    matched_channels.update(route.actions)
                    logger.debug(f"Route '{route.name}' matched, channels: {route.actions}")
            except Exception as e:
                logger.warning(f"Error matching route '{route.name}': {e}")

        return list(matched_channels)

    def _build_route_context(self, event: NotificationEvent) -> RouteContext:
        """Build RouteContext from NotificationEvent."""
        # Extract data from different event types
        total_issues = 0
        critical_issues = 0
        high_issues = 0
        medium_issues = 0
        low_issues = 0
        info_issues = 0
        status = "unknown"
        data_asset = ""
        tags: dict[str, str] = {}
        metadata: dict[str, Any] = {}

        if isinstance(event, (ValidationFailedEvent, ScheduleFailedEvent)):
            total_issues = getattr(event, "total_issues", 0)
            if getattr(event, "has_critical", False):
                critical_issues = 1
            if getattr(event, "has_high", False):
                high_issues = 1
            status = "failure"
            data_asset = getattr(event, "source_name", "")

        elif isinstance(event, DriftDetectedEvent):
            status = "drift_detected"
            data_asset = getattr(event, "source_name", "")
            metadata["drift_percentage"] = getattr(event, "drift_percentage", 0)

        return RouteContext(
            checkpoint_name=event.event_type,
            run_id=getattr(event, "validation_id", str(id(event))),
            status=status,
            data_asset=data_asset,
            run_time=event.timestamp,
            total_issues=total_issues,
            critical_issues=critical_issues,
            high_issues=high_issues,
            medium_issues=medium_issues,
            low_issues=low_issues,
            info_issues=info_issues,
            tags=tags,
            metadata=metadata,
        )

    # =========================================================================
    # Deduplication
    # =========================================================================

    async def _build_deduplicator(self) -> None:
        """Build NotificationDeduplicator from database config."""
        from truthound_dashboard.db.models import DeduplicationConfig

        result = await self.session.execute(
            select(DeduplicationConfig).where(DeduplicationConfig.is_active == True)
        )
        config = result.scalar_one_or_none()

        if config:
            # Map dashboard policy to truthound policy
            policy_map = {
                "basic": DeduplicationPolicy.BASIC,
                "severity": DeduplicationPolicy.SEVERITY,
                "issue_based": DeduplicationPolicy.ISSUE_BASED,
                "strict": DeduplicationPolicy.STRICT,
                "none": DeduplicationPolicy.NONE,
            }
            policy = policy_map.get(config.policy, DeduplicationPolicy.BASIC)

            truthound_config = TruthoundDeduplicationConfig(
                enabled=True,
                policy=policy,
                default_window=TimeWindow(seconds=config.window_seconds),
            )

            self._deduplicator = NotificationDeduplicator(
                store=InMemoryDeduplicationStore(),
                config=truthound_config,
            )
            logger.info(
                f"Built deduplicator with policy={config.policy}, "
                f"window={config.window_seconds}s"
            )
        else:
            # Default deduplicator
            self._deduplicator = NotificationDeduplicator(
                store=InMemoryDeduplicationStore(),
                config=TruthoundDeduplicationConfig(
                    enabled=True,
                    policy=DeduplicationPolicy.BASIC,
                    default_window=TimeWindow(minutes=5),
                ),
            )
            logger.info("Built default deduplicator (no active config found)")

    async def is_duplicate(
        self,
        event: NotificationEvent,
        channel_id: str,
    ) -> bool:
        """Check if notification is a duplicate.

        Args:
            event: Notification event.
            channel_id: Target channel ID.

        Returns:
            True if duplicate (should be suppressed), False otherwise.
        """
        if not self._deduplicator:
            await self._build_deduplicator()

        # Generate fingerprint
        fingerprint = NotificationFingerprint.generate(
            checkpoint_name=event.event_type,
            action_type=channel_id,
            severity=self._get_event_severity(event),
            data_asset=getattr(event, "source_name", ""),
        )

        # Check using the deduplicator's is_duplicate method
        return self._deduplicator.is_duplicate_fingerprint(fingerprint)

    async def mark_notification_sent(
        self,
        event: NotificationEvent,
        channel_id: str,
    ) -> None:
        """Mark notification as sent for deduplication tracking.

        Args:
            event: Notification event.
            channel_id: Target channel ID.
        """
        if not self._deduplicator:
            return

        fingerprint = NotificationFingerprint.generate(
            checkpoint_name=event.event_type,
            action_type=channel_id,
            severity=self._get_event_severity(event),
            data_asset=getattr(event, "source_name", ""),
        )
        self._deduplicator.mark_sent(fingerprint)

    def _get_event_severity(self, event: NotificationEvent) -> str:
        """Extract severity from event."""
        if hasattr(event, "has_critical") and event.has_critical:
            return "critical"
        elif hasattr(event, "has_high") and event.has_high:
            return "high"
        return "medium"

    # =========================================================================
    # Throttling
    # =========================================================================

    async def _build_throttler(self) -> None:
        """Build NotificationThrottler from database config."""
        from truthound_dashboard.db.models import ThrottlingConfig

        result = await self.session.execute(
            select(ThrottlingConfig).where(ThrottlingConfig.is_active == True)
        )
        configs = result.scalars().all()

        builder = ThrottlerBuilder()

        # Apply first active global config (channel_id is None)
        global_config = next((c for c in configs if c.channel_id is None), None)
        if global_config:
            if global_config.per_minute:
                builder.with_per_minute_limit(global_config.per_minute)
            if global_config.per_hour:
                builder.with_per_hour_limit(global_config.per_hour)
            if global_config.per_day:
                builder.with_per_day_limit(global_config.per_day)
            builder.with_burst_allowance(global_config.burst_allowance)
            logger.info(
                f"Built throttler with per_minute={global_config.per_minute}, "
                f"per_hour={global_config.per_hour}, per_day={global_config.per_day}"
            )
        else:
            # Default throttling
            builder.with_per_minute_limit(10)
            builder.with_per_hour_limit(100)
            builder.with_per_day_limit(500)
            logger.info("Built default throttler (no active config found)")

        builder.with_algorithm("token_bucket")
        builder.with_scope(RateLimitScope.PER_ACTION)

        self._throttler = builder.build()

    async def is_throttled(self, channel_id: str) -> bool:
        """Check if channel is throttled.

        Args:
            channel_id: Target channel ID.

        Returns:
            True if throttled (should not send), False otherwise.
        """
        if not self._throttler:
            await self._build_throttler()

        result = self._throttler.check(
            action_type=channel_id,
            checkpoint_name="notification",
        )
        return not result.allowed

    async def acquire_throttle_permit(self, channel_id: str) -> bool:
        """Acquire a throttle permit (check and consume).

        Args:
            channel_id: Target channel ID.

        Returns:
            True if permit acquired, False if throttled.
        """
        if not self._throttler:
            await self._build_throttler()

        result = self._throttler.acquire(
            action_type=channel_id,
            checkpoint_name="notification",
        )
        return result.allowed

    # =========================================================================
    # Escalation
    # =========================================================================

    async def _build_escalation_engine(self) -> None:
        """Build EscalationEngine from database policies."""
        from truthound_dashboard.db.models import EscalationPolicyModel

        result = await self.session.execute(
            select(EscalationPolicyModel).where(EscalationPolicyModel.is_active == True)
        )
        policies = result.scalars().all()

        config = EscalationEngineConfig(
            store_type="memory",
            metrics_enabled=True,
        )
        self._escalation_engine = EscalationEngine(config)

        for policy_model in policies:
            try:
                truthound_policy = self._build_escalation_policy(policy_model)
                self._escalation_engine.register_policy(truthound_policy)
                logger.debug(f"Registered escalation policy: {policy_model.name}")
            except Exception as e:
                logger.warning(
                    f"Failed to build escalation policy '{policy_model.name}': {e}"
                )

        # Set notification handler (we'll just log for now, actual sending
        # is handled by dispatcher)
        async def notification_handler(record, level, targets):
            logger.info(
                f"Escalation notification: record={record.id}, "
                f"level={level.level}, targets={[t.name for t in targets]}"
            )
            return True

        self._escalation_engine.set_notification_handler(notification_handler)
        logger.info(f"Built escalation engine with {len(policies)} policies")

    def _build_escalation_policy(
        self, model: "EscalationPolicyModel"
    ) -> EscalationPolicy:
        """Build truthound EscalationPolicy from database model."""
        levels = []
        for level_config in model.levels:
            targets = []
            for target_config in level_config.get("targets", []):
                target_type = TargetType(target_config.get("type", "user"))
                targets.append(
                    EscalationTarget(
                        type=target_type,
                        identifier=target_config.get("identifier", ""),
                        name=target_config.get("name", ""),
                        metadata=target_config.get("metadata", {}),
                    )
                )

            levels.append(
                EscalationLevel(
                    level=level_config.get("level", 1),
                    delay_minutes=level_config.get("delay_minutes", 0),
                    targets=targets,
                    repeat_count=level_config.get("repeat_count", 0),
                    repeat_interval_minutes=level_config.get(
                        "repeat_interval_minutes", 5
                    ),
                    require_ack=level_config.get("require_ack", True),
                )
            )

        return EscalationPolicy(
            name=model.name,
            description=model.description or "",
            levels=levels,
            enabled=True,
            triggers=[EscalationTrigger.UNACKNOWLEDGED],
            max_escalations=model.max_escalations,
        )

    async def trigger_escalation(
        self,
        event: NotificationEvent,
        policy_name: str | None = None,
    ) -> str | None:
        """Trigger escalation for an event.

        Args:
            event: Notification event.
            policy_name: Optional specific policy name, or auto-select.

        Returns:
            Escalation record ID if triggered, None otherwise.
        """
        if not self._escalation_engine:
            await self._build_escalation_engine()

        # Determine severity to select policy
        severity = self._get_event_severity(event)
        if not policy_name:
            # Auto-select policy based on severity
            policy_name = f"{severity}_alerts"

        incident_id = f"{event.event_type}-{getattr(event, 'validation_id', id(event))}"

        try:
            result = await self._escalation_engine.trigger(
                incident_id=incident_id,
                context={
                    "event_type": event.event_type,
                    "severity": severity,
                    "source_name": getattr(event, "source_name", ""),
                    "timestamp": event.timestamp.isoformat(),
                },
                policy_name=policy_name,
            )
            if result.success:
                return result.record.id
        except Exception as e:
            logger.warning(f"Failed to trigger escalation: {e}")

        return None

    async def acknowledge_escalation(
        self, record_id: str, actor: str
    ) -> bool:
        """Acknowledge an escalation.

        Args:
            record_id: Escalation record ID.
            actor: Who is acknowledging.

        Returns:
            True if successful.
        """
        if not self._escalation_engine:
            return False

        try:
            result = await self._escalation_engine.acknowledge(
                record_id=record_id,
                acknowledged_by=actor,
            )
            return result.success
        except Exception as e:
            logger.error(f"Failed to acknowledge escalation: {e}")
            return False

    async def resolve_escalation(
        self, record_id: str, actor: str
    ) -> bool:
        """Resolve an escalation.

        Args:
            record_id: Escalation record ID.
            actor: Who is resolving.

        Returns:
            True if successful.
        """
        if not self._escalation_engine:
            return False

        try:
            result = await self._escalation_engine.resolve(
                record_id=record_id,
                resolved_by=actor,
            )
            return result.success
        except Exception as e:
            logger.error(f"Failed to resolve escalation: {e}")
            return False

    # =========================================================================
    # Stats
    # =========================================================================

    def get_stats(self) -> TruthoundStats:
        """Get aggregated stats from all truthound components.

        Returns:
            TruthoundStats with stats from each component.
        """
        stats = TruthoundStats()

        # Router stats
        if self._router:
            stats.routing = {
                "total_routes": len(self._router.routes),
                "mode": self._router.mode.value if hasattr(self._router, "mode") else "unknown",
            }

        # Deduplication stats
        if self._deduplicator:
            try:
                dedup_stats = self._deduplicator.get_stats()
                stats.deduplication = {
                    "total_evaluated": getattr(dedup_stats, "total_evaluated", 0),
                    "suppressed": getattr(dedup_stats, "suppressed", 0),
                    "suppression_ratio": getattr(dedup_stats, "suppression_ratio", 0.0),
                    "active_fingerprints": getattr(dedup_stats, "active_fingerprints", 0),
                }
            except Exception as e:
                logger.warning(f"Failed to get deduplication stats: {e}")

        # Throttling stats
        if self._throttler:
            try:
                throttle_stats = self._throttler.get_stats()
                stats.throttling = {
                    "total_checked": getattr(throttle_stats, "total_checked", 0),
                    "total_allowed": getattr(throttle_stats, "total_allowed", 0),
                    "total_throttled": getattr(throttle_stats, "total_throttled", 0),
                    "throttle_rate": getattr(throttle_stats, "throttle_rate", 0.0),
                    "allow_rate": getattr(throttle_stats, "allow_rate", 0.0),
                }
            except Exception as e:
                logger.warning(f"Failed to get throttling stats: {e}")

        # Escalation stats
        if self._escalation_engine:
            try:
                esc_stats = self._escalation_engine.get_stats()
                stats.escalation = {
                    "total_escalations": getattr(esc_stats, "total_escalations", 0),
                    "active_escalations": getattr(esc_stats, "active_escalations", 0),
                    "acknowledged_count": getattr(esc_stats, "acknowledged_count", 0),
                    "resolved_count": getattr(esc_stats, "resolved_count", 0),
                    "acknowledgment_rate": getattr(esc_stats, "acknowledgment_rate", 0.0),
                    "avg_time_to_acknowledge": getattr(
                        esc_stats, "avg_time_to_acknowledge_seconds", 0
                    ),
                }
            except Exception as e:
                logger.warning(f"Failed to get escalation stats: {e}")

        return stats

    # =========================================================================
    # Combined Check
    # =========================================================================

    async def should_send_notification(
        self,
        event: NotificationEvent,
        channel_id: str,
    ) -> bool:
        """Check if notification should be sent (dedup + throttle).

        This is a convenience method that checks both deduplication
        and throttling in one call.

        Args:
            event: Notification event.
            channel_id: Target channel ID.

        Returns:
            True if notification should be sent.
        """
        # Check deduplication
        if await self.is_duplicate(event, channel_id):
            logger.debug(f"Notification suppressed (duplicate): {event.event_type}")
            return False

        # Check throttling
        if not await self.acquire_throttle_permit(channel_id):
            logger.debug(f"Notification suppressed (throttled): {channel_id}")
            return False

        return True

    async def reload_config(self) -> None:
        """Reload all configurations from database.

        Call this after configuration changes to rebuild all components.
        """
        self._initialized = False
        self._router = None
        self._deduplicator = None
        self._throttler = None
        # Note: We don't reset escalation engine as it may have active incidents
        await self.initialize()


# Factory function
async def get_truthound_adapter(session: AsyncSession) -> TruthoundNotificationAdapter:
    """Get an initialized TruthoundNotificationAdapter.

    Args:
        session: Database session.

    Returns:
        Initialized adapter.
    """
    adapter = TruthoundNotificationAdapter(session)
    await adapter.initialize()
    return adapter
