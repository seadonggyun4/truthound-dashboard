"""Pydantic schemas for storage tiering features.

This module provides schemas for:
- Storage tiers (hot, warm, cold, archive)
- Tier policies (age-based, access-based, size-based, scheduled, composite, custom)
- Tiering configurations
- Migration history

Based on truthound 1.2.10+ storage tiering capabilities.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from .base import BaseSchema, IDMixin, ListResponseWrapper, TimestampMixin


# =============================================================================
# Enums
# =============================================================================


class TierType(str, Enum):
    """Storage tier types."""

    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    ARCHIVE = "archive"


class MigrationDirection(str, Enum):
    """Migration direction for tier policies."""

    DEMOTE = "demote"
    PROMOTE = "promote"


class TierPolicyType(str, Enum):
    """Types of tier policies."""

    AGE_BASED = "age_based"
    ACCESS_BASED = "access_based"
    SIZE_BASED = "size_based"
    SCHEDULED = "scheduled"
    COMPOSITE = "composite"
    CUSTOM = "custom"


class MigrationStatus(str, Enum):
    """Migration operation status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# Storage Tier Schemas
# =============================================================================


class StorageTierBase(BaseSchema):
    """Base storage tier schema."""

    name: str = Field(
        ...,
        description="Unique tier name",
        min_length=1,
        max_length=50,
        examples=["hot", "warm", "cold", "archive"],
    )
    tier_type: TierType = Field(
        default=TierType.HOT,
        description="Tier classification",
    )
    store_type: str = Field(
        ...,
        description="Backend store type",
        min_length=1,
        max_length=50,
        examples=["filesystem", "s3", "gcs", "azure_blob"],
    )
    store_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Store backend configuration",
    )
    priority: int = Field(
        default=1,
        description="Read order priority (lower = higher priority)",
        ge=1,
        le=100,
    )
    cost_per_gb: float | None = Field(
        default=None,
        description="Cost per GB for cost analysis",
        ge=0,
    )
    retrieval_time_ms: int | None = Field(
        default=None,
        description="Expected retrieval latency in milliseconds",
        ge=0,
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional tier metadata",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the tier is active",
    )


class StorageTierCreate(StorageTierBase):
    """Schema for creating a storage tier."""

    pass


class StorageTierUpdate(BaseSchema):
    """Schema for updating a storage tier."""

    name: str | None = Field(None, min_length=1, max_length=50)
    tier_type: TierType | None = None
    store_type: str | None = Field(None, min_length=1, max_length=50)
    store_config: dict[str, Any] | None = None
    priority: int | None = Field(None, ge=1, le=100)
    cost_per_gb: float | None = Field(None, ge=0)
    retrieval_time_ms: int | None = Field(None, ge=0)
    metadata: dict[str, Any] | None = None
    is_active: bool | None = None


class StorageTierResponse(StorageTierBase, IDMixin, TimestampMixin):
    """Schema for storage tier response."""

    pass


class StorageTierListResponse(ListResponseWrapper):
    """Schema for storage tier list response."""

    items: list[StorageTierResponse]


# =============================================================================
# Tier Policy Schemas
# =============================================================================


class PolicyConfigBase(BaseModel):
    """Base configuration for all policy types."""

    pass


class AgeBasedPolicyConfig(PolicyConfigBase):
    """Configuration for age-based tier policy.

    Migrate items based on age.
    """

    after_days: int = Field(
        default=0,
        description="Days before migration",
        ge=0,
        le=3650,  # 10 years max
    )
    after_hours: int = Field(
        default=0,
        description="Additional hours before migration",
        ge=0,
        le=23,
    )

    @model_validator(mode="after")
    def validate_at_least_one_time(self) -> "AgeBasedPolicyConfig":
        """Ensure at least one time unit is specified."""
        if self.after_days == 0 and self.after_hours == 0:
            raise ValueError("At least one time unit (days or hours) must be specified")
        return self


class AccessBasedPolicyConfig(PolicyConfigBase):
    """Configuration for access-based tier policy.

    Migrate based on access patterns.
    """

    inactive_days: int | None = Field(
        default=None,
        description="Days without access for demotion",
        ge=1,
        le=3650,
    )
    min_access_count: int | None = Field(
        default=None,
        description="Minimum accesses for promotion",
        ge=1,
        le=1000000,
    )
    access_window_days: int = Field(
        default=7,
        description="Window for counting accesses (days)",
        ge=1,
        le=365,
    )

    @model_validator(mode="after")
    def validate_at_least_one_condition(self) -> "AccessBasedPolicyConfig":
        """Ensure at least one condition is specified."""
        if self.inactive_days is None and self.min_access_count is None:
            raise ValueError(
                "At least one condition (inactive_days or min_access_count) must be specified"
            )
        return self


