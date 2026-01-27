"""Sources API endpoints.

This module provides CRUD endpoints for managing data sources.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query

from truthound_dashboard.schemas import (
    MessageResponse,
    SourceCreate,
    SourceListResponse,
    SourceResponse,
    SourceUpdate,
)

from .deps import SourceServiceDep

router = APIRouter()


@router.get(
    "",
    response_model=SourceListResponse,
    summary="List sources",
    description="Get a paginated list of all data sources",
)
async def list_sources(
    service: SourceServiceDep,
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum items to return")
    ] = 100,
    active_only: Annotated[
        bool, Query(description="Only return active sources")
    ] = True,
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
    sources = await service.list(offset=offset, limit=limit, active_only=active_only)
    total = await service.count(active_only=active_only)

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
    source = await service.get_by_id(source_id)
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
    deleted = await service.delete(source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Source not found")
    return MessageResponse(message="Source deleted successfully")


@router.post(
    "/bulk-delete",
    response_model=dict,
    summary="Bulk delete sources",
    description="Delete multiple data sources at once",
)
async def bulk_delete_sources(
    service: SourceServiceDep,
    request: dict,
) -> dict:
    """Delete multiple data sources.

    Args:
        service: Injected source service.
        request: Dictionary with 'ids' key containing list of source IDs.

    Returns:
        Result with deleted count and any failed IDs.
    """
    ids = request.get("ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="No source IDs provided")

    deleted_count = 0
    failed_ids = []

    for source_id in ids:
        try:
            deleted = await service.delete(source_id)
            if deleted:
                deleted_count += 1
            else:
                failed_ids.append(source_id)
        except Exception:
            failed_ids.append(source_id)

    return {
        "success": True,
        "data": {
            "deleted_count": deleted_count,
            "failed_ids": failed_ids,
            "total_requested": len(ids),
        },
    }


@router.post(
    "/{source_id}/test",
    response_model=dict,
    summary="Test source connection",
    description="Test connection to a data source",
)
async def test_source_connection(
    service: SourceServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
) -> dict:
    """Test connection to a data source.

    Args:
        service: Injected source service.
        source_id: Source unique identifier.

    Returns:
        Connection test result with success status and message.

    Raises:
        HTTPException: 404 if source not found.
    """
    from truthound_dashboard.core.connections import test_connection

    source = await service.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    result = await test_connection(source.type, source.config)
    return {"success": True, "data": result}


@router.get(
    "/types/supported",
    response_model=dict,
    summary="Get supported source types",
    description="Get list of supported data source types and their configuration",
)
async def get_supported_types() -> dict:
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

    return {
        "success": True,
        "data": {
            "types": get_supported_source_types(),
            "categories": get_source_type_categories(),
        },
    }


@router.post(
    "/test-connection",
    response_model=dict,
    summary="Test connection configuration",
    description="Test a connection configuration before creating a source",
)
async def test_connection_config(
    request: dict,
) -> dict:
    """Test connection configuration before creating a source.

    This endpoint allows testing connection settings without
    persisting them to the database.

    Args:
        request: Dictionary with 'type' and 'config' keys.

    Returns:
        Connection test result with success status and message.
    """
    from truthound_dashboard.core.connections import test_connection

    source_type = request.get("type")
    config = request.get("config", {})

    if not source_type:
        raise HTTPException(status_code=400, detail="Source type is required")

    result = await test_connection(source_type, config)
    return {"success": True, "data": result}
