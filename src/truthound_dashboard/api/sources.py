"""Sources API endpoints.

This module provides CRUD endpoints for managing data sources.

API Design: Direct Response Style
- Single resources return the resource directly
- List endpoints return PaginatedResponse with data, total, offset, limit
- Errors are handled via HTTPException
- Success is indicated by HTTP status codes (200, 201, 204)
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from pydantic import Field

from truthound_dashboard.schemas import (
    MessageResponse,
    SourceCreate,
    SourceCredentialUpdate,
    SourceListResponse,
    SourceOwnershipResponse,
    SourceOwnershipUpdate,
    SourceResponse,
    SourceTypesResponse,
    SourceUpdate,
    TestConnectionResponse,
)
from truthound_dashboard.schemas.base import BaseSchema

from .deps import SourceServiceDep, require_permission

router = APIRouter()


@router.get(
    "",
    response_model=SourceListResponse,
    summary="List sources",
    description="Get a paginated list of all data sources",
)
async def list_sources(
    service: SourceServiceDep,
    context=Depends(require_permission("sources:read")),
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum items to return")
    ] = 100,
    active_only: Annotated[
        bool, Query(description="Only return active sources")
    ] = True,
    saved_view_id: Annotated[str | None, Query(description="Apply saved view filters")] = None,
    search: Annotated[str | None, Query(description="Search by source name or description")] = None,
    status: Annotated[str | None, Query(description="Source status filter (active/inactive)")] = None,
    owner_user_id: Annotated[str | None, Query(description="Filter by owner user ID")] = None,
    team_id: Annotated[str | None, Query(description="Filter by team ID")] = None,
    domain_id: Annotated[str | None, Query(description="Filter by domain ID")] = None,
) -> SourceListResponse:
    """List all data sources with pagination.

    Args:
        service: Injected source service.
        offset: Number of items to skip.
        limit: Maximum items to return.
        active_only: Filter to active sources only.

    Returns:
        Paginated list of sources.
    """
    # Sequential execution required - SQLAlchemy session doesn't support concurrent operations
    sources = await service.list(
        offset=offset,
        limit=limit,
        active_only=active_only,
        workspace_id=context.workspace.id,
        saved_view_id=saved_view_id,
        search=search,
        status=status,
        owner_user_id=owner_user_id,
        team_id=team_id,
        domain_id=domain_id,
    )
    total = await service.count(
        active_only=active_only,
        workspace_id=context.workspace.id,
        saved_view_id=saved_view_id,
        search=search,
        status=status,
        owner_user_id=owner_user_id,
        team_id=team_id,
        domain_id=domain_id,
    )

    return SourceListResponse(
        data=[SourceResponse.from_model(s) for s in sources],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post(
    "",
    response_model=SourceResponse,
    status_code=201,
    summary="Create source",
    description="Create a new data source",
)
async def create_source(
    service: SourceServiceDep,
    source: SourceCreate,
    context=Depends(require_permission("sources:write")),
) -> SourceResponse:
    """Create a new data source.

    Args:
        service: Injected source service.
        source: Source creation data.

    Returns:
        Created source.
    """
    created = await service.create(
        name=source.name,
        type=source.type,
        config=source.config,
        description=source.description,
        workspace_id=source.workspace_id or context.workspace.id,
        environment=source.environment,
        created_by=context.user.id,
        owner_user_id=source.owner_user_id,
        team_id=source.team_id,
        domain_id=source.domain_id,
    )
    return SourceResponse.from_model(created)


@router.get(
    "/{source_id}",
    response_model=SourceResponse,
    summary="Get source",
    description="Get a specific data source by ID",
)
async def get_source(
    service: SourceServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
    context=Depends(require_permission("sources:read")),
) -> SourceResponse:
    """Get a specific data source.

    Args:
        service: Injected source service.
        source_id: Source unique identifier.

    Returns:
        Source details.

    Raises:
        HTTPException: 404 if source not found.
    """
    source = await service.get_by_id(source_id, workspace_id=context.workspace.id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceResponse.from_model(source)


@router.put(
    "/{source_id}",
    response_model=SourceResponse,
    summary="Update source",
    description="Update an existing data source",
)
async def update_source(
    service: SourceServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
    update: SourceUpdate,
    context=Depends(require_permission("sources:write")),
) -> SourceResponse:
    """Update an existing data source.

    Args:
        service: Injected source service.
        source_id: Source unique identifier.
        update: Update data.

    Returns:
        Updated source.

    Raises:
        HTTPException: 404 if source not found.
    """
    updated = await service.update(
        source_id,
        name=update.name,
        config=update.config,
        description=update.description,
        is_active=update.is_active,
        environment=update.environment,
        workspace_id=context.workspace.id,
        updated_by=context.user.id,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceResponse.from_model(updated)


@router.delete(
    "/{source_id}",
    response_model=MessageResponse,
    summary="Delete source",
    description="Delete a data source and all related data",
)
async def delete_source(
    service: SourceServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
    context=Depends(require_permission("sources:write")),
) -> MessageResponse:
    """Delete a data source.

    Args:
        service: Injected source service.
        source_id: Source unique identifier.

    Returns:
        Success message.

    Raises:
        HTTPException: 404 if source not found.
    """
    source = await service.get_by_id(source_id, workspace_id=context.workspace.id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    deleted = await service.delete(source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Source not found")
    return MessageResponse(message="Source deleted successfully")


class BulkDeleteRequest(BaseSchema):
    """Request for bulk delete operation."""

    ids: list[str] = Field(..., description="List of source IDs to delete")


class BulkDeleteResponse(BaseSchema):
    """Response for bulk delete operation."""

    deleted_count: int = Field(..., description="Number of successfully deleted sources")
    failed_ids: list[str] = Field(default_factory=list, description="IDs that failed to delete")
    total_requested: int = Field(..., description="Total number of IDs requested")


@router.post(
    "/bulk-delete",
    response_model=BulkDeleteResponse,
    summary="Bulk delete sources",
    description="Delete multiple data sources at once",
)
async def bulk_delete_sources(
    service: SourceServiceDep,
    request: BulkDeleteRequest,
    context=Depends(require_permission("sources:write")),
) -> BulkDeleteResponse:
    """Delete multiple data sources.

    Args:
        service: Injected source service.
        request: Request with list of source IDs.

    Returns:
        Result with deleted count and any failed IDs.
    """
    if not request.ids:
        raise HTTPException(status_code=400, detail="No source IDs provided")

    deleted_count = 0
    failed_ids = []

    for source_id in request.ids:
        try:
            source = await service.get_by_id(source_id, workspace_id=context.workspace.id)
            if source is None:
                failed_ids.append(source_id)
                continue
            deleted = await service.delete(source_id)
            if deleted:
                deleted_count += 1
            else:
                failed_ids.append(source_id)
        except Exception:
            failed_ids.append(source_id)

    return BulkDeleteResponse(
        deleted_count=deleted_count,
        failed_ids=failed_ids,
        total_requested=len(request.ids),
    )


@router.post(
    "/{source_id}/test",
    response_model=TestConnectionResponse,
    summary="Test source connection",
    description="Test connection to a data source",
)
async def test_source_connection(
    service: SourceServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
    context=Depends(require_permission("sources:read")),
) -> TestConnectionResponse:
    """Test connection to a data source.

    Args:
        service: Injected source service.
        source_id: Source unique identifier.

    Returns:
        Connection test result.

    Raises:
        HTTPException: 404 if source not found.
    """
    from truthound_dashboard.core.connections import test_connection

    source = await service.get_by_id(source_id, workspace_id=context.workspace.id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    result = await test_connection(source.type, await service.materialize_config(source))
    return TestConnectionResponse(
        connected=result.get("success", False),
        message=result.get("message"),
        error=result.get("error"),
    )


@router.post(
    "/{source_id}/credentials",
    response_model=SourceResponse,
    summary="Rotate source credentials",
    description="Rotate stored source credentials without exposing secret values",
)
async def rotate_source_credentials(
    service: SourceServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
    payload: SourceCredentialUpdate = ...,
    context=Depends(require_permission("sources:write")),
) -> SourceResponse:
    source = await service.rotate_credentials(
        source_id,
        credentials=payload.credentials,
        workspace_id=context.workspace.id,
    )
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceResponse.from_model(source)


@router.get(
    "/types/supported",
    response_model=SourceTypesResponse,
    summary="Get supported source types",
    description="Get list of supported data source types and their configuration",
)
async def get_supported_types() -> SourceTypesResponse:
    """Get list of supported source types.

    Returns comprehensive information about each source type including
    field definitions for dynamic form rendering.

    Returns:
        List of supported source types with field definitions.
    """
    from truthound_dashboard.core.connections import (
        get_source_type_categories,
        get_supported_source_types,
    )

    return SourceTypesResponse(
        types=get_supported_source_types(),
        categories=get_source_type_categories(),
    )


from truthound_dashboard.schemas.source import TestConnectionRequest


@router.post(
    "/test-connection",
    response_model=TestConnectionResponse,
    summary="Test connection configuration",
    description="Test a connection configuration before creating a source",
)
async def test_connection_config(
    request: TestConnectionRequest,
    _context=Depends(require_permission("sources:write")),
) -> TestConnectionResponse:
    """Test connection configuration before creating a source.

    This endpoint allows testing connection settings without
    persisting them to the database.

    Args:
        request: Connection test request with type and config.

    Returns:
        Connection test result.
    """
    from truthound_dashboard.core.connections import test_connection

    result = await test_connection(request.type, request.config)
    return TestConnectionResponse(
        connected=result.get("success", False),
        message=result.get("message"),
        error=result.get("error"),
    )


@router.get(
    "/{source_id}/ownership",
    response_model=SourceOwnershipResponse,
    summary="Get source ownership",
)
async def get_source_ownership(
    service: SourceServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
    context=Depends(require_permission("sources:read")),
) -> SourceOwnershipResponse:
    ownership = await service.get_ownership(
        source_id=source_id,
        workspace_id=context.workspace.id,
    )
    if ownership is None:
        raise HTTPException(status_code=404, detail="Source ownership not found")
    return SourceOwnershipResponse.from_model(ownership)


@router.put(
    "/{source_id}/ownership",
    response_model=SourceOwnershipResponse,
    summary="Update source ownership",
)
async def update_source_ownership(
    service: SourceServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
    payload: SourceOwnershipUpdate,
    context=Depends(require_permission("sources:write")),
) -> SourceOwnershipResponse:
    ownership = await service.set_ownership(
        source_id=source_id,
        workspace_id=context.workspace.id,
        owner_user_id=payload.owner_user_id,
        team_id=payload.team_id,
        domain_id=payload.domain_id,
    )
    if ownership is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceOwnershipResponse.from_model(ownership)
