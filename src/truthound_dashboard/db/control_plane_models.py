"""Control-plane database models.

These models hold dashboard-native operational state while Truthound owns
the validation data-plane itself.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin
from truthound_dashboard.time import utc_now


class Workspace(Base, UUIDMixin, TimestampMixin):
    """Single-organization workspace boundary."""

    __tablename__ = "workspaces"

    __table_args__ = (
        Index("idx_workspaces_slug", "slug", unique=True),
        Index("idx_workspaces_default", "is_default"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    memberships: Mapped[list["Membership"]] = relationship(
        "Membership",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    saved_views: Mapped[list["SavedView"]] = relationship(
        "SavedView",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    artifact_records: Mapped[list["ArtifactRecord"]] = relationship(
        "ArtifactRecord",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(ArtifactRecord.created_at)",
    )
    secret_refs: Mapped[list["SecretRef"]] = relationship(
        "SecretRef",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="SecretRef.name.asc()",
    )
    teams: Mapped[list["Team"]] = relationship(
        "Team",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Team.name.asc()",
    )
    domains: Mapped[list["Domain"]] = relationship(
        "Domain",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Domain.name.asc()",
    )
    source_ownerships: Mapped[list["SourceOwnership"]] = relationship(
        "SourceOwnership",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    incident_queues: Mapped[list["IncidentQueue"]] = relationship(
        "IncidentQueue",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="IncidentQueue.name.asc()",
    )


class Role(Base, UUIDMixin, TimestampMixin):
    """Role model with normalized permission links."""

    __tablename__ = "roles"

    __table_args__ = (
        Index("idx_roles_name", "name", unique=True),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    memberships: Mapped[list["Membership"]] = relationship(
        "Membership",
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    permission_links: Mapped[list["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Permission(Base, UUIDMixin, TimestampMixin):
    """Permission registry entry."""

    __tablename__ = "permissions"

    __table_args__ = (
        Index("idx_permissions_key", "key", unique=True),
        Index("idx_permissions_category", "category"),
    )

    key: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    role_links: Mapped[list["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="permission",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class RolePermission(Base, UUIDMixin, TimestampMixin):
    """Association table between roles and permissions."""

    __tablename__ = "role_permissions"

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_permission"),
        Index("idx_role_permissions_role", "role_id"),
        Index("idx_role_permissions_permission", "permission_id"),
    )

    role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    permission_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[Role] = relationship("Role", back_populates="permission_links", lazy="selectin")
    permission: Mapped[Permission] = relationship(
        "Permission",
        back_populates="role_links",
        lazy="selectin",
    )


class User(Base, UUIDMixin, TimestampMixin):
    """Dashboard control-plane user."""

    __tablename__ = "users"

    __table_args__ = (
        Index("idx_users_email", "email", unique=True),
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    preferences: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    memberships: Mapped[list["Membership"]] = relationship(
        "Membership",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    saved_views: Mapped[list["SavedView"]] = relationship(
        "SavedView",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    queue_memberships: Mapped[list["IncidentQueueMembership"]] = relationship(
        "IncidentQueueMembership",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    team_memberships: Mapped[list["TeamMembership"]] = relationship(
        "TeamMembership",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    owned_sources: Mapped[list["SourceOwnership"]] = relationship(
        "SourceOwnership",
        back_populates="owner_user",
        lazy="selectin",
        foreign_keys="SourceOwnership.owner_user_id",
    )
    created_secret_refs: Mapped[list["SecretRef"]] = relationship(
        "SecretRef",
        back_populates="created_by_user",
        lazy="selectin",
        foreign_keys="SecretRef.created_by",
    )


class Membership(Base, UUIDMixin, TimestampMixin):
    """User membership within a workspace."""

    __tablename__ = "memberships"

    __table_args__ = (
        Index("idx_memberships_user_workspace", "user_id", "workspace_id", unique=True),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped[User] = relationship("User", back_populates="memberships", lazy="selectin")
    workspace: Mapped[Workspace] = relationship(
        "Workspace",
        back_populates="memberships",
        lazy="selectin",
    )
    role: Mapped[Role] = relationship("Role", back_populates="memberships", lazy="selectin")


class Session(Base, UUIDMixin, TimestampMixin):
    """Local control-plane session."""

    __tablename__ = "sessions"

    __table_args__ = (
        Index("idx_sessions_token_hash", "token_hash", unique=True),
        Index("idx_sessions_workspace", "workspace_id"),
    )

    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    auth_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    user: Mapped[User] = relationship("User", back_populates="sessions", lazy="selectin")
    workspace: Mapped[Workspace] = relationship(
        "Workspace",
        back_populates="sessions",
        lazy="selectin",
    )

    @property
    def is_active(self) -> bool:
        if self.revoked_at is not None:
            return False
        if self.expires_at is None:
            return True
        return self.expires_at > utc_now()


class SavedView(Base, UUIDMixin, TimestampMixin):
    """Reusable filters for list-heavy operational screens."""

    __tablename__ = "saved_views"

    __table_args__ = (
        Index("idx_saved_views_workspace_scope", "workspace_id", "scope"),
        Index("idx_saved_views_owner", "owner_id"),
    )

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    scope: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    filters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    workspace: Mapped[Workspace] = relationship(
        "Workspace",
        back_populates="saved_views",
        lazy="selectin",
    )
    owner: Mapped[User] = relationship("User", back_populates="saved_views", lazy="selectin")


class SecretRef(Base, UUIDMixin, TimestampMixin):
    """Encrypted secret reference stored in the dashboard control-plane."""

    __tablename__ = "secret_refs"

    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_secret_refs_workspace_name"),
        Index("idx_secret_refs_workspace", "workspace_id"),
        Index("idx_secret_refs_provider", "provider"),
        Index("idx_secret_refs_kind", "kind"),
    )

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="local-db")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(100), nullable=False)
    encrypted_value: Mapped[str] = mapped_column(Text, nullable=False)
    redacted_hint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    secret_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="secret_refs", lazy="selectin")
    created_by_user: Mapped[User | None] = relationship(
        "User",
        back_populates="created_secret_refs",
        lazy="selectin",
        foreign_keys=[created_by],
    )


class Team(Base, UUIDMixin, TimestampMixin):
    """Workspace-scoped operational team."""

    __tablename__ = "teams"

    __table_args__ = (
        UniqueConstraint("workspace_id", "slug", name="uq_teams_workspace_slug"),
        Index("idx_teams_workspace", "workspace_id"),
    )

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="teams", lazy="selectin")
    memberships: Mapped[list["TeamMembership"]] = relationship(
        "TeamMembership",
        back_populates="team",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    owned_sources: Mapped[list["SourceOwnership"]] = relationship(
        "SourceOwnership",
        back_populates="team",
        lazy="selectin",
    )


class TeamMembership(Base, UUIDMixin, TimestampMixin):
    """User membership inside a workspace team."""

    __tablename__ = "team_memberships"

    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_memberships_team_user"),
        Index("idx_team_memberships_team", "team_id"),
        Index("idx_team_memberships_user", "user_id"),
    )

    team_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    team: Mapped[Team] = relationship("Team", back_populates="memberships", lazy="selectin")
    user: Mapped[User] = relationship("User", back_populates="team_memberships", lazy="selectin")


class Domain(Base, UUIDMixin, TimestampMixin):
    """Workspace-scoped ownership domain."""

    __tablename__ = "domains"

    __table_args__ = (
        UniqueConstraint("workspace_id", "slug", name="uq_domains_workspace_slug"),
        Index("idx_domains_workspace", "workspace_id"),
    )

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="domains", lazy="selectin")
    owned_sources: Mapped[list["SourceOwnership"]] = relationship(
        "SourceOwnership",
        back_populates="domain",
        lazy="selectin",
    )


class SourceOwnership(Base, UUIDMixin, TimestampMixin):
    """Normalized ownership slice for a source."""

    __tablename__ = "source_ownerships"

    __table_args__ = (
        UniqueConstraint("source_id", name="uq_source_ownerships_source"),
        Index("idx_source_ownerships_workspace", "workspace_id"),
        Index("idx_source_ownerships_owner", "owner_user_id"),
        Index("idx_source_ownerships_team", "team_id"),
        Index("idx_source_ownerships_domain", "domain_id"),
    )

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    owner_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    team_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    domain_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("domains.id", ondelete="SET NULL"),
        nullable=True,
    )

    source: Mapped[Any] = relationship("Source", back_populates="ownership", lazy="selectin")
    workspace: Mapped[Workspace] = relationship(
        "Workspace",
        back_populates="source_ownerships",
        lazy="selectin",
    )
    owner_user: Mapped[User | None] = relationship(
        "User",
        back_populates="owned_sources",
        lazy="selectin",
        foreign_keys=[owner_user_id],
    )
    team: Mapped[Team | None] = relationship("Team", back_populates="owned_sources", lazy="selectin")
    domain: Mapped[Domain | None] = relationship("Domain", back_populates="owned_sources", lazy="selectin")


class ArtifactRecord(Base, UUIDMixin, TimestampMixin):
    """Canonical operational artifact record.

    Reports and static Data Docs are both persisted here so the dashboard can
    treat them as one artifact index instead of separate legacy products.
    """

    __tablename__ = "artifact_records"

    __table_args__ = (
        Index("idx_artifact_records_workspace", "workspace_id"),
        Index("idx_artifact_records_source", "source_id"),
        Index("idx_artifact_records_validation", "validation_id"),
        Index("idx_artifact_records_type", "artifact_type"),
        Index("idx_artifact_records_status", "status"),
        Index("idx_artifact_records_format", "format"),
        Index("idx_artifact_records_created", "created_at"),
        Index("idx_artifact_records_expires", "expires_at"),
    )

    workspace_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    validation_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("validations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False, default="report")
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="html")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    artifact_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    generation_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    downloaded_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_downloaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    locale: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    theme: Mapped[str | None] = mapped_column(String(50), nullable=True)

    workspace: Mapped[Workspace | None] = relationship(
        "Workspace",
        back_populates="artifact_records",
        lazy="selectin",
    )
    source: Mapped[Any | None] = relationship(
        "Source",
        back_populates="artifact_records",
        lazy="selectin",
    )
    validation: Mapped[Any | None] = relationship(
        "Validation",
        back_populates="artifact_records",
        lazy="selectin",
    )

    def increment_download(self) -> None:
        self.downloaded_count += 1
        self.last_downloaded_at = utc_now()

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return self.expires_at <= utc_now()


class IncidentQueue(Base, UUIDMixin, TimestampMixin):
    """Workspace-scoped incident queue."""

    __tablename__ = "incident_queues"

    __table_args__ = (
        UniqueConstraint("workspace_id", "slug", name="uq_incident_queues_workspace_slug"),
        Index("idx_incident_queues_workspace", "workspace_id"),
        Index("idx_incident_queues_default", "workspace_id", "is_default"),
    )

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    routing_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    workspace: Mapped[Workspace] = relationship(
        "Workspace",
        back_populates="incident_queues",
        lazy="selectin",
    )
    memberships: Mapped[list["IncidentQueueMembership"]] = relationship(
        "IncidentQueueMembership",
        back_populates="queue",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    incidents: Mapped[list[Any]] = relationship(
        "EscalationIncidentModel",
        back_populates="queue",
        lazy="selectin",
    )


class IncidentQueueMembership(Base, UUIDMixin, TimestampMixin):
    """User membership inside an incident queue."""

    __tablename__ = "incident_queue_memberships"

    __table_args__ = (
        UniqueConstraint("queue_id", "user_id", name="uq_incident_queue_membership"),
        Index("idx_incident_queue_membership_queue", "queue_id"),
        Index("idx_incident_queue_membership_user", "user_id"),
    )

    queue_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("incident_queues.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_default_responder: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    queue: Mapped[IncidentQueue] = relationship(
        "IncidentQueue",
        back_populates="memberships",
        lazy="selectin",
    )
    user: Mapped[User] = relationship("User", back_populates="queue_memberships", lazy="selectin")
