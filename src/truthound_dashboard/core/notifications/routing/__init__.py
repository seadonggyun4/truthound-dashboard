"""Advanced routing engine for notification dispatch.

This module provides a flexible, rule-based routing system for directing
notifications to appropriate channels based on configurable conditions.

Features:
    - 11 built-in rule types (severity, issue count, time window, etc.)
    - Rule combinators (AllOf, AnyOf, NotRule)
    - Plugin architecture for custom rules
    - YAML/JSON configuration support
    - Priority-based route ordering

Example:
    from truthound_dashboard.core.notifications.routing import (
        ActionRouter,
        Route,
        RouteContext,
        SeverityRule,
        AllOf,
    )

    # Create rules
    critical_rule = SeverityRule(min_severity="critical")
    production_rule = TagRule(tags=["production"])
    combined_rule = AllOf(rules=[critical_rule, production_rule])

    # Create route
    route = Route(
        name="critical_production",
        rule=combined_rule,
        actions=["channel-1", "channel-2"],
        priority=100,
    )

    # Create router and match
    router = ActionRouter(routes=[route])
    context = RouteContext(event=event, metadata={"tags": ["production"]})
    matched_routes = await router.match(context)
"""

from .combinators import AllOf, AnyOf, NotRule
from .config import RouteConfigParser
from .engine import ActionRouter, Route, RouteContext, RoutingResult
from .rules import (
    AlwaysRule,
    BaseRule,
    DataAssetRule,
    ErrorRule,
    IssueCountRule,
    MetadataRule,
    NeverRule,
    PassRateRule,
    RuleRegistry,
    SeverityRule,
    StatusRule,
    TagRule,
    TimeWindowRule,
)

__all__ = [
    # Base
    "BaseRule",
    "RuleRegistry",
    # Rules
    "SeverityRule",
    "IssueCountRule",
    "PassRateRule",
    "TimeWindowRule",
    "TagRule",
    "DataAssetRule",
    "MetadataRule",
    "StatusRule",
    "ErrorRule",
    "AlwaysRule",
    "NeverRule",
    # Combinators
    "AllOf",
    "AnyOf",
    "NotRule",
    # Engine
    "ActionRouter",
    "Route",
    "RouteContext",
    "RoutingResult",
    # Config
    "RouteConfigParser",
]
