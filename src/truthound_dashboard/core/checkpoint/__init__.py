"""Checkpoint implementation for validation pipeline orchestration.

A Checkpoint represents a complete data validation pipeline that combines:
- Data source configuration
- Validator configuration
- Action orchestration (notifications, storage)
- Trigger management (scheduling)
- Result routing (conditional action execution)

This module provides the concrete Checkpoint implementation that
integrates with the TruthoundBackend for validation operations.

Usage:
    from truthound_dashboard.core.checkpoint import Checkpoint, CheckpointRunner

    # Create a checkpoint
    checkpoint = Checkpoint(
        config=CheckpointConfig(
            name="daily_orders",
            source_id="orders_db",
            validators=["null", "uniqueness"],
        ),
        actions=[
            SlackNotificationAction(webhook_url="..."),
            FileStorageAction(base_path="./results"),
        ],
    )

    # Add routing rules
    checkpoint.set_router(
        Router(routes=[
            Route(
                name="critical_alert",
                rule=Jinja2Rule("critical", "has_critical"),
                actions=["slack", "pagerduty"],
            ),
        ])
    )

    # Run the checkpoint
    result = await checkpoint.run()

    # Or use the runner for multiple checkpoints
    runner = CheckpointRunner()
    runner.register(checkpoint)
    result = await runner.run("daily_orders")
"""

from truthound_dashboard.core.checkpoint.checkpoint import (
    Checkpoint,
    CheckpointBuilder,
)
from truthound_dashboard.core.checkpoint.runner import (
    CheckpointRunner,
    get_checkpoint_runner,
)
from truthound_dashboard.core.checkpoint.adapters import (
    TruthoundCheckpointAdapter,
    TruthoundActionAdapter,
    create_checkpoint_from_truthound,
    create_truthound_checkpoint,
    create_checkpoint_from_config,
    wrap_truthound_action,
    get_ci_reporter_for_checkpoint,
    report_checkpoint_to_ci,
    is_truthound_checkpoint_available,
)

__all__ = [
    # Core checkpoint classes
    "Checkpoint",
    "CheckpointBuilder",
    "CheckpointRunner",
    "get_checkpoint_runner",
    # Truthound adapters
    "TruthoundCheckpointAdapter",
    "TruthoundActionAdapter",
    # Factory functions
    "create_checkpoint_from_truthound",
    "create_truthound_checkpoint",
    "create_checkpoint_from_config",
    "wrap_truthound_action",
    # CI/CD helpers
    "get_ci_reporter_for_checkpoint",
    "report_checkpoint_to_ci",
    "is_truthound_checkpoint_available",
]
