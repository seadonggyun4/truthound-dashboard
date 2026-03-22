"""Dashboard-native control-plane services."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from truthound_dashboard.config import get_settings
from truthound_dashboard.db import Membership, Role, SavedView, Session, User, Workspace
from truthound_dashboard.db import RolePermission

from .authz import AuthorizationService
from truthound_dashboard.time import utc_now

DEFAULT_WORKSPACE_SLUG = "default"
DEFAULT_USER_EMAIL = "admin@truthound.local"
SESSION_TTL_HOURS = 12
ALLOWED_SAVED_VIEW_SCOPES = {"sources", "alerts", "artifacts", "history"}


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass
class ControlPlaneContext:
    """Resolved dashboard control-plane identity."""

    user: User
    workspace: Workspace
    role: Role
    session: Session | None = None
    permission_keys: tuple[str, ...] = field(default_factory=tuple)


class ControlPlaneService:
    """Bootstrap and query control-plane state."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.authz = AuthorizationService(session)

    async def ensure_bootstrap_state(self) -> ControlPlaneContext:
        workspace = await self._ensure_default_workspace()
        roles = await self.authz.ensure_seeded()
        user = await self._ensure_default_user()
        role = roles["admin"]
        await self._ensure_membership(user_id=user.id, workspace_id=workspace.id, role_id=role.id)
        permission_keys = tuple(self.authz.permission_keys_for_role(role))
        return ControlPlaneContext(
            user=user,
            workspace=workspace,
            role=role,
            permission_keys=permission_keys,
        )

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
                session_obj.last_seen_at = utc_now()
                permission_keys = tuple(self.authz.permission_keys_for_role(membership.role))
                return ControlPlaneContext(
                    user=session_obj.user,
                    workspace=session_obj.workspace,
                    role=membership.role,
                    session=session_obj,
                    permission_keys=permission_keys,
                )

        if settings.auth_enabled:
            raise PermissionError("Authentication required")

        return await self.ensure_bootstrap_state()

    async def _get_membership(self, *, user_id: str, workspace_id: str) -> Membership | None:
        result = await self.session.execute(
            select(Membership)
            .options(
                selectinload(Membership.role)
                .selectinload(Role.permission_links)
                .selectinload(RolePermission.permission)
            )
            .where(Membership.user_id == user_id, Membership.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()


class AuthService(ControlPlaneService):
    """Local session management."""

    async def get_or_create_session(self, token: str | None = None) -> tuple[str | None, ControlPlaneContext]:
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
                permission_keys=context.permission_keys,
            )

    async def login(
        self,
        *,
        password: str | None = None,
        workspace_id: str | None = None,
    ) -> tuple[str, ControlPlaneContext]:
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
            permission_keys = tuple(self.authz.permission_keys_for_role(membership.role))
            context = ControlPlaneContext(
                user=context.user,
                workspace=workspace,
                role=membership.role,
                permission_keys=permission_keys,
            )

        session_obj, token = await self._create_session(context)
        return token, ControlPlaneContext(
            user=context.user,
            workspace=context.workspace,
            role=context.role,
            session=session_obj,
            permission_keys=context.permission_keys,
        )

    async def logout(self, token: str | None) -> None:
        if not token:
            return
        token_hash = _hash_value(token)
        result = await self.session.execute(select(Session).where(Session.token_hash == token_hash))
        session_obj = result.scalar_one_or_none()
        if session_obj is not None:
            session_obj.revoked_at = utc_now()
            session_obj.last_seen_at = utc_now()

    async def _create_session(self, context: ControlPlaneContext) -> tuple[Session, str]:
        token = secrets.token_urlsafe(32)
        session_obj = Session(
            token_hash=_hash_value(token),
            user_id=context.user.id,
            workspace_id=context.workspace.id,
            expires_at=utc_now() + timedelta(hours=SESSION_TTL_HOURS),
            last_seen_at=utc_now(),
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
        if scope is not None and scope not in ALLOWED_SAVED_VIEW_SCOPES:
            return []
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
        if scope not in ALLOWED_SAVED_VIEW_SCOPES:
            raise ValueError(f"Unsupported saved view scope: {scope}")
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
