"""Checkpoint implementation for validation pipeline orchestration.

Provides the core Checkpoint class that orchestrates the complete
validation pipeline from data loading through action execution.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from truthound_dashboard.core.interfaces.actions import (
    ActionContext,
    ActionProtocol,
    ActionResult,
    ActionStatus,
    AsyncActionProtocol,
    BaseAction,
    AsyncBaseAction,
)
from truthound_dashboard.core.interfaces.checkpoint import (
    CheckpointConfig,
    CheckpointProtocol,
    CheckpointResult,
    CheckpointStatus,
)
from truthound_dashboard.core.interfaces.routing import (
    Route,
    RouteContext,
    Router,
    RouteMode,
)
from truthound_dashboard.core.interfaces.triggers import BaseTrigger

if TYPE_CHECKING:
    from truthound_dashboard.core.backends.base import BaseDataQualityBackend

logger = logging.getLogger(__name__)


class Checkpoint(CheckpointProtocol):
    """Concrete checkpoint implementation.

    Orchestrates the complete validation pipeline:
    1. Load data from configured source
    2. Run validators
    3. Build result
    4. Evaluate routing rules
    5. Execute matched actions
    6. Return comprehensive result

    Example:
        checkpoint = Checkpoint(
            config=CheckpointConfig(
                name="daily_orders",
                source_id="orders_db",
                validators=["null", "uniqueness"],
            ),
        )

        # Add actions
        checkpoint.add_action(SlackNotificationAction(...))
        checkpoint.add_action(FileStorageAction(...))

        # Add routing
        checkpoint.set_router(Router(routes=[...]))

        # Run
        result = await checkpoint.run()
    """

    def __init__(
        self,
        config: CheckpointConfig | dict[str, Any],
        actions: list[BaseAction | AsyncBaseAction] | None = None,
        triggers: list[BaseTrigger] | None = None,
        router: Router | None = None,
        backend: "BaseDataQualityBackend | None" = None,
    ) -> None:
        """Initialize checkpoint.

        Args:
            config: Checkpoint configuration.
            actions: List of actions to execute.
            triggers: List of triggers for this checkpoint.
            router: Router for conditional action execution.
            backend: Data quality backend (uses default if None).
        """
        if isinstance(config, dict):
            config = CheckpointConfig.from_dict(config)

        self._config = config
        self._actions: dict[str, BaseAction | AsyncBaseAction] = {}
        self._triggers: list[BaseTrigger] = triggers or []
        self._router = router
        self._backend = backend

        # Register provided actions
        if actions:
            for action in actions:
                self.add_action(action)

    @property
    def name(self) -> str:
        """Get checkpoint name."""
        return self._config.name

    @property
    def config(self) -> CheckpointConfig:
        """Get checkpoint configuration."""
        return self._config

    @property
    def actions(self) -> list[BaseAction | AsyncBaseAction]:
        """Get configured actions."""
        return list(self._actions.values())

    @property
    def triggers(self) -> list[BaseTrigger]:
        """Get configured triggers."""
        return self._triggers

    @property
    def router(self) -> Router | None:
        """Get the router."""
        return self._router

    def add_action(self, action: BaseAction | AsyncBaseAction) -> None:
        """Add an action to the checkpoint.

        Args:
            action: Action to add.
        """
        self._actions[action.name] = action

    def remove_action(self, name: str) -> bool:
        """Remove an action by name.

        Args:
            name: Action name.

        Returns:
            True if action was removed.
        """
        if name in self._actions:
            del self._actions[name]
            return True
        return False

    def add_trigger(self, trigger: BaseTrigger) -> None:
        """Add a trigger to the checkpoint.

        Args:
            trigger: Trigger to add.
        """
        self._triggers.append(trigger)

    def set_router(self, router: Router) -> None:
        """Set the router for action routing.

        Args:
            router: Router to use.
        """
        self._router = router

    def _get_backend(self) -> "BaseDataQualityBackend":
        """Get the backend, initializing if needed.

        Returns:
            Data quality backend.
        """
        if self._backend is None:
            from truthound_dashboard.core.backends.factory import BackendFactory
            self._backend = BackendFactory.get_backend()
        return self._backend

    async def run(
        self,
        trigger_context: dict[str, Any] | None = None,
    ) -> CheckpointResult:
        """Run the checkpoint.

        Executes the full validation pipeline:
        1. Validate configuration
        2. Load and validate data
        3. Build checkpoint result
        4. Execute actions based on routing

        Args:
            trigger_context: Optional context from the trigger.

        Returns:
            Checkpoint result with validation and action results.
        """
        run_id = str(uuid.uuid4())
        started_at = datetime.now()

        logger.info(f"Starting checkpoint run: {self.name} (run_id={run_id})")

        try:
            # Run validation
            check_result = await self._run_validation()

            # Build checkpoint result
            result = CheckpointResult.from_check_result(
                check_result=check_result,
                checkpoint_name=self.name,
                run_id=run_id,
                config=self._config,
            )
            result.started_at = started_at
            result.completed_at = datetime.now()
            result.duration_ms = (result.completed_at - started_at).total_seconds() * 1000
            result.trigger_context = trigger_context or {}

            # Execute actions
            action_results = await self._execute_actions(result, run_id)
            result.action_results = action_results

            logger.info(
                f"Checkpoint completed: {self.name} "
                f"status={result.status.value} "
                f"issues={result.issue_count} "
                f"duration={result.duration_ms:.1f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Checkpoint failed: {self.name} error={str(e)}")
            completed_at = datetime.now()

            return CheckpointResult(
                checkpoint_name=self.name,
                run_id=run_id,
                status=CheckpointStatus.ERROR,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=(completed_at - started_at).total_seconds() * 1000,
                error_message=str(e),
                trigger_context=trigger_context or {},
            )

    async def _run_validation(self) -> Any:
        """Run the validation using the backend.

        Returns:
            Check result from the backend.
        """
        backend = self._get_backend()

        # Build data input
        data_input = await self._get_data_input()

        # Run check with configured validators
        return await backend.check(
            data=data_input,
            validators=self._config.validators or None,
            validator_config=self._config.validator_config or None,
            schema=self._config.schema_path,
            auto_schema=self._config.auto_schema,
        )

    async def _get_data_input(self) -> Any:
        """Get the data input for validation.

        Returns:
            Data input (path or DataSource).
        """
        # If source_id is set, load from database
        if self._config.source_id:
            from truthound_dashboard.core.services import get_source_data_input
            return await get_source_data_input(self._config.source_id)

        # Otherwise use source_name as path
        if self._config.source_name:
            return self._config.source_name

        raise ValueError("No source_id or source_name configured for checkpoint")

    async def _execute_actions(
        self,
        result: CheckpointResult,
        run_id: str,
    ) -> list[ActionResult]:
        """Execute actions based on routing rules.

        Args:
            result: Checkpoint result.
            run_id: Run identifier.

        Returns:
            List of action results.
        """
        action_results: list[ActionResult] = []

        # Determine which actions to execute
        if self._router:
            # Use router to determine actions
            route_context = RouteContext(
                checkpoint_result=result,
                run_id=run_id,
                checkpoint_name=self.name,
                tags=self._config.tags,
                metadata=self._config.metadata,
            )
            action_names = self._router.route(route_context)
        else:
            # Execute all actions
            action_names = list(self._actions.keys())

        # Build action context
        action_context = ActionContext(
            checkpoint_result=result,
            run_id=run_id,
            checkpoint_name=self.name,
            tags=self._config.tags,
            metadata=self._config.metadata,
        )

        # Execute actions
        for action_name in action_names:
            action = self._actions.get(action_name)
            if action is None:
                logger.warning(f"Action not found: {action_name}")
                continue

            try:
                if isinstance(action, AsyncBaseAction):
                    action_result = await action.execute_async(action_context)
                else:
                    action_result = action.execute(action_context)
                action_results.append(action_result)
            except Exception as e:
                logger.error(f"Action failed: {action_name} error={str(e)}")
                action_results.append(ActionResult(
                    action_name=action_name,
                    action_type=getattr(action, "action_type", "unknown"),
                    status=ActionStatus.FAILURE,
                    message=f"Action failed: {str(e)}",
                    error=str(e),
                ))

        return action_results


class CheckpointBuilder:
    """Builder pattern for constructing checkpoints.

    Provides a fluent interface for building checkpoints.

    Example:
        checkpoint = (
            CheckpointBuilder()
            .name("daily_orders")
            .source("orders_db")
            .validators(["null", "uniqueness", "range"])
            .action(SlackNotificationAction(...))
            .action(FileStorageAction(...))
            .route_on_failure(["slack", "pagerduty"])
            .build()
        )
    """

    def __init__(self) -> None:
        """Initialize builder."""
        self._config = CheckpointConfig()
        self._actions: list[BaseAction | AsyncBaseAction] = []
        self._triggers: list[BaseTrigger] = []
        self._routes: list[Route] = []
        self._router_mode = RouteMode.ALL_MATCHES

    def name(self, name: str) -> "CheckpointBuilder":
        """Set checkpoint name."""
        self._config.name = name
        return self

    def description(self, description: str) -> "CheckpointBuilder":
        """Set checkpoint description."""
        self._config.description = description
        return self

    def source(self, source_id: str) -> "CheckpointBuilder":
        """Set source ID."""
        self._config.source_id = source_id
        return self

    def source_name(self, name: str) -> "CheckpointBuilder":
        """Set source name/path."""
        self._config.source_name = name
        return self

    def validators(self, validators: list[str]) -> "CheckpointBuilder":
        """Set validators to run."""
        self._config.validators = validators
        return self

    def validator_config(
        self, config: dict[str, dict[str, Any]]
    ) -> "CheckpointBuilder":
        """Set validator configuration."""
        self._config.validator_config = config
        return self

    def schema(self, path: str) -> "CheckpointBuilder":
        """Set schema path."""
        self._config.schema_path = path
        return self

    def auto_schema(self, enabled: bool = True) -> "CheckpointBuilder":
        """Enable/disable auto schema learning."""
        self._config.auto_schema = enabled
        return self

    def tags(self, tags: dict[str, str]) -> "CheckpointBuilder":
        """Set tags."""
        self._config.tags = tags
        return self

    def tag(self, key: str, value: str) -> "CheckpointBuilder":
        """Add a single tag."""
        self._config.tags[key] = value
        return self

    def timeout(self, seconds: int) -> "CheckpointBuilder":
        """Set timeout in seconds."""
        self._config.timeout_seconds = seconds
        return self

    def action(self, action: BaseAction | AsyncBaseAction) -> "CheckpointBuilder":
        """Add an action."""
        self._actions.append(action)
        return self

    def trigger(self, trigger: BaseTrigger) -> "CheckpointBuilder":
        """Add a trigger."""
        self._triggers.append(trigger)
        return self

    def route(self, route: Route) -> "CheckpointBuilder":
        """Add a route."""
        self._routes.append(route)
        return self

    def route_on_failure(self, actions: list[str]) -> "CheckpointBuilder":
        """Add a route that triggers on failure."""
        from truthound_dashboard.core.interfaces.routing import Jinja2Rule

        self._routes.append(Route(
            name="on_failure",
            rule=Jinja2Rule("failure", "failed"),
            actions=actions,
        ))
        return self

    def route_on_critical(self, actions: list[str]) -> "CheckpointBuilder":
        """Add a route that triggers on critical issues."""
        from truthound_dashboard.core.interfaces.routing import Jinja2Rule

        self._routes.append(Route(
            name="on_critical",
            rule=Jinja2Rule("critical", "has_critical"),
            actions=actions,
        ))
        return self

    def router_mode(self, mode: RouteMode) -> "CheckpointBuilder":
        """Set router mode."""
        self._router_mode = mode
        return self

    def build(self) -> Checkpoint:
        """Build the checkpoint.

        Returns:
            Configured Checkpoint instance.
        """
        router = None
        if self._routes:
            router = Router(mode=self._router_mode, routes=self._routes)

        return Checkpoint(
            config=self._config,
            actions=self._actions,
            triggers=self._triggers,
            router=router,
        )
