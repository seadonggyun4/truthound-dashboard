"""Schemas for dashboard-native control-plane APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from .base import BaseSchema, IDMixin, ListResponseWrapper, TimestampMixin


class RoleResponse(BaseSchema, IDMixin, TimestampMixin):
    name: str
    description: str | None = None
    permissions: list[str] = Field(default_factory=list)
    is_system: bool = True


class PermissionResponse(BaseSchema, IDMixin, TimestampMixin):
    key: str
    category: str
    description: str | None = None
    is_system: bool = True


class WorkspaceResponse(BaseSchema, IDMixin, TimestampMixin):
    name: str
    slug: str
    description: str | None = None
    is_default: bool = False
    is_active: bool = True


class UserResponse(BaseSchema, IDMixin, TimestampMixin):
    email: str
    display_name: str
    is_active: bool = True
    is_system: bool = False
    preferences: dict[str, Any] = Field(default_factory=dict)


class MembershipResponse(BaseSchema, IDMixin, TimestampMixin):
    user: UserResponse
    workspace: WorkspaceResponse
    role: RoleResponse
    is_default: bool = False


class SessionResponse(BaseSchema):
    token: str | None = None
    expires_at: datetime | None = None
    user: UserResponse
    workspace: WorkspaceResponse
    role: RoleResponse


class SessionCreateRequest(BaseSchema):
    password: str | None = None
    workspace_id: str | None = None


SavedViewScope = Literal["sources", "alerts", "artifacts", "history"]


class SavedViewBase(BaseSchema):
    scope: SavedViewScope
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    filters: dict[str, Any] = Field(default_factory=dict)
    is_default: bool = False


class SavedViewCreate(SavedViewBase):
    pass


class SavedViewUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    filters: dict[str, Any] | None = None
    is_default: bool | None = None


class SavedViewResponse(SavedViewBase, IDMixin, TimestampMixin):
    owner_id: str
    workspace_id: str
    owner_name: str | None = None


class SavedViewListResponse(ListResponseWrapper[SavedViewResponse]):
    pass


class OverviewSlice(BaseSchema):
    total: int = 0
    active: int | None = None
    healthy: int | None = None
    unhealthy: int | None = None
    failed: int | None = None
    fresh_24h: int | None = None
    stale: int | None = None
    unowned: int | None = None


class OverviewQueueBacklog(BaseSchema):
    queue_id: str
    queue_name: str
    count: int = 0


class OverviewAssigneeLoad(BaseSchema):
    user_id: str | None = None
    user_name: str
    count: int = 0


class OverviewArtifactTypeCount(BaseSchema):
    artifact_type: str
    count: int = 0


class OverviewWorkspaceSummary(BaseSchema):
    id: str
    name: str | None = None
    slug: str | None = None


class OverviewSavedView(BaseSchema):
    id: str
    name: str
    scope: SavedViewScope
    description: str | None = None
    is_default: bool = False
    owner_name: str | None = None


class OverviewNamedCount(BaseSchema):
    id: str | None = None
    name: str
    count: int = 0


class OverviewOwnershipFreshness(BaseSchema):
    ownership_type: str
    ownership_id: str | None = None
    ownership_name: str
    fresh_24h: int = 0
    stale: int = 0


class OverviewResponse(BaseSchema):
    workspace: OverviewWorkspaceSummary
    sources: OverviewSlice
    incidents: OverviewSlice
    artifacts: OverviewSlice
    incident_backlog: list[OverviewQueueBacklog] = Field(default_factory=list)
    assignee_workload: list[OverviewAssigneeLoad] = Field(default_factory=list)
    artifact_types: list[OverviewArtifactTypeCount] = Field(default_factory=list)
    sources_by_owner: list[OverviewNamedCount] = Field(default_factory=list)
    sources_by_team: list[OverviewNamedCount] = Field(default_factory=list)
    sources_by_domain: list[OverviewNamedCount] = Field(default_factory=list)
    artifact_freshness_by_ownership: list[OverviewOwnershipFreshness] = Field(default_factory=list)
    saved_views: list[OverviewSavedView] = Field(default_factory=list)