class SizeBasedPolicyConfig(PolicyConfigBase):
    """Configuration for size-based tier policy.

    Migrate based on item size or tier capacity.
    """

    min_size_bytes: int = Field(
        default=0,
        description="Minimum item size in bytes",
        ge=0,
    )
    min_size_kb: int = Field(
        default=0,
        description="Minimum item size in KB",
        ge=0,
    )
    min_size_mb: int = Field(
        default=0,
        description="Minimum item size in MB",
        ge=0,
    )
    min_size_gb: int = Field(
        default=0,
        description="Minimum item size in GB",
        ge=0,
    )
    tier_max_size_bytes: int = Field(
        default=0,
        description="Maximum total tier size in bytes",
        ge=0,
    )
    tier_max_size_gb: int = Field(
        default=0,
        description="Maximum total tier size in GB",
        ge=0,
    )

    @model_validator(mode="after")
    def validate_at_least_one_size(self) -> "SizeBasedPolicyConfig":
        """Ensure at least one size condition is specified."""
        has_item_size = any([
            self.min_size_bytes > 0,
            self.min_size_kb > 0,
            self.min_size_mb > 0,
            self.min_size_gb > 0,
        ])
        has_tier_size = any([
            self.tier_max_size_bytes > 0,
            self.tier_max_size_gb > 0,
        ])
        if not has_item_size and not has_tier_size:
            raise ValueError("At least one size condition must be specified")
        return self

    @property
    def total_min_size_bytes(self) -> int:
        """Calculate total minimum size in bytes."""
        return (
            self.min_size_bytes
            + self.min_size_kb * 1024
            + self.min_size_mb * 1024 * 1024
            + self.min_size_gb * 1024 * 1024 * 1024
        )

    @property
    def total_tier_max_bytes(self) -> int:
        """Calculate total tier max size in bytes."""
        return self.tier_max_size_bytes + self.tier_max_size_gb * 1024 * 1024 * 1024


class ScheduledPolicyConfig(PolicyConfigBase):
    """Configuration for scheduled tier policy.

    Migrate on a schedule (specific days/times).
    """

    on_days: list[int] | None = Field(
        default=None,
        description="Days to run (0=Monday, 6=Sunday)",
        examples=[[0, 1, 2, 3, 4], [5, 6]],
    )
    at_hour: int | None = Field(
        default=None,
        description="Hour to run (0-23)",
        ge=0,
        le=23,
    )
    min_age_days: int = Field(
        default=0,
        description="Minimum item age in days",
        ge=0,
        le=3650,
    )

    @field_validator("on_days")
    @classmethod
    def validate_days(cls, v: list[int] | None) -> list[int] | None:
        """Validate day values."""
        if v is not None:
            for day in v:
                if day < 0 or day > 6:
                    raise ValueError(f"Day must be 0-6, got {day}")
        return v


class CompositePolicyConfig(PolicyConfigBase):
    """Configuration for composite tier policy.

    Combine multiple policies with AND/OR logic.
    """

    require_all: bool = Field(
        default=True,
        description="True = AND logic (all must match), False = OR logic (any match)",
    )
    child_policy_ids: list[str] = Field(
        default_factory=list,
        description="IDs of child policies to combine",
    )

    @field_validator("child_policy_ids")
    @classmethod
    def validate_min_children(cls, v: list[str]) -> list[str]:
        """Ensure at least 2 child policies for composite."""
        if len(v) < 2:
            raise ValueError("Composite policy requires at least 2 child policies")
        return v


class CustomPolicyConfig(PolicyConfigBase):
    """Configuration for custom tier policy.

    Define custom migration logic with a predicate expression.
    """

    predicate_expression: str = Field(
        ...,
        description="Python expression for migration predicate",
        min_length=1,
        max_length=1000,
    )
    description: str = Field(
        default="",
        description="Human-readable description of the custom logic",
        max_length=500,
    )


class TierPolicyBase(BaseSchema):
    """Base tier policy schema."""

    name: str = Field(
        ...,
        description="Policy name",
        min_length=1,
        max_length=255,
    )
    description: str | None = Field(
        default=None,
        description="Policy description",
        max_length=1000,
    )
    policy_type: TierPolicyType = Field(
        ...,
        description="Type of policy",
    )
    from_tier_id: str = Field(
        ...,
        description="Source tier ID",
    )
    to_tier_id: str = Field(
        ...,
        description="Destination tier ID",
    )
    direction: MigrationDirection = Field(
        default=MigrationDirection.DEMOTE,
        description="Migration direction",
    )
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Policy-specific configuration",
    )
    is_active: bool = Field(
        default=True,
        description="Whether policy is active",
    )
    priority: int = Field(
        default=0,
        description="Execution priority (lower = runs first)",
        ge=0,
        le=1000,
    )


