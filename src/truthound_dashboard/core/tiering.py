"""Storage Tiering Service.

This module provides storage tiering functionality using truthound's
storage tiering module (truthound.stores.tiering).

Architecture:
    API Endpoints
         ↓
    TieringService
         ↓
    TieringAdapter
         ↓
    truthound.stores.tiering
        - TierType
        - StorageTier
        - TieringConfig
        - TierPolicy classes
        - TierMetadataStore
        - TieringResult

Features:
    - Storage tier management (hot, warm, cold, archive)
    - Policy-based migration (age, access, size, scheduled, composite, custom)
    - Migration execution with truthound backends
    - Access tracking for intelligent tiering
    - Background policy evaluation and execution
    - Migration history and statistics
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import partial
from typing import Any, Protocol, runtime_checkable
from uuid import uuid4

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

# Thread pool for blocking truthound operations
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="tiering")


def _generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid4())


# =============================================================================
# Protocols for type checking
# =============================================================================


@runtime_checkable
class TruthoundStore(Protocol):
    """Protocol for truthound store backends."""

    def save(self, item_id: str, data: Any) -> str: ...
    def get(self, item_id: str) -> Any: ...
    def delete(self, item_id: str) -> bool: ...
    def list(self) -> list[str]: ...


@runtime_checkable
class TruthoundTierPolicy(Protocol):
    """Protocol for truthound tier policies."""

    @property
    def from_tier(self) -> str: ...

    @property
    def to_tier(self) -> str: ...

    def should_migrate(self, info: Any) -> bool: ...


# =============================================================================
# Result dataclasses
# =============================================================================


@dataclass
class MigrationItem:
    """Represents an item to be migrated."""

    item_id: str
    from_tier: str
    to_tier: str
    size_bytes: int = 0
    policy_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MigrationResult:
    """Result of a single migration operation."""

    item_id: str
    from_tier: str
    to_tier: str
    success: bool
    size_bytes: int = 0
    error_message: str | None = None
    duration_ms: float = 0.0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


@dataclass
class TieringExecutionResult:
    """Result of a tiering execution run."""

    start_time: datetime
    end_time: datetime
    items_scanned: int = 0
    items_migrated: int = 0
    items_failed: int = 0
    bytes_migrated: int = 0
    migrations: list[MigrationResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    dry_run: bool = False

    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()

    @property
    def success_rate(self) -> float:
        """Calculate migration success rate."""
        total = self.items_migrated + self.items_failed
        return self.items_migrated / total if total > 0 else 1.0


@dataclass
class TierInfo:
    """Metadata about an item's tier placement."""

    item_id: str
    tier_name: str
    created_at: datetime
    migrated_at: datetime | None = None
    access_count: int = 0
    last_accessed: datetime | None = None
    size_bytes: int = 0
    next_migration: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Tiering Adapter - truthound integration layer
# =============================================================================


