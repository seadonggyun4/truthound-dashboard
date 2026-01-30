"""Schedule management schemas.

Schemas for validation schedule request/response.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .base import IDMixin, TimestampMixin


class ScheduleBase(BaseModel):
    """Base schedule fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Schedule name")
    cron_expression: str = Field(
        ...,
        description="Cron expression (5 fields: min hour day month weekday)",
        examples=["0 8 * * *", "*/30 * * * *", "0 0 * * 0"],
    )
    notify_on_failure: bool = Field(True, description="Send notification on failure")


class ScheduleCreate(ScheduleBase):
    """Request body for creating a schedule."""

    source_id: str = Field(..., description="Source ID to schedule")
    trigger_type: str = Field("cron", description="Trigger type (cron, interval, data_change, composite, event, webhook, manual)")
    trigger_config: dict[str, Any] | None = Field(None, description="Trigger-specific configuration")
    config: dict[str, Any] | None = Field(
        None,
        description="Additional configuration (validators, schema_path, etc.)",
    )


class ScheduleUpdate(BaseModel):
    """Request body for updating a schedule."""

    name: str | None = Field(None, min_length=1, max_length=255)
    cron_expression: str | None = Field(None)
    trigger_type: str | None = Field(None, description="Trigger type")
    trigger_config: dict[str, Any] | None = Field(None, description="Trigger-specific configuration")
    notify_on_failure: bool | None = Field(None)
    config: dict[str, Any] | None = Field(None)


class ScheduleResponse(BaseModel, IDMixin, TimestampMixin):
    """Response for a schedule."""

    name: str = Field(..., description="Schedule name")
    source_id: str = Field(..., description="Source ID")
    cron_expression: str = Field(..., description="Cron expression")
    trigger_type: str = Field("cron", description="Trigger type")
    trigger_config: dict[str, Any] | None = Field(None, description="Trigger-specific configuration")
    is_active: bool = Field(..., description="Whether schedule is active")
    notify_on_failure: bool = Field(..., description="Notify on failure")
    last_run_at: str | None = Field(None, description="Last run timestamp (ISO)")
    next_run_at: str | None = Field(None, description="Next scheduled run (ISO)")
    config: dict[str, Any] | None = Field(None, description="Configuration")

    # Optional source info
    source_name: str | None = Field(None, description="Source name")


class ScheduleListItem(BaseModel, IDMixin, TimestampMixin):
    """List item for schedules."""

    name: str
    source_id: str
    cron_expression: str
    trigger_type: str = "cron"
    trigger_config: dict[str, Any] | None = None
    is_active: bool
    notify_on_failure: bool
    last_run_at: str | None = None
    next_run_at: str | None = None
    source_name: str | None = None


class ScheduleListResponse(BaseModel):
    """Paginated list response for schedules."""

    data: list[ScheduleListItem] = Field(default_factory=list)
    total: int = 0
    offset: int = 0
    limit: int = 100


class ScheduleActionResponse(BaseModel):
    """Response for schedule actions (pause, resume, run)."""

    message: str = Field(..., description="Action result message")
    schedule: ScheduleResponse | None = Field(None, description="Updated schedule")
