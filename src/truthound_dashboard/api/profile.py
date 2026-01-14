"""Profile API endpoints.

This module provides endpoints for data profiling.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from truthound_dashboard.schemas import ProfileRequest, ProfileResponse

from .deps import ProfileServiceDep, SourceServiceDep

router = APIRouter()


@router.post(
    "/sources/{source_id}/profile",
    response_model=ProfileResponse,
    summary="Profile source",
    description="Run data profiling on a source with optional sampling",
)
async def profile_source(
    service: ProfileServiceDep,
    source_service: SourceServiceDep,
    source_id: Annotated[str, Path(description="Source ID to profile")],
    request: ProfileRequest | None = None,
) -> ProfileResponse:
    """Run data profiling on a source.

    Args:
        service: Injected profile service.
        source_service: Injected source service.
        source_id: Source to profile.
        request: Optional profiling configuration with sample_size.

    Returns:
        Profiling result with column statistics.

    Raises:
        HTTPException: 404 if source not found.
    """
    # Verify source exists
    source = await source_service.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    # Extract sample_size from request if provided
    sample_size = request.sample_size if request else None

    try:
        result = await service.profile_source(
            source_id,
            sample_size=sample_size,
        )
        return ProfileResponse.from_result(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
