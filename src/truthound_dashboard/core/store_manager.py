"""Unified store management using truthound's store backends.

This module provides a unified interface for validation result storage
using truthound's enterprise store features:
- Retention policies (truthound.stores.retention)
- Caching (truthound.stores.caching)
- Versioning (truthound.stores.versioning)
- Storage tiering (truthound.stores.tiering)
- Observability (truthound.stores.observability)

Note: SQLite VACUUM is dashboard-specific and not part of truthound.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from truthound.stores import get_store
from truthound.stores.retention import (
    CompositePolicy,
    CountBasedPolicy,
    RetentionConfig,
    RetentionResult,
    RetentionSchedule,
    RetentionStore,
    SizeBasedPolicy,
    StatusBasedPolicy,
    TagBasedPolicy,
    TimeBasedPolicy,
)
from truthound.stores.caching import (
    CachedStore,
    CacheConfig,
    CacheMode,
    EvictionPolicy,
    LFUCache,
    LRUCache,
    TTLCache,
)
from truthound.stores.versioning import (
    VersionedStore,
    VersionDiff,
    VersionInfo,
    VersioningConfig,
)
from truthound.stores.tiering import (
    AccessBasedTierPolicy,
    AgeBasedTierPolicy,
    CompositeTierPolicy,
    MigrationDirection,
    SizeBasedTierPolicy,
    StorageTier,
    TieredStore,
    TieringConfig,
    TieringResult,
    TierType,
)
from truthound.stores.observability import ObservableStore
from truthound.stores.observability import (
    AuditConfig,
    AuditEvent,
    AuditEventType,
    AuditLogger,
    InMemoryAuditBackend,
    InMemoryMetricsBackend,
    JsonAuditBackend,
    MetricsConfig,
    MetricsRegistry,
    ObservabilityConfig,
    StoreMetrics,
    TracingConfig,
)


# Local definitions for types not exported by truthound
class PolicyMode(str, Enum):
    """Mode for composite retention policies."""

    ALL = "all"  # All policies must match
    ANY = "any"  # Any policy can match


class RetentionAction(str, Enum):
    """Action to take when retention policy matches."""

    DELETE = "delete"
    ARCHIVE = "archive"
    MOVE = "move"


class VersioningMode(str, Enum):
    """Mode for versioning strategy."""

    SEMANTIC = "semantic"
    INCREMENTAL = "incremental"
    TIMESTAMP = "timestamp"
    GIT_LIKE = "git_like"


class AuditStatus(str, Enum):
    """Status of audit events."""

    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"


class DataRedactor:
    """Simple data redactor for audit logs."""

    def __init__(self, fields_to_redact: list[str] | None = None):
        self.fields_to_redact = fields_to_redact or []

    def redact(self, data: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive fields from data."""
        result = dict(data)
        for field in self.fields_to_redact:
            if field in result:
                result[field] = "[REDACTED]"
        return result

from truthound_dashboard.config import get_settings

logger = logging.getLogger(__name__)


class CacheType(str, Enum):
    """Cache eviction policy types."""
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"


@dataclass
class DashboardStoreConfig:
    """Configuration for the dashboard store system.

    Attributes:
        base_path: Base path for file storage.
        enable_caching: Enable caching layer.
        cache_type: Type of cache (LRU, LFU, TTL).
        cache_max_size: Maximum cache entries.
        cache_ttl_seconds: TTL for cache entries.
        enable_versioning: Enable result versioning.
        max_versions: Maximum versions to keep per item.
        enable_tiering: Enable storage tiering.
        enable_observability: Enable audit/metrics/tracing.
        audit_log_path: Path for audit logs.
    """
    base_path: Path = field(default_factory=lambda: Path(".truthound/store"))

    # Caching
    enable_caching: bool = True
    cache_type: CacheType = CacheType.LFU
    cache_max_size: int = 1000
    cache_ttl_seconds: int = 3600

    # Versioning
    enable_versioning: bool = True
    max_versions: int = 10

    # Tiering
    enable_tiering: bool = False
    hot_retention_days: int = 7
    warm_retention_days: int = 30
    cold_retention_days: int = 90

    # Observability
    enable_observability: bool = True
    enable_audit: bool = True
    enable_metrics: bool = True
    enable_tracing: bool = False
    audit_log_path: Path = field(default_factory=lambda: Path(".truthound/audit"))


