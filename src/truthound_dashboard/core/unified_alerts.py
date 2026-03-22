"""Queue-aware unified alert service."""

from __future__ import annotations

from truthound_dashboard.core.incidents import IncidentService


class UnifiedAlertsService(IncidentService):
    """Compatibility wrapper retaining the historical service name."""

