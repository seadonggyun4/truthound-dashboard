"""Control-plane API endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy import select

from truthound_dashboard.db import Role, User, Workspace
from truthound_dashboard.schemas.control_plane import (
    OverviewResponse,
    RoleResponse,
    SavedViewCreate,
    SavedViewListResponse,
    SavedViewResponse,
    SavedViewUpdate,
    SessionCreateRequest,
    SessionResponse,
    UserResponse,
    WorkspaceResponse,
)

from .deps import (
    SessionDep,
    get_auth_service,
    get_control_plane_context,
    get_overview_service,
    get_saved_view_service,
)

router = APIRouter()


def _workspace_response(workspace: Workspace) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(workspace)


def _role_response(role: Role) -> RoleResponse:
    return RoleResponse.model_validate(role)


def _user_response(user: User) -> UserResponse:
    return UserResponse.model_validate(user)


def _saved_view_response(view: object) -> SavedViewResponse:
    return SavedViewResponse(
        id=view.id,
        scope=view.scope,
        name=view.name,
        description=view.description,
        filters=view.filters,
        is_default=view.is_default,
        owner_id=view.owner_id,
        workspace_id=view.workspace_id,
        owner_name=view.owner.display_name if getattr(view, "owner", None) else None,
        created_at=view.created_at,
        updated_at=view.updated_at,
    )


@router.get("/auth/session", response_model=SessionResponse)
async def get_session(
    auth_service: Annotated[object, Depends(get_auth_service)],
    x_truthound_session: Annotated[str | None, Header(alias="X-Truthound-Session")] = None,
) -> SessionResponse:
    """Get or bootstrap the active session."""
    try:
        token, context = await auth_service.get_or_create_session(x_truthound_session)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return SessionResponse(
        token=token,
        expires_at=context.session.expires_at if context.session else None,
        user=_user_response(context.user),
        workspace=_workspace_response(context.workspace),
        role=_role_response(context.role),
    )


@router.post("/auth/session", response_model=SessionResponse)
async def create_session(
    payload: SessionCreateRequest,
    auth_service: Annotated[object, Depends(get_auth_service)],
) -> SessionResponse:
    """Create a local session."""
    try:
        token, context = await auth_service.login(
            password=payload.password,
            workspace_id=payload.workspace_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return SessionResponse(
        token=token,
        expires_at=context.session.expires_at if context.session else None,
        user=_user_response(context.user),
        workspace=_workspace_response(context.workspace),
        role=_role_response(context.role),
    )


@router.delete("/auth/session", response_model=dict[str, str])
async def delete_session(
    auth_service: Annotated[object, Depends(get_auth_service)],
    x_truthound_session: Annotated[str | None, Header(alias="X-Truthound-Session")] = None,
) -> dict[str, str]:
    """Revoke a session."""
    await auth_service.logout(x_truthound_session)
    return {"message": "Session revoked"}


@router.get("/me", response_model=SessionResponse)
async def get_me(
    context=Depends(get_control_plane_context),
) -> SessionResponse:
    """Get current user/workspace context."""
    return SessionResponse(
        token=None,
        expires_at=context.session.expires_at if context.session else None,
        user=_user_response(context.user),
        workspace=_workspace_response(context.workspace),
        role=_role_response(context.role),
    )


@router.get("/workspaces", response_model=list[WorkspaceResponse])
async def list_workspaces(
    session: SessionDep,
    auth_service: Annotated[object, Depends(get_auth_service)],
) -> list[WorkspaceResponse]:
    await auth_service.ensure_bootstrap_state()
    result = await session.execute(select(Workspace).order_by(Workspace.name.asc()))
    return [_workspace_response(workspace) for workspace in result.scalars().all()]


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    session: SessionDep,
    auth_service: Annotated[object, Depends(get_auth_service)],
) -> list[RoleResponse]:
    await auth_service.ensure_bootstrap_state()
    result = await session.execute(select(Role).order_by(Role.name.asc()))
    return [_role_response(role) for role in result.scalars().all()]


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    session: SessionDep,
    auth_service: Annotated[object, Depends(get_auth_service)],
) -> list[UserResponse]:
    await auth_service.ensure_bootstrap_state()
    result = await session.execute(select(User).order_by(User.display_name.asc()))
    return [_user_response(user) for user in result.scalars().all()]


@router.get("/views", response_model=SavedViewListResponse)
async def list_saved_views(
    service: Annotated[object, Depends(get_saved_view_service)],
    context=Depends(get_control_plane_context),
    scope: Annotated[str | None, Query()] = None,
) -> SavedViewListResponse:
    views = await service.list_views(
        workspace_id=context.workspace.id,
        scope=scope,
    )
    return SavedViewListResponse(
        data=[_saved_view_response(view) for view in views],
        total=len(views),
        offset=0,
        limit=len(views) or 100,
    )


@router.post("/views", response_model=SavedViewResponse, status_code=201)
async def create_saved_view(
    payload: SavedViewCreate,
    service: Annotated[object, Depends(get_saved_view_service)],
    context=Depends(get_control_plane_context),
) -> SavedViewResponse:
    view = await service.create_view(
        workspace_id=context.workspace.id,
        owner_id=context.user.id,
        scope=payload.scope,
        name=payload.name,
        description=payload.description,
        filters=payload.filters,
        is_default=payload.is_default,
    )
    return _saved_view_response(view)


@router.put("/views/{view_id}", response_model=SavedViewResponse)
async def update_saved_view(
    view_id: str,
    payload: SavedViewUpdate,
    service: Annotated[object, Depends(get_saved_view_service)],
    context=Depends(get_control_plane_context),
) -> SavedViewResponse:
    view = await service.update_view(
        view_id=view_id,
        workspace_id=context.workspace.id,
        name=payload.name,
        description=payload.description,
        filters=payload.filters,
        is_default=payload.is_default,
    )
    if view is None:
        raise HTTPException(status_code=404, detail="Saved view not found")
    return _saved_view_response(view)


@router.delete("/views/{view_id}", response_model=dict[str, str])
async def delete_saved_view(
    view_id: str,
    service: Annotated[object, Depends(get_saved_view_service)],
    context=Depends(get_control_plane_context),
) -> dict[str, str]:
    deleted = await service.delete_view(view_id=view_id, workspace_id=context.workspace.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Saved view not found")
    return {"message": "Saved view deleted"}


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    service: Annotated[object, Depends(get_overview_service)],
    context=Depends(get_control_plane_context),
) -> OverviewResponse:
    overview = await service.get_overview(workspace_id=context.workspace.id)
    return OverviewResponse.model_validate(overview)
