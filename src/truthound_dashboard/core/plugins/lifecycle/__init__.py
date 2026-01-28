"""Plugin Lifecycle Management.

This module provides:
- State machine for plugin lifecycle
- Graceful shutdown and rollback
"""

from __future__ import annotations

from .states import (
    PluginState,
    StateTransition,
    StateTransitionError,
)
from .machine import (
    PluginStateMachine,
    create_state_machine,
)

__all__ = [
    # States
    "PluginState",
    "StateTransition",
    "StateTransitionError",
    # Machine
    "PluginStateMachine",
    "create_state_machine",
]