class TierPolicyCreate(TierPolicyBase):
    """Schema for creating a tier policy."""

    parent_id: str | None = Field(
        default=None,
        description="Parent composite policy ID (for nested policies)",
    )


class TierPolicyUpdate(BaseSchema):
    """Schema for updating a tier policy."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    policy_type: TierPolicyType | None = None
    from_tier_id: str | None = None
    to_tier_id: str | None = None
    direction: MigrationDirection | None = None
    config: dict[str, Any] | None = None
    is_active: bool | None = None
    priority: int | None = Field(None, ge=0, le=1000)
    parent_id: str | None = None


class TierPolicyResponse(TierPolicyBase, IDMixin, TimestampMixin):
    """Schema for tier policy response."""

    parent_id: str | None = Field(
        default=None,
        description="Parent composite policy ID",
    )
    child_count: int = Field(
        default=0,
        description="Number of child policies (for composite)",
    )
    from_tier_name: str | None = Field(
        default=None,
        description="Source tier name",
    )
    to_tier_name: str | None = Field(
        default=None,
        description="Destination tier name",
    )


class TierPolicyListResponse(ListResponseWrapper):
    """Schema for tier policy list response."""

    items: list[TierPolicyResponse]


class TierPolicyWithChildren(TierPolicyResponse):
    """Schema for tier policy with nested children."""

    children: list["TierPolicyWithChildren"] = Field(
        default_factory=list,
        description="Nested child policies",
    )


# Rebuild for self-referencing model
TierPolicyWithChildren.model_rebuild()


# =============================================================================
# Tiering Configuration Schemas
# =============================================================================


class TieringConfigBase(BaseSchema):
    """Base tiering configuration schema."""

    name: str = Field(
        ...,
        description="Configuration name",
        min_length=1,
        max_length=255,
    )
    description: str | None = Field(
        default=None,
        description="Configuration description",
        max_length=1000,
    )
    default_tier_id: str | None = Field(
        default=None,
        description="Default tier for new items",
    )
    enable_promotion: bool = Field(
        default=True,
        description="Whether to auto-promote on frequent access",
    )
    promotion_threshold: int = Field(
        default=10,
        description="Access count to trigger promotion",
        ge=1,
        le=10000,
    )
    check_interval_hours: int = Field(
        default=24,
        description="Hours between auto-checks",
        ge=1,
        le=168,  # 1 week max
    )
    batch_size: int = Field(
        default=100,
        description="Items per migration batch",
        ge=1,
        le=10000,
    )
    enable_parallel_migration: bool = Field(
        default=False,
        description="Whether to enable parallel migration",
    )
    max_parallel_migrations: int = Field(
        default=4,
        description="Maximum concurrent migrations",
        ge=1,
        le=100,
    )
    is_active: bool = Field(
        default=True,
        description="Whether configuration is active",
    )


class TieringConfigCreate(TieringConfigBase):
    """Schema for creating a tiering configuration."""

    pass


class TieringConfigUpdate(BaseSchema):
    """Schema for updating a tiering configuration."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    default_tier_id: str | None = None
    enable_promotion: bool | None = None
    promotion_threshold: int | None = Field(None, ge=1, le=10000)
    check_interval_hours: int | None = Field(None, ge=1, le=168)
    batch_size: int | None = Field(None, ge=1, le=10000)
    enable_parallel_migration: bool | None = None
    max_parallel_migrations: int | None = Field(None, ge=1, le=100)
    is_active: bool | None = None


class TieringConfigResponse(TieringConfigBase, IDMixin, TimestampMixin):
    """Schema for tiering configuration response."""

    default_tier_name: str | None = Field(
        default=None,
        description="Default tier name",
    )


class TieringConfigListResponse(ListResponseWrapper):
    """Schema for tiering configuration list response."""

    items: list[TieringConfigResponse]


# =============================================================================
# Migration History Schemas
# =============================================================================


class MigrationHistoryBase(BaseSchema):
    """Base migration history schema."""

    policy_id: str | None = Field(
        default=None,
        description="Policy that triggered migration",
    )
    item_id: str = Field(
        ...,
        description="ID of the migrated item",
        min_length=1,
        max_length=255,
    )
    from_tier_id: str = Field(
        ...,
        description="Source tier ID",
    )
    to_tier_id: str = Field(
        ...,
        description="Destination tier ID",
    )
    size_bytes: int = Field(
        default=0,
        description="Size of migrated item",
        ge=0,
    )
    status: MigrationStatus = Field(
        default=MigrationStatus.PENDING,
        description="Migration status",
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if failed",
        max_length=1000,
    )


