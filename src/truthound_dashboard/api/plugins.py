"""Registry-only plugin API surface."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.core.plugins.registry import plugin_registry
from truthound_dashboard.db.models import PluginStatus as DBPluginStatus
from truthound_dashboard.db.models import PluginType as DBPluginType
from truthound_dashboard.schemas.plugins import (
    DependencyGraphNode,
    DependencyGraphResponse,
    DependencyInfo,
    DependencyResolutionRequest,
    DependencyResolutionResponse,
    DocumentationRenderRequest,
    DocumentationRenderResponse,
    MarketplaceSearchRequest,
    MarketplaceStats,
    PluginInstallRequest,
    PluginInstallResponse,
    PluginLifecycleEvent,
    PluginLifecycleResponse,
    PluginListResponse,
    PluginResponse,
    PluginState,
    PluginStatus,
    PluginTransitionRequest,
    PluginTransitionResponse,
    PluginType,
    PluginUninstallRequest,
    PluginUninstallResponse,
    PluginUpdateCheckResponse,
)
from .deps import get_session
from truthound_dashboard.time import utc_now

router = APIRouter()
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _map_lifecycle_state(plugin: object) -> PluginState:
    if getattr(plugin, "is_enabled", False):
        return PluginState.ACTIVE
    if getattr(plugin, "status", "available") in {"installed", "disabled"}:
        return PluginState.LOADED
    return PluginState.DISCOVERED


@router.get("/plugins", response_model=PluginListResponse)
async def list_plugins(
    session: SessionDep,
    type: PluginType | None = None,
    status: PluginStatus | None = None,
    search: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> PluginListResponse:
    db_type = DBPluginType(type.value) if type else None
    db_status = DBPluginStatus(status.value) if status else None
    plugins, total = await plugin_registry.list_plugins(
        session=session,
        plugin_type=db_type,
        status=db_status,
        search=search,
        offset=offset,
        limit=limit,
    )
    return PluginListResponse(
        data=[PluginResponse.from_model(plugin) for plugin in plugins],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/plugins/stats", response_model=MarketplaceStats)
async def get_marketplace_stats(session: SessionDep) -> MarketplaceStats:
    stats = await plugin_registry.get_statistics(session)
    return MarketplaceStats(
        total_plugins=stats["total_plugins"],
        total_validators=stats["total_validators"],
        total_reporters=stats["total_reporters"],
        total_installs=0,
        categories=[],
        featured_plugins=[],
        popular_plugins=[],
        recent_plugins=[],
    )


@router.post("/plugins/search", response_model=PluginListResponse)
async def search_plugins(
    session: SessionDep,
    request: MarketplaceSearchRequest,
) -> PluginListResponse:
    db_type = DBPluginType(request.types[0].value) if request.types and len(request.types) == 1 else None
    plugins, total = await plugin_registry.list_plugins(
        session=session,
        plugin_type=db_type,
        search=request.query,
        offset=request.offset,
        limit=request.limit,
    )
    return PluginListResponse(
        data=[PluginResponse.from_model(plugin) for plugin in plugins],
        total=total,
        offset=request.offset,
        limit=request.limit,
    )


@router.get("/plugins/{plugin_id}", response_model=PluginResponse)
async def get_plugin(
    session: SessionDep,
    plugin_id: str,
) -> PluginResponse:
    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if plugin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found")
    return PluginResponse.from_model(plugin)


@router.post("/plugins/{plugin_id}/install", response_model=PluginInstallResponse)
async def install_plugin(
    session: SessionDep,
    plugin_id: str,
    request: PluginInstallRequest | None = None,
) -> PluginInstallResponse:
    try:
        plugin = await plugin_registry.install_plugin(
            session=session,
            plugin_id=plugin_id,
            enable=request.enable_after_install if request else True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return PluginInstallResponse(
        success=True,
        plugin_id=plugin.id,
        installed_version=plugin.installed_version or plugin.version,
        message=f"Installed {plugin.display_name}",
        warnings=[],
    )


@router.post("/plugins/{plugin_id}/uninstall", response_model=PluginUninstallResponse)
async def uninstall_plugin(
    session: SessionDep,
    plugin_id: str,
    request: PluginUninstallRequest | None = None,
) -> PluginUninstallResponse:
    try:
        await plugin_registry.uninstall_plugin(
            session=session,
            plugin_id=plugin_id,
            remove_data=request.remove_data if request else False,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return PluginUninstallResponse(
        success=True,
        plugin_id=plugin_id,
        message="Plugin uninstalled",
    )


@router.post("/plugins/{plugin_id}/enable", response_model=PluginResponse)
async def enable_plugin(
    session: SessionDep,
    plugin_id: str,
) -> PluginResponse:
    try:
        plugin = await plugin_registry.enable_plugin(session=session, plugin_id=plugin_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PluginResponse.from_model(plugin)


@router.post("/plugins/{plugin_id}/disable", response_model=PluginResponse)
async def disable_plugin(
    session: SessionDep,
    plugin_id: str,
) -> PluginResponse:
    try:
        plugin = await plugin_registry.disable_plugin(session=session, plugin_id=plugin_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PluginResponse.from_model(plugin)


@router.get("/plugins/{plugin_id}/update-check", response_model=PluginUpdateCheckResponse)
async def check_plugin_update(
    session: SessionDep,
    plugin_id: str,
) -> PluginUpdateCheckResponse:
    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if plugin is None:
        raise HTTPException(status_code=404, detail="Plugin not found")
    latest_version = plugin.latest_version or plugin.version
    return PluginUpdateCheckResponse(
        plugin_id=plugin.id,
        current_version=plugin.installed_version or plugin.version,
        latest_version=latest_version,
        update_available=latest_version != (plugin.installed_version or plugin.version),
        changelog=plugin.changelog,
        breaking_changes=False,
        release_notes=plugin.changelog,
    )


@router.get("/plugins/{plugin_id}/dependencies", response_model=DependencyGraphResponse)
async def get_plugin_dependencies(
    session: SessionDep,
    plugin_id: str,
) -> DependencyGraphResponse:
    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if plugin is None:
        raise HTTPException(status_code=404, detail="Plugin not found")

    dependencies = [
        DependencyInfo(
            plugin_id=dependency.get("plugin_id", ""),
            version_constraint=dependency.get("version_constraint", "*"),
            dependency_type="optional" if dependency.get("optional") else "required",
            resolved_version=None,
            is_installed=False,
            is_satisfied=False,
        )
        for dependency in (plugin.dependencies or [])
    ]
    return DependencyGraphResponse(
        root_plugin_id=plugin.id,
        nodes=[
            DependencyGraphNode(
                plugin_id=plugin.id,
                version=plugin.version,
                dependencies=dependencies,
                dependents=[],
                depth=0,
            )
        ],
        has_cycles=False,
        cycle_path=None,
        install_order=[plugin.id],
        total_dependencies=len(dependencies),
    )


@router.post("/plugins/dependencies/resolve", response_model=DependencyResolutionResponse)
async def resolve_plugin_dependencies(
    session: SessionDep,
    request: DependencyResolutionRequest,
) -> DependencyResolutionResponse:
    resolved: list[DependencyInfo] = []
    unresolved: list[DependencyInfo] = []
    install_order: list[str] = []

    for plugin_id in request.plugin_ids:
        plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
        if plugin is None:
            unresolved.append(
                DependencyInfo(
                    plugin_id=plugin_id,
                    version_constraint="*",
                    dependency_type="required",
                    resolved_version=None,
                    is_installed=False,
                    is_satisfied=False,
                )
            )
            continue
        install_order.append(plugin_id)
        for dependency in plugin.dependencies or []:
            resolved.append(
                DependencyInfo(
                    plugin_id=dependency.get("plugin_id", ""),
                    version_constraint=dependency.get("version_constraint", "*"),
                    dependency_type="optional" if dependency.get("optional") else "required",
                    resolved_version=None,
                    is_installed=False,
                    is_satisfied=False,
                )
            )

    return DependencyResolutionResponse(
        success=len(unresolved) == 0,
        resolved=resolved,
        unresolved=unresolved,
        conflicts=[],
        install_order=install_order,
        error=None if len(unresolved) == 0 else "Some plugins could not be resolved",
    )


@router.post("/plugins/docs/render", response_model=DocumentationRenderResponse)
async def render_plugin_documentation(
    session: SessionDep,
    request: DocumentationRenderRequest,
) -> DocumentationRenderResponse:
    plugin = await plugin_registry.get_plugin(session, plugin_id=request.plugin_id)
    if plugin is None:
        raise HTTPException(status_code=404, detail="Plugin not found")

    content = plugin.readme or plugin.changelog or plugin.description or ""
    if request.format == "json":
        content = (
            '{'
            f'"plugin_id":"{plugin.id}",'
            f'"display_name":"{plugin.display_name}",'
            f'"description":"{plugin.description}"'
            '}'
        )

    return DocumentationRenderResponse(
        plugin_id=plugin.id,
        format=request.format,
        content=content,
        generation_time_ms=0,
    )


@router.get("/plugins/{plugin_id}/lifecycle", response_model=PluginLifecycleResponse)
async def get_plugin_lifecycle(
    session: SessionDep,
    plugin_id: str,
) -> PluginLifecycleResponse:
    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if plugin is None:
        raise HTTPException(status_code=404, detail="Plugin not found")

    current_state = _map_lifecycle_state(plugin)
    return PluginLifecycleResponse(
        plugin_id=plugin.id,
        current_state=current_state,
        can_activate=current_state in {PluginState.LOADED, PluginState.DISCOVERED},
        can_deactivate=current_state == PluginState.ACTIVE,
        can_reload=current_state in {PluginState.ACTIVE, PluginState.LOADED},
        can_upgrade=bool(plugin.latest_version and plugin.latest_version != plugin.version),
        recent_events=[
            PluginLifecycleEvent(
                plugin_id=plugin.id,
                from_state=current_state,
                to_state=current_state,
                trigger="observed",
                timestamp=utc_now(),
                metadata={},
            )
        ],
    )


@router.post("/plugins/{plugin_id}/lifecycle", response_model=PluginTransitionResponse)
async def transition_plugin_lifecycle(
    session: SessionDep,
    plugin_id: str,
    request: PluginTransitionRequest,
) -> PluginTransitionResponse:
    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if plugin is None:
        raise HTTPException(status_code=404, detail="Plugin not found")

    previous_state = _map_lifecycle_state(plugin)
    try:
        if request.target_state == PluginState.ACTIVE:
            plugin = await plugin_registry.enable_plugin(session=session, plugin_id=plugin_id)
        elif request.target_state in {PluginState.UNLOADED, PluginState.LOADED}:
            plugin = await plugin_registry.disable_plugin(session=session, plugin_id=plugin_id)
        else:
            raise HTTPException(status_code=400, detail="Unsupported lifecycle transition")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return PluginTransitionResponse(
        success=True,
        plugin_id=plugin.id,
        from_state=previous_state,
        to_state=_map_lifecycle_state(plugin),
        message="Lifecycle updated",
        error=None,
    )
