"""Routing interfaces for checkpoint-based validation pipelines.

Routing rules determine which actions to execute based on validation
results. They enable complex conditional logic for notifications and
post-validation processing.

This module defines abstract interfaces for routing that are loosely
coupled from truthound's checkpoint.routing module.

Routing features:
- Jinja2-based rule expressions
- Compound rules (AllOf, AnyOf, Not)
- Priority-based routing
- Action fanout (parallel execution)
- Context-based routing
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from truthound_dashboard.core.interfaces.actions import (
        ActionContext,
        ActionProtocol,
        ActionResult,
    )
    from truthound_dashboard.core.interfaces.checkpoint import CheckpointResult


class RouteMode(str, Enum):
    """How routes are evaluated."""

    FIRST_MATCH = "first_match"  # Stop at first matching route
    ALL_MATCHES = "all_matches"  # Execute all matching routes
    PRIORITY = "priority"  # Execute in priority order


class RoutePriority(int, Enum):
    """Priority levels for routes."""

    CRITICAL = 100
    HIGH = 75
    MEDIUM = 50
    LOW = 25
    DEFAULT = 0


@dataclass
class RouteContext:
    """Context passed to routing rule evaluation.

    Attributes:
        checkpoint_result: The validation result.
        run_id: Unique run identifier.
        checkpoint_name: Name of the checkpoint.
        tags: Tags from the checkpoint.
        metadata: Additional metadata.
        variables: Custom variables for rule evaluation.
    """

    checkpoint_result: "CheckpointResult"
    run_id: str
    checkpoint_name: str
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)

    def to_template_context(self) -> dict[str, Any]:
        """Convert to Jinja2 template context.

        Returns:
            Dictionary suitable for Jinja2 rendering.
        """
        result = self.checkpoint_result
        return {
            # Result properties
            "status": result.status.value,
            "passed": result.status.value == "success",
            "failed": result.status.value == "failure",
            "has_critical": getattr(result, "has_critical", False),
            "has_high": getattr(result, "has_high", False),
            "issue_count": getattr(result, "issue_count", 0),
            "critical_count": getattr(result, "critical_count", 0),
            "high_count": getattr(result, "high_count", 0),
            "medium_count": getattr(result, "medium_count", 0),
            "low_count": getattr(result, "low_count", 0),
            "row_count": getattr(result, "row_count", 0),
            "column_count": getattr(result, "column_count", 0),
            # Context properties
            "run_id": self.run_id,
            "checkpoint_name": self.checkpoint_name,
            "tags": self.tags,
            "metadata": self.metadata,
            # Custom variables
            **self.variables,
        }


@runtime_checkable
class RoutingRuleProtocol(Protocol):
    """Protocol for routing rule implementations.

    Routing rules evaluate checkpoint results and return True
    if the associated actions should be executed.

    Example:
        class SeverityRule:
            def __init__(self, min_severity: str):
                self.min_severity = min_severity

            def evaluate(self, context: RouteContext) -> bool:
                return context.checkpoint_result.has_severity(self.min_severity)
    """

    @property
    def name(self) -> str:
        """Get rule name."""
        ...

    @property
    def expression(self) -> str:
        """Get the rule expression (for Jinja2 rules)."""
        ...

    def evaluate(self, context: RouteContext) -> bool:
        """Evaluate the rule against the context.

        Args:
            context: Routing context with checkpoint result.

        Returns:
            True if rule matches (actions should execute).
        """
        ...


class BaseRoutingRule(ABC):
    """Abstract base class for routing rules.

    Provides common functionality for all routing rules.
    Subclasses must implement the evaluate method.
    """

    def __init__(
        self,
        name: str = "",
        description: str = "",
    ) -> None:
        """Initialize rule.

        Args:
            name: Rule name.
            description: Rule description.
        """
        self._name = name or self.__class__.__name__
        self._description = description

    @property
    def name(self) -> str:
        """Get rule name."""
        return self._name

    @property
    def expression(self) -> str:
        """Get the rule expression."""
        return ""

    @property
    def description(self) -> str:
        """Get rule description."""
        return self._description

    @abstractmethod
    def evaluate(self, context: RouteContext) -> bool:
        """Evaluate the rule."""
        ...


class Jinja2Rule(BaseRoutingRule):
    """Jinja2 expression-based routing rule.

    Evaluates a Jinja2 expression against the routing context.
    The expression should evaluate to a boolean.

    Example:
        rule = Jinja2Rule("critical_alert", "has_critical or critical_count > 0")
        if rule.evaluate(context):
            # Send critical alert
    """

    def __init__(
        self,
        name: str,
        expression: str,
        description: str = "",
    ) -> None:
        """Initialize Jinja2 rule.

        Args:
            name: Rule name.
            expression: Jinja2 expression that evaluates to boolean.
            description: Rule description.
        """
        super().__init__(name=name, description=description)
        self._expression = expression
        self._compiled: Any | None = None

    @property
    def expression(self) -> str:
        """Get the Jinja2 expression."""
        return self._expression

    def evaluate(self, context: RouteContext) -> bool:
        """Evaluate the Jinja2 expression.

        Args:
            context: Routing context.

        Returns:
            True if expression evaluates to truthy.
        """
        try:
            from jinja2 import Environment
        except ImportError:
            # Fallback to simple eval for basic expressions
            return self._fallback_evaluate(context)

        env = Environment()
        template_str = "{{ " + self._expression + " }}"
        template = env.from_string(template_str)
        result = template.render(**context.to_template_context())
        return result.lower() in ("true", "1", "yes")

    def _fallback_evaluate(self, context: RouteContext) -> bool:
        """Fallback evaluation without Jinja2."""
        ctx = context.to_template_context()

        # Handle simple expressions
        expr = self._expression.strip()

        # Direct variable lookup
        if expr in ctx:
            return bool(ctx[expr])

        # Simple comparisons
        for op in [" > ", " >= ", " < ", " <= ", " == ", " != "]:
            if op in expr:
                left, right = expr.split(op, 1)
                left_val = ctx.get(left.strip(), left.strip())
                right_val = ctx.get(right.strip(), right.strip())

                try:
                    left_val = float(left_val) if not isinstance(left_val, bool) else left_val
                    right_val = float(right_val) if not isinstance(right_val, bool) else right_val
                except (ValueError, TypeError):
                    pass

                if op == " > ":
                    return left_val > right_val
                elif op == " >= ":
                    return left_val >= right_val
                elif op == " < ":
                    return left_val < right_val
                elif op == " <= ":
                    return left_val <= right_val
                elif op == " == ":
                    return left_val == right_val
                elif op == " != ":
                    return left_val != right_val

        # Boolean operations
        if " or " in expr:
            parts = expr.split(" or ")
            return any(bool(ctx.get(p.strip(), False)) for p in parts)

        if " and " in expr:
            parts = expr.split(" and ")
            return all(bool(ctx.get(p.strip(), False)) for p in parts)

        return False


class AllOf(BaseRoutingRule):
    """Compound rule that matches when ALL child rules match.

    Example:
        rule = AllOf([
            Jinja2Rule("critical", "has_critical"),
            Jinja2Rule("high_count", "high_count > 10"),
        ])
    """

    def __init__(
        self,
        rules: list[BaseRoutingRule],
        name: str = "",
        description: str = "",
    ) -> None:
        """Initialize AllOf rule.

        Args:
            rules: Child rules that must all match.
            name: Rule name.
            description: Rule description.
        """
        super().__init__(name=name or "AllOf", description=description)
        self._rules = rules

    @property
    def rules(self) -> list[BaseRoutingRule]:
        """Get child rules."""
        return self._rules

    @property
    def expression(self) -> str:
        """Get combined expression."""
        exprs = [r.expression for r in self._rules if r.expression]
        return " and ".join(f"({e})" for e in exprs)

    def evaluate(self, context: RouteContext) -> bool:
        """Evaluate all child rules.

        Returns True only if all rules match.
        """
        return all(rule.evaluate(context) for rule in self._rules)


class AnyOf(BaseRoutingRule):
    """Compound rule that matches when ANY child rule matches.

    Example:
        rule = AnyOf([
            Jinja2Rule("critical", "has_critical"),
            Jinja2Rule("error", "status == 'error'"),
        ])
    """

    def __init__(
        self,
        rules: list[BaseRoutingRule],
        name: str = "",
        description: str = "",
    ) -> None:
        """Initialize AnyOf rule.

        Args:
            rules: Child rules (any one can match).
            name: Rule name.
            description: Rule description.
        """
        super().__init__(name=name or "AnyOf", description=description)
        self._rules = rules

    @property
    def rules(self) -> list[BaseRoutingRule]:
        """Get child rules."""
        return self._rules

    @property
    def expression(self) -> str:
        """Get combined expression."""
        exprs = [r.expression for r in self._rules if r.expression]
        return " or ".join(f"({e})" for e in exprs)

    def evaluate(self, context: RouteContext) -> bool:
        """Evaluate all child rules.

        Returns True if any rule matches.
        """
        return any(rule.evaluate(context) for rule in self._rules)


class NotRule(BaseRoutingRule):
    """Compound rule that inverts another rule.

    Example:
        rule = NotRule(Jinja2Rule("success", "passed"))
        # Matches when validation did NOT pass
    """

    def __init__(
        self,
        rule: BaseRoutingRule,
        name: str = "",
        description: str = "",
    ) -> None:
        """Initialize Not rule.

        Args:
            rule: Rule to invert.
            name: Rule name.
            description: Rule description.
        """
        super().__init__(name=name or "Not", description=description)
        self._rule = rule

    @property
    def rule(self) -> BaseRoutingRule:
        """Get the inverted rule."""
        return self._rule

    @property
    def expression(self) -> str:
        """Get negated expression."""
        return f"not ({self._rule.expression})"

    def evaluate(self, context: RouteContext) -> bool:
        """Evaluate the inverted rule.

        Returns True if the child rule does NOT match.
        """
        return not self._rule.evaluate(context)


class AlwaysRule(BaseRoutingRule):
    """Rule that always matches."""

    def __init__(self, name: str = "always") -> None:
        super().__init__(name=name, description="Always matches")

    @property
    def expression(self) -> str:
        return "True"

    def evaluate(self, context: RouteContext) -> bool:
        return True


class NeverRule(BaseRoutingRule):
    """Rule that never matches."""

    def __init__(self, name: str = "never") -> None:
        super().__init__(name=name, description="Never matches")

    @property
    def expression(self) -> str:
        return "False"

    def evaluate(self, context: RouteContext) -> bool:
        return False


# =============================================================================
# Route Definition
# =============================================================================


@dataclass
class Route:
    """A route defines a rule and its associated actions.

    When the rule matches, the actions are executed.

    Attributes:
        name: Route name for identification.
        rule: Routing rule to evaluate.
        actions: Actions to execute when rule matches.
        priority: Priority for route ordering.
        enabled: Whether this route is enabled.
        metadata: Additional metadata.
        stop_on_match: Stop evaluating other routes after this one matches.
    """

    name: str
    rule: BaseRoutingRule
    actions: list[str]  # Action names
    priority: RoutePriority = RoutePriority.DEFAULT
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    stop_on_match: bool = False

    def evaluate(self, context: RouteContext) -> bool:
        """Evaluate the route's rule.

        Args:
            context: Routing context.

        Returns:
            True if route matches.
        """
        if not self.enabled:
            return False
        return self.rule.evaluate(context)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "rule_expression": self.rule.expression,
            "actions": self.actions,
            "priority": self.priority.value,
            "enabled": self.enabled,
            "metadata": self.metadata,
            "stop_on_match": self.stop_on_match,
        }


# =============================================================================
# Router Protocol
# =============================================================================


@runtime_checkable
class RouterProtocol(Protocol):
    """Protocol for router implementations.

    Routers evaluate routes and determine which actions to execute.

    Example:
        router = Router(mode=RouteMode.FIRST_MATCH)
        router.add_route(Route(
            name="critical_alert",
            rule=Jinja2Rule("critical", "has_critical"),
            actions=["pagerduty", "slack_critical"],
        ))

        matched_actions = router.route(context)
    """

    @property
    def mode(self) -> RouteMode:
        """Get routing mode."""
        ...

    @property
    def routes(self) -> list[Route]:
        """Get all routes."""
        ...

    def add_route(self, route: Route) -> None:
        """Add a route to the router.

        Args:
            route: Route to add.
        """
        ...

    def remove_route(self, name: str) -> bool:
        """Remove a route by name.

        Args:
            name: Route name.

        Returns:
            True if route was removed.
        """
        ...

    def route(self, context: RouteContext) -> list[str]:
        """Evaluate routes and return matching action names.

        Args:
            context: Routing context.

        Returns:
            List of action names to execute.
        """
        ...


class Router:
    """Default router implementation.

    Evaluates routes based on the configured mode and returns
    the actions that should be executed.
    """

    def __init__(
        self,
        mode: RouteMode = RouteMode.ALL_MATCHES,
        routes: list[Route] | None = None,
    ) -> None:
        """Initialize router.

        Args:
            mode: Routing mode.
            routes: Initial routes.
        """
        self._mode = mode
        self._routes: list[Route] = routes or []

    @property
    def mode(self) -> RouteMode:
        """Get routing mode."""
        return self._mode

    @property
    def routes(self) -> list[Route]:
        """Get all routes."""
        return self._routes.copy()

    def add_route(self, route: Route) -> None:
        """Add a route."""
        self._routes.append(route)
        # Re-sort by priority if in priority mode
        if self._mode == RouteMode.PRIORITY:
            self._routes.sort(key=lambda r: r.priority.value, reverse=True)

    def remove_route(self, name: str) -> bool:
        """Remove a route by name."""
        for i, route in enumerate(self._routes):
            if route.name == name:
                del self._routes[i]
                return True
        return False

    def route(self, context: RouteContext) -> list[str]:
        """Evaluate routes and return matching action names.

        Args:
            context: Routing context.

        Returns:
            List of unique action names to execute.
        """
        actions: list[str] = []
        seen: set[str] = set()

        # Sort routes if in priority mode
        routes = self._routes
        if self._mode == RouteMode.PRIORITY:
            routes = sorted(routes, key=lambda r: r.priority.value, reverse=True)

        for route in routes:
            if route.evaluate(context):
                for action in route.actions:
                    if action not in seen:
                        actions.append(action)
                        seen.add(action)

                # Stop if configured or first match mode
                if route.stop_on_match or self._mode == RouteMode.FIRST_MATCH:
                    break

        return actions

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mode": self._mode.value,
            "routes": [r.to_dict() for r in self._routes],
        }
