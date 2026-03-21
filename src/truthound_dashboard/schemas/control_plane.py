"""Schemas for dashboard-native control-plane APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from .base import BaseSchema, IDMixin, ListResponseWrapper, TimestampMixin


class RoleResponse(BaseSchema, IDMixin, TimestampMixin):
    name: str
    description: str | None = None
    permissions: list[str] = Field(default_factory=list)
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


class SavedViewBase(BaseSchema):
    scope: str = Field(..., min_length=1, max_length=100)
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


class OverviewSavedView(BaseSchema):
    id: str
    name: str
    scope: str
    description: str | None = None
    is_default: bool = False
    owner_name: str | None = None


class OverviewResponse(BaseSchema):
    sources: OverviewSlice
    incidents: OverviewSlice
    artifacts: OverviewSlice
    saved_views: list[OverviewSavedView] = Field(default_factory=list)