class TieringAdapter:
    """Adapter for truthound storage tiering functionality.

    This adapter provides a clean interface between the dashboard and
    truthound's tiering module, handling:
    - Store backend creation
    - Policy object creation
    - Migration execution
    - Metadata tracking

    The adapter gracefully handles cases where truthound is unavailable
    or lacks certain features.
    """

    _truthound_available: bool | None = None
    _tiering_available: bool | None = None

    def __init__(self) -> None:
        """Initialize adapter."""
        self._stores: dict[str, Any] = {}
        self._metadata_store: Any = None
        self._check_availability()

    def _check_availability(self) -> None:
        """Check truthound tiering availability."""
        if TieringAdapter._truthound_available is None:
            try:
                import truthound
                TieringAdapter._truthound_available = True
            except ImportError:
                TieringAdapter._truthound_available = False
                logger.warning("truthound not available, using fallback implementation")

        if TieringAdapter._tiering_available is None and TieringAdapter._truthound_available:
            try:
                from truthound.stores.tiering.base import TierType, StorageTier, TieringConfig
                from truthound.stores.tiering.policies import AgeBasedTierPolicy
                TieringAdapter._tiering_available = True
            except ImportError:
                TieringAdapter._tiering_available = False
                logger.warning("truthound.stores.tiering not available, using fallback")

    @property
    def is_available(self) -> bool:
        """Check if truthound tiering is available."""
        return TieringAdapter._tiering_available or False

    def create_store(
        self,
        store_type: str,
        store_config: dict[str, Any],
    ) -> Any:
        """Create a truthound store backend.

        Args:
            store_type: Type of store (filesystem, s3, gcs, etc.)
            store_config: Store configuration.

        Returns:
            Store instance or fallback store.
        """
        if not self.is_available:
            return self._create_fallback_store(store_type, store_config)

        try:
            from truthound.stores import get_store
            return get_store(store_type, **store_config)
        except Exception as e:
            logger.warning(f"Failed to create truthound store: {e}")
            return self._create_fallback_store(store_type, store_config)

    def _create_fallback_store(
        self,
        store_type: str,
        store_config: dict[str, Any],
    ) -> "FallbackStore":
        """Create a fallback store for when truthound is unavailable."""
        return FallbackStore(store_type, store_config)

    def create_storage_tier(
        self,
        name: str,
        store: Any,
        tier_type: str,
        priority: int = 1,
        cost_per_gb: float | None = None,
        retrieval_time_ms: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """Create a truthound StorageTier.

        Args:
            name: Tier name.
            store: Store backend instance.
            tier_type: Tier type (hot, warm, cold, archive).
            priority: Read order priority.
            cost_per_gb: Cost per GB for analysis.
            retrieval_time_ms: Expected retrieval latency.
            metadata: Additional metadata.

        Returns:
            StorageTier instance or dataclass fallback.
        """
        if not self.is_available:
            return FallbackStorageTier(
                name=name,
                store=store,
                tier_type=tier_type,
                priority=priority,
                cost_per_gb=cost_per_gb,
                retrieval_time_ms=retrieval_time_ms,
                metadata=metadata or {},
            )

        try:
            from truthound.stores.tiering.base import StorageTier, TierType as TruthoundTierType

            tier_type_enum = getattr(TruthoundTierType, tier_type.upper(), TruthoundTierType.HOT)

            return StorageTier(
                name=name,
                store=store,
                tier_type=tier_type_enum,
                priority=priority,
                cost_per_gb=cost_per_gb,
                retrieval_time_ms=retrieval_time_ms,
                metadata=metadata or {},
            )
        except Exception as e:
            logger.warning(f"Failed to create truthound StorageTier: {e}")
            return FallbackStorageTier(
                name=name,
                store=store,
                tier_type=tier_type,
                priority=priority,
                cost_per_gb=cost_per_gb,
                retrieval_time_ms=retrieval_time_ms,
                metadata=metadata or {},
            )

    def create_policy(
        self,
        policy_type: str,
        from_tier: str,
        to_tier: str,
        config: dict[str, Any],
        direction: str = "demote",
    ) -> Any:
        """Create a truthound tier policy.

        Args:
            policy_type: Type of policy (age_based, access_based, etc.)
            from_tier: Source tier name.
            to_tier: Destination tier name.
            config: Policy-specific configuration.
            direction: Migration direction (demote/promote).

        Returns:
            TierPolicy instance or fallback.
        """
        if not self.is_available:
            return self._create_fallback_policy(
                policy_type, from_tier, to_tier, config, direction
            )

        try:
            return self._create_truthound_policy(
                policy_type, from_tier, to_tier, config, direction
            )
        except Exception as e:
            logger.warning(f"Failed to create truthound policy: {e}")
            return self._create_fallback_policy(
                policy_type, from_tier, to_tier, config, direction
            )

    def _create_truthound_policy(
        self,
        policy_type: str,
        from_tier: str,
        to_tier: str,
        config: dict[str, Any],
        direction: str,
    ) -> Any:
        """Create a truthound policy from type and config."""
        from truthound.stores.tiering.base import MigrationDirection as TruthoundDirection
        from truthound.stores.tiering import policies as th_policies

        direction_enum = (
            TruthoundDirection.PROMOTE
            if direction == "promote"
            else TruthoundDirection.DEMOTE
        )

        if policy_type == "age_based":
            return th_policies.AgeBasedTierPolicy(
                from_tier=from_tier,
                to_tier=to_tier,
                after_days=config.get("after_days", 0),
                after_hours=config.get("after_hours", 0),
                direction=direction_enum,
            )
        elif policy_type == "access_based":
            return th_policies.AccessBasedTierPolicy(
                from_tier=from_tier,
                to_tier=to_tier,
                inactive_days=config.get("inactive_days"),
                min_access_count=config.get("min_access_count"),
                access_window_days=config.get("access_window_days", 7),
                direction=direction_enum,
            )
        elif policy_type == "size_based":
            return th_policies.SizeBasedTierPolicy(
                from_tier=from_tier,
                to_tier=to_tier,
                min_size_bytes=config.get("min_size_bytes", 0),
                min_size_kb=config.get("min_size_kb", 0),
                min_size_mb=config.get("min_size_mb", 0),
                min_size_gb=config.get("min_size_gb", 0),
                tier_max_size_bytes=config.get("tier_max_size_bytes", 0),
                tier_max_size_gb=config.get("tier_max_size_gb", 0),
                direction=direction_enum,
            )
        elif policy_type == "scheduled":
            return th_policies.ScheduledTierPolicy(
                from_tier=from_tier,
                to_tier=to_tier,
                on_days=config.get("on_days"),
                at_hour=config.get("at_hour"),
                min_age_days=config.get("min_age_days", 0),
                direction=direction_enum,
            )
        elif policy_type == "custom":
            # Custom policies use a predicate function
            predicate_expr = config.get("predicate_expression", "False")

            def custom_predicate(info: Any) -> bool:
                try:
                    # Safe evaluation with limited scope
                    local_vars = {
                        "info": info,
                        "size_bytes": getattr(info, "size_bytes", 0),
                        "access_count": getattr(info, "access_count", 0),
                        "created_at": getattr(info, "created_at", None),
                        "last_accessed": getattr(info, "last_accessed", None),
                    }
                    return bool(eval(predicate_expr, {"__builtins__": {}}, local_vars))
                except Exception:
                    return False

            return th_policies.CustomTierPolicy(
                from_tier=from_tier,
                to_tier=to_tier,
                predicate=custom_predicate,
                description=config.get("description", ""),
            )
        else:
            raise ValueError(f"Unknown policy type: {policy_type}")

    def _create_fallback_policy(
        self,
        policy_type: str,
        from_tier: str,
        to_tier: str,
        config: dict[str, Any],
        direction: str,
    ) -> "FallbackPolicy":
        """Create a fallback policy."""
        return FallbackPolicy(
            policy_type=policy_type,
            from_tier=from_tier,
            to_tier=to_tier,
            config=config,
            direction=direction,
        )

    def create_metadata_store(self) -> Any:
        """Create or get the tier metadata store.

        Returns:
            TierMetadataStore instance.
        """
        if self._metadata_store is not None:
            return self._metadata_store

        if self.is_available:
            try:
                from truthound.stores.tiering.base import InMemoryTierMetadataStore
                self._metadata_store = InMemoryTierMetadataStore()
            except Exception as e:
                logger.warning(f"Failed to create truthound metadata store: {e}")
                self._metadata_store = FallbackMetadataStore()
        else:
            self._metadata_store = FallbackMetadataStore()

        return self._metadata_store

    async def execute_migration(
        self,
        item_id: str,
        from_store: Any,
        to_store: Any,
        metadata_store: Any,
    ) -> MigrationResult:
        """Execute a single item migration.

        Args:
            item_id: ID of item to migrate.
            from_store: Source store.
            to_store: Destination store.
            metadata_store: Metadata store for tracking.

        Returns:
            MigrationResult with migration details.
        """
        started_at = datetime.utcnow()
        from_tier = getattr(from_store, "name", "unknown")
        to_tier = getattr(to_store, "name", "unknown")

        try:
            # Run migration in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                _executor,
                partial(self._sync_migrate, item_id, from_store, to_store, metadata_store),
            )
            completed_at = datetime.utcnow()
            duration_ms = (completed_at - started_at).total_seconds() * 1000

            return MigrationResult(
                item_id=item_id,
                from_tier=from_tier,
                to_tier=to_tier,
                success=result.get("success", False),
                size_bytes=result.get("size_bytes", 0),
                error_message=result.get("error"),
                duration_ms=duration_ms,
                started_at=started_at,
                completed_at=completed_at,
            )
        except Exception as e:
            completed_at = datetime.utcnow()
            duration_ms = (completed_at - started_at).total_seconds() * 1000
            return MigrationResult(
                item_id=item_id,
                from_tier=from_tier,
                to_tier=to_tier,
                success=False,
                error_message=str(e),
                duration_ms=duration_ms,
                started_at=started_at,
                completed_at=completed_at,
            )

    def _sync_migrate(
        self,
        item_id: str,
        from_store: Any,
        to_store: Any,
        metadata_store: Any,
    ) -> dict[str, Any]:
        """Synchronous migration operation (runs in thread pool)."""
        try:
            # Get item from source
            data = from_store.get(item_id)
            if data is None:
                return {"success": False, "error": f"Item {item_id} not found in source tier"}

            # Calculate size
            size_bytes = len(str(data).encode("utf-8")) if data else 0

            # Save to destination
            to_store.save(item_id, data)

            # Delete from source
            from_store.delete(item_id)

            # Update metadata
            if metadata_store:
                info = metadata_store.get_info(item_id)
                if info:
                    info.tier_name = getattr(to_store, "name", "unknown")
                    info.migrated_at = datetime.utcnow()
                    metadata_store.save_info(info)

            return {"success": True, "size_bytes": size_bytes}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def evaluate_policy(
        self,
        policy: Any,
        tier_info: TierInfo,
    ) -> bool:
        """Evaluate if an item should be migrated by a policy.

        Args:
            policy: Tier policy to evaluate.
            tier_info: Item's tier information.

        Returns:
            True if item should be migrated.
        """
        try:
            if hasattr(policy, "should_migrate"):
                return policy.should_migrate(tier_info)
            elif isinstance(policy, FallbackPolicy):
                return policy.evaluate(tier_info)
            return False
        except Exception as e:
            logger.warning(f"Policy evaluation failed: {e}")
            return False


