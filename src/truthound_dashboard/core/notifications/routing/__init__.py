"""Advanced routing engine using truthound.checkpoint.routing.

This module provides a routing system for directing notifications to
appropriate channels, using truthound's routing infrastructure.

Key Components from truthound.checkpoint.routing:
    - ActionRouter: Main routing engine with route modes
    - Route: Defines a route with rule, actions, and priority
    - RouteContext: Context data for rule evaluation
    - RouteMode: FIRST_MATCH, ALL_MATCHES, PRIORITY_GROUP

Built-in Rules from truthound (11 types):
    - AlwaysRule / NeverRule: Always match / never match
    - SeverityRule: Match based on issue severity
    - IssueCountRule: Match based on issue count
    - StatusRule: Match based on checkpoint status
    - TagRule: Match based on tag presence/value
    - DataAssetRule: Match based on data asset name pattern
    - MetadataRule: Match based on metadata values
    - TimeWindowRule: Match based on time period
    - PassRateRule: Match based on pass rate
    - ErrorRule: Match based on error occurrence

Combinators from truthound:
    - AllOf: All rules must match (AND)
    - AnyOf: At least one rule must match (OR)
    - NotRule: Invert rule result (NOT)

Example:
    from truthound.checkpoint.routing import (
        ActionRouter, Route, AllOf
    )
    from truthound.checkpoint.routing.rules import (
        SeverityRule, TagRule
    )
    from truthound.checkpoint.routing.base import RouteMode

    # Create rules using truthound
    critical_prod_rule = AllOf([
        SeverityRule(min_severity="critical"),
        TagRule(tags={"env": "prod"}),
    ])

    # Create route
    route = Route(
        name="critical_prod",
        rule=critical_prod_rule,
        actions=[PagerDutyAction(...)],
        priority=100,
    )

    # Create router
    router = ActionRouter(mode=RouteMode.ALL_MATCHES)
    router.add_route(route)
"""

# Re-export from truthound.checkpoint.routing
from truthound.checkpoint.routing import (
    ActionRouter,
    Route,
    AllOf,
    AnyOf,
    NotRule,
)
from truthound.checkpoint.routing.base import (
    RouteContext,
    RouteMode,
    RoutePriority,
)
from truthound.checkpoint.routing.rules import (
    AlwaysRule,
    NeverRule,
    SeverityRule,
    IssueCountRule,
    StatusRule,
    TagRule,
    DataAssetRule,
    MetadataRule,
    TimeWindowRule,
    PassRateRule,
    ErrorRule,
)

# Dashboard-specific adapters for backward compatibility
from .engine import (
    DashboardRouteContext,
    DashboardRoutingResult,
    create_route_context_from_event,
)
from .config_parser import (
    ConfigParser,
    RouteConfig,
    RoutingConfig,
    parse_routing_config,
)

__all__ = [
    # truthound core
    "ActionRouter",
    "Route",
    "RouteContext",
    "RouteMode",
    "RoutePriority",
    # truthound rules
    "AlwaysRule",
    "NeverRule",
    "SeverityRule",
    "IssueCountRule",
    "StatusRule",
    "TagRule",
    "DataAssetRule",
    "MetadataRule",
    "TimeWindowRule",
    "PassRateRule",
    "ErrorRule",
    # truthound combinators
    "AllOf",
    "AnyOf",
    "NotRule",
    # Dashboard adapters
    "DashboardRouteContext",
    "DashboardRoutingResult",
    "create_route_context_from_event",
    # Config
    "ConfigParser",
    "RouteConfig",
    "RoutingConfig",
    "parse_routing_config",
]
