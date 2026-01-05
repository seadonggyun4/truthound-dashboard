"""API router configuration.

This module configures the main API router and includes all sub-routers.
"""

from fastapi import APIRouter

from . import (
    drift,
    health,
    history,
    notifications,
    profile,
    rules,
    schedules,
    schemas,
    sources,
    validations,
)

api_router = APIRouter()

# Health endpoints (no prefix)
api_router.include_router(
    health.router,
    tags=["health"],
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

# Profiling endpoints
api_router.include_router(
    profile.router,
    tags=["profiling"],
)

# History endpoints (Phase 2)
api_router.include_router(
    history.router,
    tags=["history"],
)

# Drift detection endpoints (Phase 2)
api_router.include_router(
    drift.router,
    tags=["drift"],
)

# Schedule management endpoints (Phase 2)
api_router.include_router(
    schedules.router,
    tags=["schedules"],
)

# Notification management endpoints (Phase 3)
api_router.include_router(
    notifications.router,
    tags=["notifications"],
)
