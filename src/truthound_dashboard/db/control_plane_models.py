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
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


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


class Role(Base, UUIDMixin, TimestampMixin):
    """Simple role model with inline permission set."""

    __tablename__ = "roles"

    __table_args__ = (
        Index("idx_roles_name", "name", unique=True),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    permissions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    memberships: Mapped[list["Membership"]] = relationship(
        "Membership",
        back_populates="role",
        cascade="all, delete-orphan",
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
        return self.expires_at > datetime.utcnow()


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
