"""Dashboard-native control-plane services.

Truthound owns validation semantics. The dashboard owns user/workspace/session
state, reusable views, and operational aggregates.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from truthound_dashboard.config import get_settings
from truthound_dashboard.db import Membership, Role, SavedView, Session, User, Workspace
from truthound_dashboard.db.models import EscalationIncidentModel, GeneratedReport, Source


DEFAULT_WORKSPACE_SLUG = "default"
DEFAULT_USER_EMAIL = "admin@truthound.local"
SESSION_TTL_HOURS = 12

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": [
        "sources:read",
        "sources:write",
        "validations:read",
        "validations:write",
        "incidents:read",
        "incidents:write",
        "reports:read",
        "reports:write",
        "plugins:read",
        "plugins:write",
        "observability:read",
        "views:write",
        "users:read",
        "roles:read",
    ],
    "operator": [
        "sources:read",
        "sources:write",
        "validations:read",
        "validations:write",
        "incidents:read",
        "incidents:write",
        "reports:read",
        "reports:write",
        "plugins:read",
        "observability:read",
        "views:write",
    ],
    "viewer": [
        "sources:read",
        "validations:read",
        "incidents:read",
        "reports:read",
        "plugins:read",
        "observability:read",
    ],
}


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass
class ControlPlaneContext:
    """Resolved dashboard control-plane identity."""

    user: User
    workspace: Workspace
    role: Role
    session: Session | None = None


class ControlPlaneService:
    """Bootstrap and query control-plane state."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ensure_bootstrap_state(self) -> ControlPlaneContext:
        """Ensure the single-org bootstrap entities exist."""
        workspace = await self._ensure_default_workspace()
        roles = await self._ensure_roles()
        user = await self._ensure_default_user()
        role = roles["admin"]
        await self._ensure_membership(user_id=user.id, workspace_id=workspace.id, role_id=role.id)
        return ControlPlaneContext(user=user, workspace=workspace, role=role)

    async def _ensure_default_workspace(self) -> Workspace:
        result = await self.session.execute(
            select(Workspace).where(
                or_(Workspace.is_default == True, Workspace.slug == DEFAULT_WORKSPACE_SLUG)  # noqa: E712
            )
        )
        workspace = result.scalars().first()
        if workspace is not None:
            return workspace

        workspace = Workspace(
            name="Default Workspace",
            slug=DEFAULT_WORKSPACE_SLUG,
            description="Default operational workspace for Truthound Dashboard",
            is_default=True,
            is_active=True,
        )
        self.session.add(workspace)
        await self.session.flush()
        return workspace

    async def _ensure_roles(self) -> dict[str, Role]:
        existing = {
            role.name: role
            for role in (
                await self.session.execute(select(Role).where(Role.name.in_(list(ROLE_PERMISSIONS.keys()))))
            ).scalars()
        }

        for name, permissions in ROLE_PERMISSIONS.items():
            role = existing.get(name)
            if role is None:
                role = Role(
                    name=name,
                    description=f"System {name} role",
                    permissions=permissions,
                    is_system=True,
                )
                self.session.add(role)
                await self.session.flush()
                existing[name] = role
            elif role.permissions != permissions:
                role.permissions = permissions

        return existing

    async def _ensure_default_user(self) -> User:
        result = await self.session.execute(select(User).where(User.email == DEFAULT_USER_EMAIL))
        user = result.scalar_one_or_none()
        if user is not None:
            return user

        user = User(
            email=DEFAULT_USER_EMAIL,
            display_name="Truthound Admin",
            is_active=True,
            is_system=True,
            preferences={"theme": "system"},
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def _ensure_membership(self, *, user_id: str, workspace_id: str, role_id: str) -> Membership:
        result = await self.session.execute(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.workspace_id == workspace_id,
            )
        )
        membership = result.scalar_one_or_none()
        if membership is not None:
            if membership.role_id != role_id:
                membership.role_id = role_id
            membership.is_default = True
            return membership

        membership = Membership(
            user_id=user_id,
            workspace_id=workspace_id,
            role_id=role_id,
            is_default=True,
        )
        self.session.add(membership)
        await self.session.flush()
        return membership

    async def resolve_context(self, token: str | None = None) -> ControlPlaneContext:
        """Resolve the active context from a session token or bootstrap fallback."""
        settings = get_settings()
        if token:
            token_hash = _hash_value(token)
            result = await self.session.execute(
                select(Session)
                .options(
                    selectinload(Session.user),
                    selectinload(Session.workspace),
                )
                .where(Session.token_hash == token_hash)
                .where(Session.revoked_at.is_(None))
            )
            session_obj = result.scalar_one_or_none()
            if session_obj is not None and session_obj.is_active:
                membership = await self._get_membership(
                    user_id=session_obj.user_id,
                    workspace_id=session_obj.workspace_id,
                )
                if membership is None:
                    raise PermissionError("Session is not attached to an active workspace")
                session_obj.last_seen_at = datetime.utcnow()
                return ControlPlaneContext(
                    user=session_obj.user,
                    workspace=session_obj.workspace,
                    role=membership.role,
                    session=session_obj,
                )

        if settings.auth_enabled:
            raise PermissionError("Authentication required")

        return await self.ensure_bootstrap_state()

    async def _get_membership(self, *, user_id: str, workspace_id: str) -> Membership | None:
        result = await self.session.execute(
            select(Membership)
            .options(selectinload(Membership.role))
            .where(Membership.user_id == user_id, Membership.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()


class AuthService(ControlPlaneService):
    """Local session management."""

    async def get_or_create_session(self, token: str | None = None) -> tuple[str | None, ControlPlaneContext]:
        """Return current session context, auto-creating one when auth is disabled."""
        try:
            context = await self.resolve_context(token)
            return token, context
        except PermissionError:
            if get_settings().auth_enabled:
                raise
            context = await self.ensure_bootstrap_state()
            session_obj, created_token = await self._create_session(context)
            return created_token, ControlPlaneContext(
                user=context.user,
                workspace=context.workspace,
                role=context.role,
                session=session_obj,
            )

    async def login(self, *, password: str | None = None, workspace_id: str | None = None) -> tuple[str, ControlPlaneContext]:
        """Create a new local session."""
        settings = get_settings()
        context = await self.ensure_bootstrap_state()
        if settings.auth_enabled and password != settings.auth_password:
            raise PermissionError("Invalid credentials")

        if workspace_id and workspace_id != context.workspace.id:
            result = await self.session.execute(select(Workspace).where(Workspace.id == workspace_id))
            workspace = result.scalar_one_or_none()
            if workspace is None:
                raise ValueError("Workspace not found")
            membership = await self._get_membership(user_id=context.user.id, workspace_id=workspace.id)
            if membership is None:
                raise PermissionError("Workspace access denied")
            context = ControlPlaneContext(
                user=context.user,
                workspace=workspace,
                role=membership.role,
            )

        session_obj, token = await self._create_session(context)
        return token, ControlPlaneContext(
            user=context.user,
            workspace=context.workspace,
            role=context.role,
            session=session_obj,
        )

    async def logout(self, token: str | None) -> None:
        """Revoke a session token."""
        if not token:
            return
        token_hash = _hash_value(token)
        result = await self.session.execute(select(Session).where(Session.token_hash == token_hash))
        session_obj = result.scalar_one_or_none()
        if session_obj is not None:
            session_obj.revoked_at = datetime.utcnow()
            session_obj.last_seen_at = datetime.utcnow()

    async def _create_session(self, context: ControlPlaneContext) -> tuple[Session, str]:
        token = secrets.token_urlsafe(32)
        session_obj = Session(
            token_hash=_hash_value(token),
            user_id=context.user.id,
            workspace_id=context.workspace.id,
            expires_at=datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS),
            last_seen_at=datetime.utcnow(),
            auth_metadata={"provider": "local"},
        )
        self.session.add(session_obj)
        await self.session.flush()
        await self.session.refresh(session_obj)
        return session_obj, token


class SavedViewService(ControlPlaneService):
    """CRUD for reusable list filters."""

    async def list_views(
        self,
        *,
        workspace_id: str,
        scope: str | None = None,
        owner_id: str | None = None,
    ) -> list[SavedView]:
        query = (
            select(SavedView)
            .options(selectinload(SavedView.owner))
            .where(SavedView.workspace_id == workspace_id)
            .order_by(SavedView.scope.asc(), SavedView.name.asc())
        )
        if scope:
            query = query.where(SavedView.scope == scope)
        if owner_id:
            query = query.where(SavedView.owner_id == owner_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_view(
        self,
        *,
        workspace_id: str,
        owner_id: str,
        scope: str,
        name: str,
        filters: dict[str, Any],
        description: str | None = None,
        is_default: bool = False,
    ) -> SavedView:
        view = SavedView(
            workspace_id=workspace_id,
            owner_id=owner_id,
            scope=scope,
            name=name,
            description=description,
            filters=filters,
            is_default=is_default,
        )
        self.session.add(view)
        await self.session.flush()
        await self.session.refresh(view)
        return view

    async def update_view(
        self,
        *,
        view_id: str,
        workspace_id: str,
        name: str | None = None,
        description: str | None = None,
        filters: dict[str, Any] | None = None,
        is_default: bool | None = None,
    ) -> SavedView | None:
        result = await self.session.execute(
            select(SavedView).where(SavedView.id == view_id, SavedView.workspace_id == workspace_id)
        )
        view = result.scalar_one_or_none()
        if view is None:
            return None
        if name is not None:
            view.name = name
        if description is not None:
            view.description = description
        if filters is not None:
            view.filters = filters
        if is_default is not None:
            view.is_default = is_default
        await self.session.flush()
        await self.session.refresh(view)
        return view

    async def delete_view(self, *, view_id: str, workspace_id: str) -> bool:
        result = await self.session.execute(
            select(SavedView).where(SavedView.id == view_id, SavedView.workspace_id == workspace_id)
        )
        view = result.scalar_one_or_none()
        if view is None:
            return False
        await self.session.delete(view)
        return True


class OverviewService(ControlPlaneService):
    """Fleet overview aggregates for the dashboard homepage."""

    async def get_overview(self, *, workspace_id: str) -> dict[str, Any]:
        source_query = select(Source).where(
            or_(Source.workspace_id == workspace_id, Source.workspace_id.is_(None))
        )
        source_result = await self.session.execute(source_query)
        sources = list(source_result.scalars().all())

        total_sources = len(sources)
        active_sources = len([source for source in sources if source.is_active])
        healthy_sources = len(
            [source for source in sources if source.latest_validation and source.latest_validation.status == "success"]
        )
        unhealthy_sources = len(
            [
                source
                for source in sources
                if source.latest_validation and source.latest_validation.status in {"failed", "error"}
            ]
        )

        incident_total = (
            await self.session.scalar(select(func.count()).select_from(EscalationIncidentModel))
        ) or 0
        incident_active = (
            await self.session.scalar(
                select(func.count())
                .select_from(EscalationIncidentModel)
                .where(EscalationIncidentModel.state != "resolved")
            )
        ) or 0

        artifact_total = (
            await self.session.scalar(
                select(func.count())
                .select_from(GeneratedReport)
                .where(or_(GeneratedReport.workspace_id == workspace_id, GeneratedReport.workspace_id.is_(None)))
            )
        ) or 0
        artifact_failed = (
            await self.session.scalar(
                select(func.count())
                .select_from(GeneratedReport)
                .where(
                    or_(GeneratedReport.workspace_id == workspace_id, GeneratedReport.workspace_id.is_(None)),
                    GeneratedReport.status == "failed",
                )
            )
        ) or 0

        views = await SavedViewService(self.session).list_views(workspace_id=workspace_id)

        return {
            "sources": {
                "total": total_sources,
                "active": active_sources,
                "healthy": healthy_sources,
                "unhealthy": unhealthy_sources,
            },
            "incidents": {
                "total": incident_total,
                "active": incident_active,
            },
            "artifacts": {
                "total": artifact_total,
                "failed": artifact_failed,
            },
            "saved_views": [
                {
                    "id": view.id,
                    "name": view.name,
                    "scope": view.scope,
                    "description": view.description,
                    "is_default": view.is_default,
                    "owner_name": view.owner.display_name if view.owner else None,
                }
                for view in views[:8]
            ],
        }