@dataclass
class RetentionPolicySettings:
    """Retention policy settings using truthound policies.

    Attributes:
        validation_retention_days: Days to keep validations.
        profile_keep_per_source: Profiles to keep per source.
        notification_log_retention_days: Days to keep notification logs.
        max_storage_mb: Maximum storage in MB (optional).
        keep_failed_longer: Keep failed validations longer.
        failed_retention_days: Days to keep failed validations.
        protected_tags: Tags to never delete.
        delete_tags: Tags to delete after retention.
    """
    validation_retention_days: int = 90
    profile_keep_per_source: int = 5
    notification_log_retention_days: int = 30
    max_storage_mb: int | None = None
    keep_failed_longer: bool = True
    failed_retention_days: int = 180
    protected_tags: list[str] = field(default_factory=list)
    delete_tags: list[str] = field(default_factory=list)

    def to_truthound_config(self) -> RetentionConfig:
        """Convert to truthound RetentionConfig."""
        policies = []

        # Time-based policy for validations
        policies.append(TimeBasedPolicy(max_age_days=self.validation_retention_days))

        # Status-based policy for failed validations
        if self.keep_failed_longer:
            policies.append(
                StatusBasedPolicy(
                    status="failure",
                    max_age_days=self.failed_retention_days,
                    retain=True,
                )
            )

        # Size-based policy if configured
        if self.max_storage_mb:
            policies.append(SizeBasedPolicy(max_size_mb=self.max_storage_mb))

        # Tag-based policies
        if self.protected_tags:
            policies.append(
                TagBasedPolicy(
                    required_tags={tag: "*" for tag in self.protected_tags},
                    action=RetentionAction.ARCHIVE,
                )
            )

        if self.delete_tags:
            policies.append(
                TagBasedPolicy(
                    delete_tags={tag: "*" for tag in self.delete_tags},
                    action=RetentionAction.DELETE,
                )
            )

        return RetentionConfig(
            policies=policies,
            mode=PolicyMode.ANY,
            default_action=RetentionAction.DELETE,
            schedule=RetentionSchedule(
                enabled=True,
                interval_hours=24,
                batch_size=1000,
            ),
        )