# =============================================================================
# Fallback implementations
# =============================================================================


@dataclass
class FallbackStore:
    """Fallback store implementation when truthound is unavailable."""

    store_type: str
    config: dict[str, Any]
    _data: dict[str, Any] = field(default_factory=dict)

    def save(self, item_id: str, data: Any) -> str:
        self._data[item_id] = data
        return item_id

    def get(self, item_id: str) -> Any:
        return self._data.get(item_id)

    def delete(self, item_id: str) -> bool:
        if item_id in self._data:
            del self._data[item_id]
            return True
        return False

    def list(self) -> list[str]:
        return list(self._data.keys())


@dataclass
class FallbackStorageTier:
    """Fallback StorageTier when truthound is unavailable."""

    name: str
    store: Any
    tier_type: str
    priority: int = 1
    cost_per_gb: float | None = None
    retrieval_time_ms: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FallbackPolicy:
    """Fallback policy implementation."""

    policy_type: str
    from_tier: str
    to_tier: str
    config: dict[str, Any]
    direction: str = "demote"

    def evaluate(self, info: TierInfo) -> bool:
        """Evaluate if item should be migrated."""
        now = datetime.utcnow()

        if self.policy_type == "age_based":
            after_days = self.config.get("after_days", 0)
            after_hours = self.config.get("after_hours", 0)
            threshold = timedelta(days=after_days, hours=after_hours)
            age = now - info.created_at
            return age >= threshold

        elif self.policy_type == "access_based":
            inactive_days = self.config.get("inactive_days")
            min_access_count = self.config.get("min_access_count")

            if inactive_days and info.last_accessed:
                inactive_time = now - info.last_accessed
                if inactive_time >= timedelta(days=inactive_days):
                    return True

            if min_access_count:
                return info.access_count >= min_access_count

            return False

        elif self.policy_type == "size_based":
            total_min_bytes = (
                self.config.get("min_size_bytes", 0)
                + self.config.get("min_size_kb", 0) * 1024
                + self.config.get("min_size_mb", 0) * 1024 * 1024
                + self.config.get("min_size_gb", 0) * 1024 * 1024 * 1024
            )
            return info.size_bytes >= total_min_bytes

        elif self.policy_type == "scheduled":
            on_days = self.config.get("on_days")
            at_hour = self.config.get("at_hour")
            min_age_days = self.config.get("min_age_days", 0)

            if on_days and now.weekday() not in on_days:
                return False
            if at_hour is not None and now.hour != at_hour:
                return False
            if min_age_days:
                age = now - info.created_at
                if age < timedelta(days=min_age_days):
                    return False
            return True

        elif self.policy_type == "custom":
            predicate_expr = self.config.get("predicate_expression", "False")
            try:
                local_vars = {
                    "info": info,
                    "size_bytes": info.size_bytes,
                    "access_count": info.access_count,
                    "created_at": info.created_at,
                    "last_accessed": info.last_accessed,
                }
                return bool(eval(predicate_expr, {"__builtins__": {}}, local_vars))
            except Exception:
                return False

        return False

    def should_migrate(self, info: Any) -> bool:
        """Alias for evaluate for protocol compatibility."""
        if isinstance(info, TierInfo):
            return self.evaluate(info)
        # Convert to TierInfo if needed
        tier_info = TierInfo(
            item_id=getattr(info, "item_id", ""),
            tier_name=getattr(info, "tier_name", ""),
            created_at=getattr(info, "created_at", datetime.utcnow()),
            migrated_at=getattr(info, "migrated_at", None),
            access_count=getattr(info, "access_count", 0),
            last_accessed=getattr(info, "last_accessed", None),
            size_bytes=getattr(info, "size_bytes", 0),
        )
        return self.evaluate(tier_info)


