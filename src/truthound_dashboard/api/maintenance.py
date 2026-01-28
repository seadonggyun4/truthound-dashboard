"""Maintenance API endpoints.

This module provides endpoints for database maintenance, retention policies,
and cache management using truthound's store features.

Migrated features (using truthound):
- Retention policies (truthound.stores.retention)
- Caching (truthound.stores.caching)

Dashboard-specific features (not in truthound):
- SQLite VACUUM (SQLite-specific optimization)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from truthound_dashboard.core.maintenance import (
    MaintenanceConfig,
    get_maintenance_manager,
)
from truthound_dashboard.core.store_manager import (
    CacheType,
    DashboardStoreConfig,
    DashboardStoreManager,
    RetentionPolicySettings,
    get_store_manager,
)
from truthound_dashboard.core.scheduler import get_scheduler
from truthound_dashboard.schemas import (
    CacheClearRequest,
    CacheStatsResponse,
    CleanupResultItem,
    CleanupTriggerRequest,
    MaintenanceReportResponse,
    MaintenanceStatusResponse,
    RetentionPolicyConfig,
    RetentionPolicyResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Track last maintenance run (in production, this would be persisted)
_last_maintenance_run: datetime | None = None


@router.get(
    "/retention",
    response_model=RetentionPolicyResponse,
    summary="Get retention policy",
    description="Get current data retention policy configuration",
)
async def get_retention_policy() -> RetentionPolicyResponse:
    """Get current retention policy configuration.

    Returns:
        Current retention policy settings.
    """
    manager = get_maintenance_manager()
    config = manager.config

    return RetentionPolicyResponse(
        validation_retention_days=config.validation_retention_days,
        profile_keep_per_source=config.profile_keep_per_source,
        notification_log_retention_days=config.notification_log_retention_days,
        run_vacuum=config.run_vacuum,
        enabled=config.enabled,
    )


@router.put(
    "/retention",
    response_model=RetentionPolicyResponse,
    summary="Update retention policy",
    description="Update data retention policy configuration",
)
async def update_retention_policy(
    config: RetentionPolicyConfig,
) -> RetentionPolicyResponse:
    """Update retention policy configuration.

    Args:
        config: New retention policy settings.

    Returns:
        Updated retention policy.
    """
    manager = get_maintenance_manager()

    # Update configuration
    manager._config = MaintenanceConfig(
        validation_retention_days=config.validation_retention_days,
        profile_keep_per_source=config.profile_keep_per_source,
        notification_log_retention_days=config.notification_log_retention_days,
        run_vacuum=config.run_vacuum,
        enabled=config.enabled,
    )

    logger.info(
        f"Retention policy updated: "
        f"validation={config.validation_retention_days}d, "
        f"profiles={config.profile_keep_per_source}/source, "
        f"notifications={config.notification_log_retention_days}d"
    )

    return RetentionPolicyResponse(
        validation_retention_days=config.validation_retention_days,
        profile_keep_per_source=config.profile_keep_per_source,
        notification_log_retention_days=config.notification_log_retention_days,
        run_vacuum=config.run_vacuum,
        enabled=config.enabled,
    )


@router.get(
    "/status",
    response_model=MaintenanceStatusResponse,
    summary="Get maintenance status",
    description="Get maintenance system status and configuration",
)
async def get_maintenance_status() -> MaintenanceStatusResponse:
    """Get maintenance system status.

    Returns:
        Maintenance system status and available tasks.
    """
    manager = get_maintenance_manager()
    config = manager.config

    # Get available task names
    available_tasks = [strategy.name for strategy in manager._strategies]

    # Get next scheduled run from scheduler
    scheduler = get_scheduler()
    next_scheduled = scheduler.get_maintenance_next_run()

    return MaintenanceStatusResponse(
        enabled=config.enabled,
        last_run_at=_last_maintenance_run,
        next_scheduled_at=next_scheduled,
        config=RetentionPolicyConfig(
            validation_retention_days=config.validation_retention_days,
            profile_keep_per_source=config.profile_keep_per_source,
            notification_log_retention_days=config.notification_log_retention_days,
            run_vacuum=config.run_vacuum,
            enabled=config.enabled,
        ),
        available_tasks=available_tasks,
    )


@router.post(
    "/cleanup",
    response_model=MaintenanceReportResponse,
    summary="Trigger cleanup",
    description="Manually trigger database cleanup using truthound retention policies",
)
async def trigger_cleanup(
    request: CleanupTriggerRequest,
) -> MaintenanceReportResponse:
    """Manually trigger database cleanup.

    This endpoint now uses truthound's retention system for cleanup
    while maintaining backward compatibility with the existing API.

    Args:
        request: Cleanup options.

    Returns:
        Cleanup results report.
    """
    global _last_maintenance_run

    manager = get_maintenance_manager()

    if request.tasks:
        # Run specific tasks (legacy behavior)
        started_at = datetime.utcnow()
        results = []

        for task_name in request.tasks:
            result = await manager.run_task(task_name)
            if result:
                results.append(
                    CleanupResultItem(
                        task_name=result.task_name,
                        records_deleted=result.records_deleted,
                        duration_ms=result.duration_ms,
                        success=result.success,
                        error=result.error,
                    )
                )
            else:
                results.append(
                    CleanupResultItem(
                        task_name=task_name,
                        records_deleted=0,
                        duration_ms=0,
                        success=False,
                        error=f"Task not found: {task_name}",
                    )
                )

        # Run vacuum if requested (SQLite-specific, not in truthound)
        vacuum_performed = False
        vacuum_error = None
        if request.run_vacuum:
            try:
                await manager.vacuum()
                vacuum_performed = True
            except Exception as e:
                vacuum_error = str(e)
                logger.error(f"VACUUM failed: {e}")

        completed_at = datetime.utcnow()
        _last_maintenance_run = completed_at

        return MaintenanceReportResponse(
            started_at=started_at,
            completed_at=completed_at,
            results=results,
            total_deleted=sum(r.records_deleted for r in results),
            total_duration_ms=int(
                (completed_at - started_at).total_seconds() * 1000
            ),
            vacuum_performed=vacuum_performed,
            vacuum_error=vacuum_error,
            success=all(r.success for r in results) and vacuum_error is None,
        )
    else:
        # Run all cleanup tasks
        # Temporarily override vacuum setting
        original_vacuum = manager.config.run_vacuum
        manager._config.run_vacuum = request.run_vacuum

        try:
            report = await manager.run_cleanup()
        finally:
            manager._config.run_vacuum = original_vacuum

        _last_maintenance_run = report.completed_at

        return MaintenanceReportResponse(
            started_at=report.started_at,
            completed_at=report.completed_at,
            results=[
                CleanupResultItem(
                    task_name=r.task_name,
                    records_deleted=r.records_deleted,
                    duration_ms=r.duration_ms,
                    success=r.success,
                    error=r.error,
                )
                for r in report.results
            ],
            total_deleted=report.total_deleted,
            total_duration_ms=report.total_duration_ms,
            vacuum_performed=report.vacuum_performed,
            vacuum_error=report.vacuum_error,
            success=report.success,
        )


@router.post(
    "/vacuum",
    response_model=MaintenanceReportResponse,
    summary="Run database vacuum",
    description="Run SQLite VACUUM to reclaim disk space (SQLite-specific, not part of truthound)",
)
async def run_vacuum() -> MaintenanceReportResponse:
    """Run SQLite VACUUM to reclaim disk space.

    Note: This is a dashboard-specific operation for SQLite.
    truthound's store system is backend-agnostic and doesn't include VACUUM.

    Returns:
        Vacuum operation result.
    """
    manager = get_maintenance_manager()

    started_at = datetime.utcnow()
    vacuum_error = None

    try:
        await manager.vacuum()
        vacuum_performed = True
    except Exception as e:
        vacuum_error = str(e)
        vacuum_performed = False
        logger.error(f"VACUUM failed: {e}")

    completed_at = datetime.utcnow()

    return MaintenanceReportResponse(
        started_at=started_at,
        completed_at=completed_at,
        results=[],
        total_deleted=0,
        total_duration_ms=int((completed_at - started_at).total_seconds() * 1000),
        vacuum_performed=vacuum_performed,
        vacuum_error=vacuum_error,
        success=vacuum_error is None,
    )


@router.get(
    "/cache/stats",
    response_model=CacheStatsResponse,
    summary="Get cache statistics",
    description="Get current cache usage statistics from truthound's caching system",
)
async def get_cache_stats() -> CacheStatsResponse:
    """Get cache statistics using truthound's cache metrics.

    Returns:
        Cache usage statistics.
    """
    try:
        store_manager = get_store_manager()
        if not store_manager._initialized:
            store_manager.initialize()

        stats = store_manager.get_cache_stats()

        return CacheStatsResponse(
            total_entries=stats.get("total_entries", 0),
            expired_entries=stats.get("expired_entries", 0),
            valid_entries=stats.get("valid_entries", 0),
            max_size=stats.get("max_size", 0),
            hit_rate=stats.get("hit_rate"),
        )
    except Exception as e:
        logger.warning(f"Failed to get cache stats from store manager: {e}")
        # Fallback to legacy cache
        from truthound_dashboard.core.cache import get_cache

        cache = get_cache()
        stats = await cache.get_stats()

        return CacheStatsResponse(
            total_entries=stats.get("total_entries", 0),
            expired_entries=stats.get("expired_entries", 0),
            valid_entries=stats.get("valid_entries", 0),
            max_size=stats.get("max_size", 0),
            hit_rate=stats.get("hit_rate"),
        )


@router.post(
    "/cache/clear",
    response_model=CacheStatsResponse,
    summary="Clear cache",
    description="Clear cached data using truthound's caching system",
)
async def clear_cache(request: CacheClearRequest) -> CacheStatsResponse:
    """Clear cache data.

    Args:
        request: Cache clear options.

    Returns:
        Updated cache statistics.
    """
    try:
        store_manager = get_store_manager()
        if not store_manager._initialized:
            store_manager.initialize()

        store_manager.clear_cache(pattern=request.pattern)
        stats = store_manager.get_cache_stats()

        return CacheStatsResponse(
            total_entries=stats.get("total_entries", 0),
            expired_entries=stats.get("expired_entries", 0),
            valid_entries=stats.get("valid_entries", 0),
            max_size=stats.get("max_size", 0),
            hit_rate=stats.get("hit_rate"),
        )
    except Exception as e:
        logger.warning(f"Failed to clear cache from store manager: {e}")
        # Fallback to legacy cache
        from truthound_dashboard.core.cache import get_cache, get_cache_manager

        if request.namespace:
            manager = get_cache_manager()
            cache = manager.get(request.namespace)
            if cache:
                if request.pattern:
                    await cache.invalidate_pattern(request.pattern)
                else:
                    await cache.clear()
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Cache namespace not found: {request.namespace}",
                )
        else:
            cache = get_cache()
            if request.pattern:
                await cache.invalidate_pattern(request.pattern)
            else:
                await cache.clear()

        cache = get_cache()
        stats = await cache.get_stats()

        return CacheStatsResponse(
            total_entries=stats.get("total_entries", 0),
            expired_entries=stats.get("expired_entries", 0),
            valid_entries=stats.get("valid_entries", 0),
            max_size=stats.get("max_size", 0),
            hit_rate=None,
        )