class DashboardStoreManager:
    """Manager for truthound-based store with all enterprise features.

    This manager wraps truthound's store system to provide:
    - Caching with LRU/LFU/TTL eviction
    - Versioning with diff and rollback
    - Storage tiering (hot/warm/cold)
    - Observability (audit, metrics, tracing)
    - Retention policies

    Example:
        manager = DashboardStoreManager()
        manager.initialize()

        # Save with versioning
        run_id = manager.save(result, message="Initial validation")

        # Get version history
        history = manager.get_version_history(run_id)

        # Run retention cleanup
        cleanup_result = manager.run_retention_cleanup()
    """

    def __init__(self, config: DashboardStoreConfig | None = None) -> None:
        """Initialize store manager.

        Args:
            config: Store configuration. Uses defaults if not provided.
        """
        self._config = config or DashboardStoreConfig()
        self._store = None
        self._base_store = None
        self._versioned_store = None
        self._cached_store = None
        self._tiered_store = None
        self._observable_store = None
        self._retention_store = None
        self._audit_logger = None
        self._metrics = None
        self._cache = None
        self._initialized = False

    @property
    def config(self) -> DashboardStoreConfig:
        """Get store configuration."""
        return self._config

    def initialize(self) -> None:
        """Initialize store with all configured layers."""
        if self._initialized:
            return

        logger.info("Initializing dashboard store manager...")

        # Base store (filesystem)
        self._base_store = get_store(
            "filesystem",
            base_path=str(self._config.base_path),
        )

        current_store = self._base_store

        # Layer 1: Versioning
        if self._config.enable_versioning:
            versioning_config = VersioningConfig(
                mode=VersioningMode.INCREMENTAL,
                max_versions=self._config.max_versions,
                auto_cleanup=True,
                track_changes=True,
            )
            self._versioned_store = VersionedStore(current_store, versioning_config)
            current_store = self._versioned_store
            logger.info(f"Versioning enabled (max {self._config.max_versions} versions)")

        # Layer 2: Caching
        if self._config.enable_caching:
            cache_config = CacheConfig(
                max_size=self._config.cache_max_size,
                ttl_seconds=self._config.cache_ttl_seconds,
                enable_statistics=True,
            )

            if self._config.cache_type == CacheType.LRU:
                self._cache = LRUCache(
                    max_size=self._config.cache_max_size,
                    ttl_seconds=self._config.cache_ttl_seconds,
                    config=cache_config,
                )
            elif self._config.cache_type == CacheType.LFU:
                self._cache = LFUCache(
                    max_size=self._config.cache_max_size,
                    ttl_seconds=self._config.cache_ttl_seconds,
                    config=cache_config,
                )
            else:
                self._cache = TTLCache(
                    ttl_seconds=self._config.cache_ttl_seconds,
                    max_size=self._config.cache_max_size,
                )

            self._cached_store = CachedStore(
                current_store,
                self._cache,
                mode=CacheMode.WRITE_THROUGH,
            )
            current_store = self._cached_store
            logger.info(f"Caching enabled ({self._config.cache_type.value})")

        # Layer 3: Tiering
        if self._config.enable_tiering:
            self._setup_tiering(current_store)
            if self._tiered_store:
                current_store = self._tiered_store
                logger.info("Storage tiering enabled")

        # Layer 4: Observability
        if self._config.enable_observability:
            self._setup_observability(current_store)
            if self._observable_store:
                current_store = self._observable_store
                logger.info("Observability enabled")

        self._store = current_store
        self._initialized = True
        logger.info("Dashboard store manager initialized")

    def _setup_tiering(self, base_store) -> None:
        """Set up storage tiering."""
        # Create tier stores
        hot_store = get_store(
            "filesystem",
            base_path=str(self._config.base_path / "hot"),
        )
        warm_store = get_store(
            "filesystem",
            base_path=str(self._config.base_path / "warm"),
        )
        cold_store = get_store(
            "filesystem",
            base_path=str(self._config.base_path / "cold"),
        )

        tiers = [
            StorageTier(
                name="hot",
                store=hot_store,
                tier_type=TierType.HOT,
                priority=1,
            ),
            StorageTier(
                name="warm",
                store=warm_store,
                tier_type=TierType.WARM,
                priority=2,
            ),
            StorageTier(
                name="cold",
                store=cold_store,
                tier_type=TierType.COLD,
                priority=3,
            ),
        ]

        # Age-based tier policies
        policies = [
            AgeBasedTierPolicy(
                from_tier="hot",
                to_tier="warm",
                after_days=self._config.hot_retention_days,
            ),
            AgeBasedTierPolicy(
                from_tier="warm",
                to_tier="cold",
                after_days=self._config.warm_retention_days,
            ),
        ]

        tiering_config = TieringConfig(
            policies=policies,
            default_tier="hot",
            check_interval_hours=24,
            batch_size=100,
        )

        self._tiered_store = TieredStore(tiers, tiering_config)

    def _setup_observability(self, base_store) -> None:
        """Set up observability (audit, metrics, tracing)."""
        # Audit backend
        audit_backend = None
        if self._config.enable_audit:
            self._config.audit_log_path.mkdir(parents=True, exist_ok=True)
            audit_config = AuditConfig(
                enabled=True,
                file_path=str(self._config.audit_log_path / "dashboard_audit.jsonl"),
                redact_sensitive=True,
                sensitive_fields=["password", "api_key", "token"],
            )
            audit_backend = JsonAuditBackend(
                config=audit_config,
                file_path=self._config.audit_log_path / "dashboard_audit.jsonl",
            )
            self._audit_logger = AuditLogger(
                backend=audit_backend,
                store_type="dashboard",
                store_id="validation_store",
            )

        # Metrics backend
        metrics_backend = None
        if self._config.enable_metrics:
            metrics_backend = InMemoryMetricsBackend()
            self._metrics = StoreMetrics(
                backend=metrics_backend,
                store_type="dashboard",
                store_id="validation_store",
            )

        obs_config = ObservabilityConfig(
            audit=AuditConfig(enabled=self._config.enable_audit),
            metrics=MetricsConfig(enabled=self._config.enable_metrics),
            tracing=TracingConfig(enabled=self._config.enable_tracing),
        )

        self._observable_store = ObservableStore(base_store, obs_config)

    # ----- Retention Operations -----

    def create_retention_store(
        self,
        settings: RetentionPolicySettings,
    ) -> RetentionStore:
        """Create a retention store with the given settings.

        Args:
            settings: Retention policy settings.

        Returns:
            Configured RetentionStore.
        """
        if not self._store:
            self.initialize()

        config = settings.to_truthound_config()
        return RetentionStore(self._store, config)

    async def run_retention_cleanup(
        self,
        settings: RetentionPolicySettings,
        dry_run: bool = False,
    ) -> RetentionResult:
        """Run retention cleanup with truthound's retention system.

        Args:
            settings: Retention policy settings.
            dry_run: If True, don't actually delete items.

        Returns:
            RetentionResult with cleanup details.
        """
        if not self._store:
            self.initialize()

        config = settings.to_truthound_config()
        config.dry_run = dry_run

        retention_store = RetentionStore(self._store, config)
        result = await retention_store.apply_retention()

        logger.info(
            f"Retention cleanup: scanned={result.items_scanned}, "
            f"deleted={result.items_deleted}, freed={result.bytes_freed} bytes"
        )

        return result

    # ----- Cache Operations -----

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics from truthound's cache.

        Returns:
            Cache statistics dictionary.
        """
        if not self._cache:
            return {
                "total_entries": 0,
                "expired_entries": 0,
                "valid_entries": 0,
                "max_size": 0,
                "hits": 0,
                "misses": 0,
                "hit_rate": 0.0,
            }

        metrics = self._cache.metrics
        return {
            "total_entries": metrics.size,
            "expired_entries": metrics.expirations,
            "valid_entries": metrics.size,
            "max_size": self._config.cache_max_size,
            "hits": metrics.hits,
            "misses": metrics.misses,
            "hit_rate": metrics.hit_rate,
            "evictions": metrics.evictions,
            "average_get_time_ms": metrics.average_get_time_ms,
            "average_set_time_ms": metrics.average_set_time_ms,
        }

    def clear_cache(self, pattern: str | None = None) -> None:
        """Clear cache entries.

        Args:
            pattern: Optional pattern to match keys (prefix match).
        """
        if not self._cache:
            return

        if pattern:
            self._cache.delete_many([
                key for key in self._cache._cache.keys()
                if key.startswith(pattern)
            ])
        else:
            self._cache.clear()

    # ----- Versioning Operations -----

    def get_version_history(
        self,
        item_id: str,
        limit: int | None = None,
    ) -> list[VersionInfo]:
        """Get version history for an item.

        Args:
            item_id: Item identifier.
            limit: Maximum versions to return.

        Returns:
            List of VersionInfo objects.
        """
        if not self._versioned_store:
            return []

        return self._versioned_store.get_version_history(item_id, limit=limit)

    def get_version_diff(
        self,
        item_id: str,
        version_a: int,
        version_b: int | None = None,
    ) -> VersionDiff:
        """Get diff between versions.

        Args:
            item_id: Item identifier.
            version_a: First version.
            version_b: Second version (latest if None).

        Returns:
            VersionDiff with changes.
        """
        if not self._versioned_store:
            raise ValueError("Versioning not enabled")

        return self._versioned_store.diff(item_id, version_a, version_b)

    def rollback_version(
        self,
        item_id: str,
        version: int,
        message: str | None = None,
    ) -> Any:
        """Rollback to a previous version.

        Args:
            item_id: Item identifier.
            version: Version to rollback to.
            message: Optional rollback message.

        Returns:
            Rolled back item.
        """
        if not self._versioned_store:
            raise ValueError("Versioning not enabled")

        return self._versioned_store.rollback(item_id, version, message=message)

    # ----- Tiering Operations -----

    async def run_tiering(self, dry_run: bool = False) -> TieringResult | None:
        """Run storage tiering migration.

        Args:
            dry_run: If True, don't actually migrate items.

        Returns:
            TieringResult or None if tiering not enabled.
        """
        if not self._tiered_store:
            return None

        result = await self._tiered_store.run_migration(dry_run=dry_run)

        logger.info(
            f"Tiering migration: scanned={result.items_scanned}, "
            f"migrated={result.items_migrated}, bytes={result.bytes_migrated}"
        )

        return result

    def get_tier_stats(self) -> dict[str, Any]:
        """Get storage tier statistics.

        Returns:
            Tier statistics dictionary.
        """
        if not self._tiered_store:
            return {}

        return {
            tier.name: {
                "type": tier.tier_type.value,
                "priority": tier.priority,
                "item_count": len(list(tier.store.list_ids())),
            }
            for tier in self._tiered_store._tiers
        }

    # ----- Observability Operations -----

    def get_audit_events(
        self,
        event_type: AuditEventType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Query audit events.

        Args:
            event_type: Filter by event type.
            start_time: Filter events after this time.
            end_time: Filter events before this time.
            limit: Maximum events to return.

        Returns:
            List of AuditEvent objects.
        """
        if not self._audit_logger:
            return []

        return self._audit_logger.backend.query(
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    def get_store_metrics(self) -> dict[str, Any]:
        """Get store metrics.

        Returns:
            Store metrics dictionary.
        """
        if not self._metrics:
            return {}

        try:
            backend = self._metrics.backend
            if hasattr(backend, 'get_metrics'):
                return backend.get_metrics()
            # InMemoryMetricsBackend doesn't have get_metrics, return empty
            return {}
        except Exception:
            return {}

    # ----- Standard Store Operations -----

    def save(self, result: Any, **kwargs) -> str:
        """Save a validation result.

        Args:
            result: Validation result to save.
            **kwargs: Additional arguments (message, created_by, etc.)

        Returns:
            Run ID.
        """
        if not self._store:
            self.initialize()

        return self._store.save(result, **kwargs)

    def get(self, item_id: str, version: int | None = None) -> Any:
        """Get a validation result.

        Args:
            item_id: Item identifier.
            version: Optional version (if versioning enabled).

        Returns:
            Validation result.
        """
        if not self._store:
            self.initialize()

        if version and self._versioned_store:
            return self._versioned_store.get(item_id, version=version)

        return self._store.get(item_id)

    def delete(self, item_id: str) -> bool:
        """Delete a validation result.

        Args:
            item_id: Item identifier.

        Returns:
            True if deleted.
        """
        if not self._store:
            self.initialize()

        return self._store.delete(item_id)

    def close(self) -> None:
        """Close all store connections."""
        if self._store:
            self._store.close()
        self._initialized = False


# Singleton instance
_store_manager: DashboardStoreManager | None = None


def get_store_manager() -> DashboardStoreManager:
    """Get store manager singleton.

    Returns:
        DashboardStoreManager instance.
    """
    global _store_manager
    if _store_manager is None:
        _store_manager = DashboardStoreManager()
    return _store_manager


def reset_store_manager() -> None:
    """Reset store manager singleton (for testing)."""
    global _store_manager
    if _store_manager:
        _store_manager.close()
    _store_manager = None