class FallbackMetadataStore:
    """Fallback metadata store when truthound is unavailable."""

    def __init__(self) -> None:
        self._data: dict[str, TierInfo] = {}

    def save_info(self, info: TierInfo) -> None:
        self._data[info.item_id] = info

    def get_info(self, item_id: str) -> TierInfo | None:
        return self._data.get(item_id)

    def delete_info(self, item_id: str) -> bool:
        if item_id in self._data:
            del self._data[item_id]
            return True
        return False

    def list_by_tier(self, tier_name: str) -> list[TierInfo]:
        return [info for info in self._data.values() if info.tier_name == tier_name]

    def update_access(self, item_id: str) -> None:
        if item_id in self._data:
            self._data[item_id].access_count += 1
            self._data[item_id].last_accessed = datetime.utcnow()


# =============================================================================
# Singleton adapter instance
# =============================================================================

_adapter_instance: TieringAdapter | None = None


def get_tiering_adapter() -> TieringAdapter:
    """Get the singleton tiering adapter instance."""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = TieringAdapter()
    return _adapter_instance


# =============================================================================
# Tiering Service
# =============================================================================


class TieringService:
    """Service for storage tiering operations.

    This service provides comprehensive storage tiering using truthound's
    tiering module. It manages:
    - Tier configuration and lifecycle
    - Policy evaluation and execution
    - Migration operations
    - Statistics and reporting
    - Background processing

    The service uses TieringAdapter to interact with truthound,
    maintaining loose coupling with the underlying library.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Async database session.
        """
        self._session = session
        self._adapter = get_tiering_adapter()
        self._tier_stores: dict[str, Any] = {}
        self._tier_objects: dict[str, Any] = {}
        self._policies: dict[str, Any] = {}

    # =========================================================================
    # Tier Management
    # =========================================================================

    async def initialize_tier(self, tier_id: str) -> Any:
        """Initialize a tier's store backend.

        Args:
            tier_id: Tier ID from database.

        Returns:
            Initialized StorageTier object.
        """
        from truthound_dashboard.db.models import StorageTierModel

        # Check cache
        if tier_id in self._tier_objects:
            return self._tier_objects[tier_id]

        # Load from database
        tier = await self._session.get(StorageTierModel, tier_id)
        if not tier:
            raise ValueError(f"Tier '{tier_id}' not found")

        # Create store backend
        store = self._adapter.create_store(tier.store_type, tier.store_config)
        self._tier_stores[tier_id] = store

        # Create StorageTier object
        tier_obj = self._adapter.create_storage_tier(
            name=tier.name,
            store=store,
            tier_type=tier.tier_type,
            priority=tier.priority,
            cost_per_gb=tier.cost_per_gb,
            retrieval_time_ms=tier.retrieval_time_ms,
            metadata=tier.metadata,
        )
        self._tier_objects[tier_id] = tier_obj

        return tier_obj

    async def get_tier_store(self, tier_id: str) -> Any:
        """Get the store backend for a tier.

        Args:
            tier_id: Tier ID.

        Returns:
            Store backend instance.
        """
        if tier_id not in self._tier_stores:
            await self.initialize_tier(tier_id)
        return self._tier_stores.get(tier_id)

    # =========================================================================
    # Policy Management
    # =========================================================================

    async def initialize_policy(self, policy_id: str) -> Any:
        """Initialize a policy object.

        Args:
            policy_id: Policy ID from database.

        Returns:
            Initialized policy object.
        """
        from truthound_dashboard.db.models import TierPolicyModel

        # Check cache
        if policy_id in self._policies:
            return self._policies[policy_id]

        # Load from database
        result = await self._session.execute(
            select(TierPolicyModel)
            .options(
                selectinload(TierPolicyModel.from_tier),
                selectinload(TierPolicyModel.to_tier),
                selectinload(TierPolicyModel.children),
            )
            .where(TierPolicyModel.id == policy_id)
        )
        policy = result.scalar_one_or_none()
        if not policy:
            raise ValueError(f"Policy '{policy_id}' not found")

        # Handle composite policies
        if policy.policy_type == "composite":
            return await self._initialize_composite_policy(policy)

        # Create policy object
        policy_obj = self._adapter.create_policy(
            policy_type=policy.policy_type,
            from_tier=policy.from_tier.name if policy.from_tier else "",
            to_tier=policy.to_tier.name if policy.to_tier else "",
            config=policy.config,
            direction=policy.direction,
        )
        self._policies[policy_id] = policy_obj

        return policy_obj

    async def _initialize_composite_policy(self, policy: Any) -> Any:
        """Initialize a composite policy with children.

        Args:
            policy: Composite policy model.

        Returns:
            Composite policy object.
        """
        if not self._adapter.is_available:
            # Create fallback composite
            child_policies = []
            for child in policy.children:
                child_obj = self._adapter.create_policy(
                    policy_type=child.policy_type,
                    from_tier=child.from_tier.name if child.from_tier else "",
                    to_tier=child.to_tier.name if child.to_tier else "",
                    config=child.config,
                    direction=child.direction,
                )
                child_policies.append(child_obj)

            return FallbackCompositePolicy(
                from_tier=policy.from_tier.name if policy.from_tier else "",
                to_tier=policy.to_tier.name if policy.to_tier else "",
                policies=child_policies,
                require_all=policy.config.get("require_all", True),
                direction=policy.direction,
            )

        try:
            from truthound.stores.tiering.policies import CompositeTierPolicy
            from truthound.stores.tiering.base import MigrationDirection as TruthoundDirection

            direction_enum = (
                TruthoundDirection.PROMOTE
                if policy.direction == "promote"
                else TruthoundDirection.DEMOTE
            )

            # Initialize child policies
            child_policies = []
            for child in policy.children:
                child_obj = await self.initialize_policy(child.id)
                child_policies.append(child_obj)

            return CompositeTierPolicy(
                from_tier=policy.from_tier.name,
                to_tier=policy.to_tier.name,
                policies=child_policies,
                require_all=policy.config.get("require_all", True),
                direction=direction_enum,
            )
        except Exception as e:
            logger.warning(f"Failed to create composite policy: {e}")
            # Fallback
            child_policies = []
            for child in policy.children:
                child_obj = self._adapter.create_policy(
                    policy_type=child.policy_type,
                    from_tier=child.from_tier.name if child.from_tier else "",
                    to_tier=child.to_tier.name if child.to_tier else "",
                    config=child.config,
                    direction=child.direction,
                )
                child_policies.append(child_obj)

            return FallbackCompositePolicy(
                from_tier=policy.from_tier.name if policy.from_tier else "",
                to_tier=policy.to_tier.name if policy.to_tier else "",
                policies=child_policies,
                require_all=policy.config.get("require_all", True),
                direction=policy.direction,
            )

    # =========================================================================
    # Migration Execution
    # =========================================================================

    async def execute_policy(
        self,
        policy_id: str,
        dry_run: bool = False,
        batch_size: int = 100,
    ) -> TieringExecutionResult:
        """Execute a tier policy.

        Args:
            policy_id: Policy ID to execute.
            dry_run: If True, don't actually migrate, just report what would happen.
            batch_size: Maximum items to process.

        Returns:
            Execution result with migration details.
        """
        from truthound_dashboard.db.models import TierPolicyModel, TierMigrationHistoryModel

        start_time = datetime.utcnow()
        result = TieringExecutionResult(
            start_time=start_time,
            end_time=start_time,
            dry_run=dry_run,
        )

        try:
            # Load policy
            db_policy = await self._session.execute(
                select(TierPolicyModel)
                .options(
                    selectinload(TierPolicyModel.from_tier),
                    selectinload(TierPolicyModel.to_tier),
                )
                .where(TierPolicyModel.id == policy_id)
            )
            policy_model = db_policy.scalar_one_or_none()
            if not policy_model:
                result.errors.append(f"Policy '{policy_id}' not found")
                result.end_time = datetime.utcnow()
                return result

            if not policy_model.is_active:
                result.errors.append(f"Policy '{policy_model.name}' is not active")
                result.end_time = datetime.utcnow()
                return result

            # Initialize tiers
            from_tier = await self.initialize_tier(policy_model.from_tier_id)
            to_tier = await self.initialize_tier(policy_model.to_tier_id)
            from_store = self._tier_stores[policy_model.from_tier_id]
            to_store = self._tier_stores[policy_model.to_tier_id]

            # Initialize policy
            policy_obj = await self.initialize_policy(policy_id)

            # Get metadata store
            metadata_store = self._adapter.create_metadata_store()

            # Get items in source tier
            items_to_check = self._get_tier_items(from_store, metadata_store, batch_size)
            result.items_scanned = len(items_to_check)

            # Evaluate and migrate
            for item_info in items_to_check:
                should_migrate = self._adapter.evaluate_policy(policy_obj, item_info)

                if should_migrate:
                    if dry_run:
                        result.items_migrated += 1
                        result.bytes_migrated += item_info.size_bytes
                        result.migrations.append(
                            MigrationResult(
                                item_id=item_info.item_id,
                                from_tier=policy_model.from_tier.name,
                                to_tier=policy_model.to_tier.name,
                                success=True,
                                size_bytes=item_info.size_bytes,
                            )
                        )
                    else:
                        # Execute actual migration
                        migration_result = await self._adapter.execute_migration(
                            item_id=item_info.item_id,
                            from_store=from_store,
                            to_store=to_store,
                            metadata_store=metadata_store,
                        )
                        result.migrations.append(migration_result)

                        if migration_result.success:
                            result.items_migrated += 1
                            result.bytes_migrated += migration_result.size_bytes

                            # Record in history
                            history_entry = TierMigrationHistoryModel(
                                id=_generate_id(),
                                policy_id=policy_id,
                                item_id=item_info.item_id,
                                from_tier_id=policy_model.from_tier_id,
                                to_tier_id=policy_model.to_tier_id,
                                size_bytes=migration_result.size_bytes,
                                started_at=migration_result.started_at,
                                completed_at=migration_result.completed_at,
                                status="completed",
                            )
                            self._session.add(history_entry)
                        else:
                            result.items_failed += 1
                            result.errors.append(
                                f"Migration failed for {item_info.item_id}: {migration_result.error_message}"
                            )

                            # Record failure
                            history_entry = TierMigrationHistoryModel(
                                id=_generate_id(),
                                policy_id=policy_id,
                                item_id=item_info.item_id,
                                from_tier_id=policy_model.from_tier_id,
                                to_tier_id=policy_model.to_tier_id,
                                size_bytes=0,
                                started_at=migration_result.started_at,
                                completed_at=migration_result.completed_at,
                                status="failed",
                                error_message=migration_result.error_message,
                            )
                            self._session.add(history_entry)

            if not dry_run:
                await self._session.commit()

        except Exception as e:
            logger.exception(f"Policy execution failed: {e}")
            result.errors.append(str(e))

        result.end_time = datetime.utcnow()
        return result

    def _get_tier_items(
        self,
        store: Any,
        metadata_store: Any,
        limit: int,
    ) -> list[TierInfo]:
        """Get items in a tier with their metadata.

        Args:
            store: Store backend.
            metadata_store: Metadata store.
            limit: Maximum items to return.

        Returns:
            List of TierInfo objects.
        """
        items = []
        tier_name = getattr(store, "name", "unknown")

        try:
            item_ids = store.list()[:limit] if hasattr(store, "list") else []

            for item_id in item_ids:
                info = metadata_store.get_info(item_id)
                if info:
                    items.append(info)
                else:
                    # Create basic info if not tracked
                    items.append(
                        TierInfo(
                            item_id=item_id,
                            tier_name=tier_name,
                            created_at=datetime.utcnow(),
                        )
                    )
        except Exception as e:
            logger.warning(f"Failed to list tier items: {e}")

        return items

    async def migrate_item(
        self,
        item_id: str,
        from_tier_id: str,
        to_tier_id: str,
    ) -> MigrationResult:
        """Migrate a single item between tiers.

        Args:
            item_id: Item to migrate.
            from_tier_id: Source tier ID.
            to_tier_id: Destination tier ID.

        Returns:
            Migration result.
        """
        from truthound_dashboard.db.models import TierMigrationHistoryModel

        from_store = await self.get_tier_store(from_tier_id)
        to_store = await self.get_tier_store(to_tier_id)
        metadata_store = self._adapter.create_metadata_store()

        result = await self._adapter.execute_migration(
            item_id=item_id,
            from_store=from_store,
            to_store=to_store,
            metadata_store=metadata_store,
        )

        # Record in history
        history_entry = TierMigrationHistoryModel(
            id=_generate_id(),
            item_id=item_id,
            from_tier_id=from_tier_id,
            to_tier_id=to_tier_id,
            size_bytes=result.size_bytes,
            started_at=result.started_at,
            completed_at=result.completed_at,
            status="completed" if result.success else "failed",
            error_message=result.error_message,
        )
        self._session.add(history_entry)
        await self._session.commit()

        return result

    # =========================================================================
    # Access Tracking
    # =========================================================================

    async def record_access(self, item_id: str, tier_id: str) -> None:
        """Record an access to an item for intelligent tiering.

        Args:
            item_id: Accessed item ID.
            tier_id: Current tier ID.
        """
        metadata_store = self._adapter.create_metadata_store()

        info = metadata_store.get_info(item_id)
        if info:
            metadata_store.update_access(item_id)
        else:
            # Create new tracking entry
            info = TierInfo(
                item_id=item_id,
                tier_name=tier_id,
                created_at=datetime.utcnow(),
                access_count=1,
                last_accessed=datetime.utcnow(),
            )
            metadata_store.save_info(info)

    # =========================================================================
    # Background Processing
    # =========================================================================

    async def process_due_policies(self) -> list[TieringExecutionResult]:
        """Process all active policies that are due for execution.

        Returns:
            List of execution results.
        """
        from truthound_dashboard.db.models import TierPolicyModel, TieringConfigModel

        results = []

        # Get active config
        config_result = await self._session.execute(
            select(TieringConfigModel).where(TieringConfigModel.is_active == True)
        )
        config = config_result.scalar_one_or_none()

        batch_size = config.batch_size if config else 100

        # Get active policies
        policies_result = await self._session.execute(
            select(TierPolicyModel)
            .where(TierPolicyModel.is_active == True)
            .where(TierPolicyModel.parent_id == None)  # Only root policies
            .order_by(TierPolicyModel.priority)
        )
        policies = policies_result.scalars().all()

        for policy in policies:
            try:
                result = await self.execute_policy(
                    policy_id=policy.id,
                    dry_run=False,
                    batch_size=batch_size,
                )
                results.append(result)
            except Exception as e:
                logger.exception(f"Failed to execute policy {policy.id}: {e}")
                results.append(
                    TieringExecutionResult(
                        start_time=datetime.utcnow(),
                        end_time=datetime.utcnow(),
                        errors=[str(e)],
                    )
                )

        return results


@dataclass
class FallbackCompositePolicy:
    """Fallback composite policy implementation."""

    from_tier: str
    to_tier: str
    policies: list[Any]
    require_all: bool = True
    direction: str = "demote"

    def should_migrate(self, info: Any) -> bool:
        """Evaluate composite policy."""
        results = [p.should_migrate(info) for p in self.policies]

        if self.require_all:
            return all(results)
        return any(results)

    def evaluate(self, info: TierInfo) -> bool:
        """Alias for should_migrate."""
        return self.should_migrate(info)


# =============================================================================
# Scheduler Integration
# =============================================================================


async def process_tiering_policies(session: AsyncSession) -> list[TieringExecutionResult]:
    """Background task to process tiering policies.

    This function is called by the scheduler to process all due policies.

    Args:
        session: Database session.

    Returns:
        List of execution results.
    """
    service = TieringService(session)
    return await service.process_due_policies()
