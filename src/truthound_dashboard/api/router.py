"""API router configuration.

This module configures the main API router and includes all sub-routers.
"""

from fastapi import APIRouter

from . import (
    alerts,
    anomaly,
    control_plane,
    drift,
    enterprise_sampling,
    health,
    history,
    lineage,
    mask,
    notifications,
    notifications_advanced,
    observability,
    plugins,
    profile,
    reports,
    rule_suggestions,
    rules,
    scan,
    schedules,
    schema_evolution,
    schemas,
    sources,
    tiering,
    triggers,
    validations,
    validators,
    versioning,
    websocket,
)

api_router = APIRouter()

# Health endpoints (no prefix)
api_router.include_router(
    health.router,
    tags=["health"],
)

api_router.include_router(
    control_plane.router,
    tags=["control-plane"],
)

# Source management
api_router.include_router(
    sources.router,
    prefix="/sources",
    tags=["sources"],
)

# Schema management
api_router.include_router(
    schemas.router,
    tags=["schemas"],
)

# Rules management
api_router.include_router(
    rules.router,
    tags=["rules"],
)

# Validation endpoints
api_router.include_router(
    validations.router,
    prefix="/validations",
    tags=["validations"],
)

# Validator registry endpoints
api_router.include_router(
    validators.router,
    tags=["validators"],
)

# Profiling endpoints
api_router.include_router(
    profile.router,
    tags=["profiling"],
)

api_router.include_router(
    history.router,
    tags=["history"],
)

api_router.include_router(
    drift.router,
    tags=["drift"],
)

# PII scan endpoints
api_router.include_router(
    scan.router,
    prefix="/scans",
    tags=["pii-scan"],
)

# Data masking endpoints
api_router.include_router(
    mask.router,
    tags=["masks"],
)

api_router.include_router(
    schedules.router,
    tags=["schedules"],
)

api_router.include_router(
    notifications.router,
    tags=["notifications"],
)

# Report generation endpoints
api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["reports"],
)

# Versioning endpoints
api_router.include_router(
    versioning.router,
    tags=["versioning"],
)

api_router.include_router(
    schema_evolution.router,
    tags=["schema-evolution"],
)

api_router.include_router(
    rule_suggestions.router,
    tags=["rule-suggestions"],
)

api_router.include_router(
    rule_suggestions.presets_router,
    tags=["rule-suggestions"],
)
api_router.include_router(
    notifications_advanced.router,
    tags=["notifications-advanced"],
)
api_router.include_router(
    lineage.router,
    prefix="/lineage",
    tags=["lineage"],
)

api_router.include_router(
    anomaly.router,
    tags=["anomaly"],
)
api_router.include_router(
    alerts.router,
    tags=["alerts"],
)
api_router.include_router(
    triggers.router,
    tags=["triggers"],
)
api_router.include_router(
    websocket.router,
    tags=["websocket"],
)
api_router.include_router(
    plugins.router,
    tags=["plugins"],
)
api_router.include_router(
    tiering.router,
    tags=["tiering"],
)
api_router.include_router(
    enterprise_sampling.router,
    tags=["enterprise-sampling"],
)
api_router.include_router(
    observability.router,
    prefix="/observability",
    tags=["observability"],
)
