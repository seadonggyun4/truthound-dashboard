"""Pydantic schemas for advanced notification features.

This module provides schemas for:
- Routing rules (11 rule types + combinators)
- Deduplication configuration (4 strategies, 6 policies)
- Throttling configuration
- Escalation policies and incidents
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

from .base import BaseSchema, IDMixin, ListResponseWrapper, TimestampMixin


# =============================================================================
# Enums
# =============================================================================


class RuleType(str, Enum):
    """Available routing rule types."""

    SEVERITY = "severity"
    ISSUE_COUNT = "issue_count"
    PASS_RATE = "pass_rate"
    TIME_WINDOW = "time_window"
    TAG = "tag"
    DATA_ASSET = "data_asset"
    METADATA = "metadata"
    STATUS = "status"
    ERROR = "error"
    ALWAYS = "always"
    NEVER = "never"
    # Combinators
    ALL_OF = "all_of"
    ANY_OF = "any_of"
    NOT = "not"


class DeduplicationStrategy(str, Enum):
    """Deduplication window strategies."""

    SLIDING = "sliding"
    TUMBLING = "tumbling"
    SESSION = "session"
    ADAPTIVE = "adaptive"


class DeduplicationPolicy(str, Enum):
    """Deduplication policies."""

    NONE = "none"
    BASIC = "basic"
    SEVERITY = "severity"
    ISSUE_BASED = "issue_based"
    STRICT = "strict"
    CUSTOM = "custom"


class EscalationState(str, Enum):
    """Escalation incident states."""

    PENDING = "pending"
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class TargetType(str, Enum):
    """Escalation target types."""

    USER = "user"
    GROUP = "group"
    ONCALL = "oncall"
    CHANNEL = "channel"


# =============================================================================
# Routing Rules Schemas
# =============================================================================


class RuleConfig(BaseModel):
    """Base configuration for a routing rule."""

    type: str = Field(..., description="Rule type")
    params: dict[str, Any] = Field(default_factory=dict, description="Rule parameters")


class RoutingRuleBase(BaseSchema):
    """Base routing rule schema."""

    name: str = Field(..., description="Rule name", min_length=1, max_length=255)
    rule_config: dict[str, Any] = Field(..., description="Rule configuration JSON")
    actions: list[str] = Field(..., description="Channel IDs to notify", min_length=1)
    priority: int = Field(default=0, description="Priority (higher = more important)")
    is_active: bool = Field(default=True, description="Whether rule is active")
    stop_on_match: bool = Field(default=False, description="Stop processing after match")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RoutingRuleCreate(RoutingRuleBase):
    """Schema for creating a routing rule."""

    pass


class RoutingRuleUpdate(BaseSchema):
    """Schema for updating a routing rule."""

    name: str | None = Field(None, description="Rule name", min_length=1, max_length=255)
    rule_config: dict[str, Any] | None = Field(None, description="Rule configuration JSON")
    actions: list[str] | None = Field(None, description="Channel IDs to notify", min_length=1)
    priority: int | None = Field(None, description="Priority")
    is_active: bool | None = Field(None, description="Whether rule is active")
    stop_on_match: bool | None = Field(None, description="Stop processing after match")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class RoutingRuleResponse(RoutingRuleBase, IDMixin, TimestampMixin):
    """Schema for routing rule response."""

    pass


class RoutingRuleListResponse(ListResponseWrapper):
    """Schema for routing rule list response."""

    items: list[RoutingRuleResponse]


class RuleTypeInfo(BaseModel):
    """Information about a rule type."""

    type: str = Field(..., description="Rule type identifier")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Rule description")
    param_schema: dict[str, Any] = Field(..., description="Parameter schema")


class RuleTypesResponse(BaseModel):
    """Response for available rule types."""

    rule_types: list[RuleTypeInfo]


# =============================================================================
# Deduplication Schemas
# =============================================================================


class DeduplicationConfigBase(BaseSchema):
    """Base deduplication configuration schema."""

    name: str = Field(..., description="Configuration name", min_length=1, max_length=255)
    strategy: DeduplicationStrategy = Field(
        default=DeduplicationStrategy.SLIDING,
        description="Window strategy",
    )
    policy: DeduplicationPolicy = Field(
        default=DeduplicationPolicy.BASIC,
        description="Deduplication policy",
    )
    window_seconds: int = Field(
        default=300,
        description="Window duration in seconds",
        ge=1,
        le=86400,
    )
    is_active: bool = Field(default=True, description="Whether config is active")


class DeduplicationConfigCreate(DeduplicationConfigBase):
    """Schema for creating deduplication config."""

    pass


class DeduplicationConfigUpdate(BaseSchema):
    """Schema for updating deduplication config."""

    name: str | None = Field(None, description="Configuration name")
    strategy: DeduplicationStrategy | None = Field(None, description="Window strategy")
    policy: DeduplicationPolicy | None = Field(None, description="Deduplication policy")
    window_seconds: int | None = Field(None, description="Window duration in seconds")
    is_active: bool | None = Field(None, description="Whether config is active")


class DeduplicationConfigResponse(DeduplicationConfigBase, IDMixin, TimestampMixin):
    """Schema for deduplication config response."""

    pass


class DeduplicationConfigListResponse(ListResponseWrapper):
    """Schema for deduplication config list response."""

    items: list[DeduplicationConfigResponse]


class DeduplicationStats(BaseModel):
    """Deduplication statistics."""

    total_received: int = Field(default=0, description="Total notifications received")
    total_deduplicated: int = Field(default=0, description="Total notifications deduplicated")
    total_passed: int = Field(default=0, description="Total notifications passed through")
    dedup_rate: float = Field(default=0.0, description="Deduplication rate percentage")
    active_fingerprints: int = Field(default=0, description="Active fingerprints in window")


# =============================================================================
# Throttling Schemas
# =============================================================================


class ThrottlingConfigBase(BaseSchema):
    """Base throttling configuration schema."""

    name: str = Field(..., description="Configuration name", min_length=1, max_length=255)
    per_minute: int | None = Field(None, description="Max notifications per minute", ge=1)
    per_hour: int | None = Field(None, description="Max notifications per hour", ge=1)
    per_day: int | None = Field(None, description="Max notifications per day", ge=1)
    burst_allowance: float = Field(
        default=1.5,
        description="Burst allowance factor",
        ge=1.0,
        le=10.0,
    )
    channel_id: str | None = Field(None, description="Channel ID (null = global)")
    is_active: bool = Field(default=True, description="Whether config is active")


class ThrottlingConfigCreate(ThrottlingConfigBase):
    """Schema for creating throttling config."""

    pass


class ThrottlingConfigUpdate(BaseSchema):
    """Schema for updating throttling config."""

    name: str | None = Field(None, description="Configuration name")
    per_minute: int | None = Field(None, description="Max notifications per minute")
    per_hour: int | None = Field(None, description="Max notifications per hour")
    per_day: int | None = Field(None, description="Max notifications per day")
    burst_allowance: float | None = Field(None, description="Burst allowance factor")
    channel_id: str | None = Field(None, description="Channel ID")
    is_active: bool | None = Field(None, description="Whether config is active")


class ThrottlingConfigResponse(ThrottlingConfigBase, IDMixin, TimestampMixin):
    """Schema for throttling config response."""

    pass


class ThrottlingConfigListResponse(ListResponseWrapper):
    """Schema for throttling config list response."""

    items: list[ThrottlingConfigResponse]


class ThrottlingStats(BaseModel):
    """Throttling statistics."""

    total_received: int = Field(default=0, description="Total notifications received")
    total_throttled: int = Field(default=0, description="Total notifications throttled")
    total_passed: int = Field(default=0, description="Total notifications passed through")
    throttle_rate: float = Field(default=0.0, description="Throttle rate percentage")
    current_window_count: int = Field(default=0, description="Count in current window")


# =============================================================================
# Escalation Schemas
# =============================================================================


class EscalationTargetBase(BaseModel):
    """Escalation target schema."""

    type: TargetType = Field(..., description="Target type")
    identifier: str = Field(..., description="Target identifier (email, group name, etc.)")
    channel: str = Field(..., description="Notification channel ID")


class EscalationLevelBase(BaseModel):
    """Escalation level schema."""

    level: int = Field(..., description="Level number (1 = first)", ge=1)
    delay_minutes: int = Field(..., description="Delay before escalating to next level", ge=0)
    targets: list[EscalationTargetBase] = Field(
        ...,
        description="Targets to notify at this level",
        min_length=1,
    )


class EscalationPolicyBase(BaseSchema):
    """Base escalation policy schema."""

    name: str = Field(..., description="Policy name", min_length=1, max_length=255)
    description: str = Field(default="", description="Policy description")
    levels: list[EscalationLevelBase] = Field(
        ...,
        description="Escalation levels",
        min_length=1,
    )
    auto_resolve_on_success: bool = Field(
        default=True,
        description="Auto-resolve when validation passes",
    )
    max_escalations: int = Field(default=3, description="Maximum escalation attempts", ge=1)
    is_active: bool = Field(default=True, description="Whether policy is active")


class EscalationPolicyCreate(EscalationPolicyBase):
    """Schema for creating escalation policy."""

    pass


class EscalationPolicyUpdate(BaseSchema):
    """Schema for updating escalation policy."""

    name: str | None = Field(None, description="Policy name")
    description: str | None = Field(None, description="Policy description")
    levels: list[EscalationLevelBase] | None = Field(None, description="Escalation levels")
    auto_resolve_on_success: bool | None = Field(None, description="Auto-resolve on success")
    max_escalations: int | None = Field(None, description="Maximum escalation attempts")
    is_active: bool | None = Field(None, description="Whether policy is active")


class EscalationPolicyResponse(EscalationPolicyBase, IDMixin, TimestampMixin):
    """Schema for escalation policy response."""

    pass


class EscalationPolicyListResponse(ListResponseWrapper):
    """Schema for escalation policy list response."""

    items: list[EscalationPolicyResponse]


class EscalationEventBase(BaseModel):
    """Escalation event (state transition history)."""

    from_state: str | None = Field(None, description="Previous state")
    to_state: str = Field(..., description="New state")
    actor: str | None = Field(None, description="Who triggered the transition")
    message: str = Field(default="", description="Event message")
    timestamp: datetime = Field(..., description="When the event occurred")


class EscalationIncidentBase(BaseSchema):
    """Base escalation incident schema."""

    policy_id: str = Field(..., description="Escalation policy ID")
    incident_ref: str = Field(..., description="External reference (e.g., validation ID)")
    state: EscalationState = Field(
        default=EscalationState.PENDING,
        description="Current state",
    )
    current_level: int = Field(default=1, description="Current escalation level")
    escalation_count: int = Field(default=0, description="Number of escalations")
    context: dict[str, Any] = Field(default_factory=dict, description="Incident context")
    acknowledged_by: str | None = Field(None, description="Who acknowledged")
    acknowledged_at: datetime | None = Field(None, description="When acknowledged")
    resolved_by: str | None = Field(None, description="Who resolved")
    resolved_at: datetime | None = Field(None, description="When resolved")
    next_escalation_at: datetime | None = Field(None, description="Next escalation time")


class EscalationIncidentResponse(EscalationIncidentBase, IDMixin, TimestampMixin):
    """Schema for escalation incident response."""

    events: list[EscalationEventBase] = Field(
        default_factory=list,
        description="State transition history",
    )


class EscalationIncidentListResponse(ListResponseWrapper):
    """Schema for escalation incident list response."""

    items: list[EscalationIncidentResponse]


class AcknowledgeRequest(BaseModel):
    """Request to acknowledge an incident."""

    actor: str = Field(..., description="Who is acknowledging")
    message: str = Field(default="", description="Acknowledgement message")


class ResolveRequest(BaseModel):
    """Request to resolve an incident."""

    actor: str | None = Field(None, description="Who is resolving (null for auto)")
    message: str = Field(default="", description="Resolution message")


class EscalationStats(BaseModel):
    """Escalation statistics."""

    total_incidents: int = Field(default=0, description="Total incidents")
    by_state: dict[str, int] = Field(default_factory=dict, description="Count by state")
    active_count: int = Field(default=0, description="Active (non-resolved) incidents")
    total_policies: int = Field(default=0, description="Total policies")
    avg_resolution_time_minutes: float | None = Field(
        None,
        description="Average resolution time in minutes",
    )


# =============================================================================
# Combined Stats
# =============================================================================


class AdvancedNotificationStats(BaseModel):
    """Combined statistics for all advanced notification features."""

    routing: dict[str, int] = Field(
        default_factory=dict,
        description="Routing statistics",
    )
    deduplication: DeduplicationStats = Field(
        default_factory=DeduplicationStats,
        description="Deduplication statistics",
    )
    throttling: ThrottlingStats = Field(
        default_factory=ThrottlingStats,
        description="Throttling statistics",
    )
    escalation: EscalationStats = Field(
        default_factory=EscalationStats,
        description="Escalation statistics",
    )