class MigrationHistoryCreate(MigrationHistoryBase):
    """Schema for creating a migration history entry."""

    pass


class MigrationHistoryResponse(MigrationHistoryBase, IDMixin):
    """Schema for migration history response."""

    started_at: datetime = Field(..., description="When migration started")
    completed_at: datetime | None = Field(
        default=None,
        description="When migration completed",
    )
    duration_ms: float | None = Field(
        default=None,
        description="Migration duration in milliseconds",
    )
    from_tier_name: str | None = Field(
        default=None,
        description="Source tier name",
    )
    to_tier_name: str | None = Field(
        default=None,
        description="Destination tier name",
    )
    policy_name: str | None = Field(
        default=None,
        description="Policy name",
    )


class MigrationHistoryListResponse(ListResponseWrapper):
    """Schema for migration history list response."""

    items: list[MigrationHistoryResponse]


# =============================================================================
# Statistics Schemas
# =============================================================================


class TierStatistics(BaseModel):
    """Statistics for a single tier."""

    tier_id: str
    tier_name: str
    tier_type: TierType
    item_count: int = 0
    total_size_bytes: int = 0
    total_size_gb: float = 0.0
    estimated_cost: float | None = None
    policy_count: int = 0


class TieringStatistics(BaseModel):
    """Overall tiering statistics."""

    total_tiers: int = 0
    active_tiers: int = 0
    total_policies: int = 0
    active_policies: int = 0
    composite_policies: int = 0
    total_migrations: int = 0
    successful_migrations: int = 0
    failed_migrations: int = 0
    total_bytes_migrated: int = 0
    tier_stats: list[TierStatistics] = Field(default_factory=list)


class PolicyTypeInfo(BaseModel):
    """Information about a policy type."""

    type: TierPolicyType
    name: str
    description: str
    config_schema: dict[str, Any]


class PolicyTypesResponse(BaseModel):
    """Response for available policy types."""

    policy_types: list[PolicyTypeInfo]


# =============================================================================
# Policy Execution Schemas
# =============================================================================


class PolicyExecutionRequest(BaseModel):
    """Request for policy execution."""

    dry_run: bool = Field(
        default=False,
        description="If True, don't actually migrate, just report what would happen",
    )
    batch_size: int = Field(
        default=100,
        description="Maximum items to process",
        ge=1,
        le=10000,
    )


class MigrationItemResponse(BaseModel):
    """Response for a single migration operation."""

    item_id: str
    from_tier: str
    to_tier: str
    success: bool
    size_bytes: int = 0
    error_message: str | None = None
    duration_ms: float = 0.0


class PolicyExecutionResponse(BaseModel):
    """Response for policy execution."""

    policy_id: str
    dry_run: bool
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    items_scanned: int = 0
    items_migrated: int = 0
    items_failed: int = 0
    bytes_migrated: int = 0
    success_rate: float = 1.0
    errors: list[str] = Field(default_factory=list)
    migrations: list[MigrationItemResponse] = Field(default_factory=list)


class MigrateItemRequest(BaseModel):
    """Request for migrating a single item."""

    from_tier_id: str = Field(..., description="Source tier ID")
    to_tier_id: str = Field(..., description="Destination tier ID")


class PolicyExecutionSummary(BaseModel):
    """Summary of a single policy execution."""

    items_scanned: int = 0
    items_migrated: int = 0
    items_failed: int = 0
    bytes_migrated: int = 0
    duration_seconds: float = 0.0
    success_rate: float = 1.0
    errors: list[str] = Field(default_factory=list)


class ProcessPoliciesResponse(BaseModel):
    """Response for processing all policies."""

    policies_executed: int = 0
    total_items_scanned: int = 0
    total_items_migrated: int = 0
    total_items_failed: int = 0
    total_bytes_migrated: int = 0
    errors: list[str] = Field(default_factory=list)
    policy_results: list[PolicyExecutionSummary] = Field(default_factory=list)


class TieringStatusResponse(BaseModel):
    """Response for tiering system status."""

    truthound_available: bool = Field(
        ...,
        description="Whether truthound tiering module is available",
    )
    tiering_enabled: bool = Field(
        ...,
        description="Whether tiering is enabled via active config",
    )
    active_config_id: str | None = Field(
        default=None,
        description="Active configuration ID",
    )
    active_config_name: str | None = Field(
        default=None,
        description="Active configuration name",
    )
    check_interval_hours: int | None = Field(
        default=None,
        description="Hours between automatic policy checks",
    )
    active_tiers: int = Field(
        default=0,
        description="Number of active storage tiers",
    )
    active_policies: int = Field(
        default=0,
        description="Number of active policies",
    )
    migrations_last_24h: int = Field(
        default=0,
        description="Number of migrations in the last 24 hours",
    )
