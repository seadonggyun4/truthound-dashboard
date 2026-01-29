"""Profile API endpoints.

This module provides endpoints for data profiling and comparison.

Note: truthound's th.profile() only supports (data, source) parameters.
Advanced options like sampling strategies, pattern detection configuration,
and correlation analysis are NOT supported by the underlying library.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query

from truthound_dashboard.schemas import (
    LatestComparisonResponse,
    ProfileAdvancedRequest,
    ProfileComparisonRequest,
    ProfileComparisonResponse,
    ProfileListResponse,
    ProfileRequest,
    ProfileResponse,
    ProfileTrendResponse,
)

from .deps import ProfileComparisonServiceDep, ProfileServiceDep, SourceServiceDep

router = APIRouter()


@router.post(
    "/sources/{source_id}/profile",
    response_model=ProfileResponse,
    summary="Profile source",
    description="Run data profiling on a source",
)
async def profile_source(
    service: ProfileServiceDep,
    source_service: SourceServiceDep,
    source_id: Annotated[str, Path(description="Source ID to profile")],
    request: ProfileRequest | None = None,
) -> ProfileResponse:
    """Run data profiling on a source.

    Note: truthound's th.profile() only supports (data, source) parameters.
    Advanced configuration options are not supported.

    Args:
        service: Injected profile service.
        source_service: Injected source service.
        source_id: Source to profile.
        request: Optional request body (not used, kept for API compatibility).

    Returns:
        Profiling result with column statistics.

    Raises:
        HTTPException: 404 if source not found, 500 on profiling error.
    """
    # Verify source exists
    source = await source_service.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    try:
        result = await service.profile_source(source_id)
        return ProfileResponse.from_result(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/sources/{source_id}/profile/advanced",
    response_model=ProfileResponse,
    summary="Profile source with advanced configuration",
    description="Run data profiling with custom ProfilerConfig options",
)
async def profile_source_advanced(
    service: ProfileServiceDep,
    source_service: SourceServiceDep,
    source_id: Annotated[str, Path(description="Source ID to profile")],
    request: ProfileAdvancedRequest,
) -> ProfileResponse:
    """Run advanced data profiling with custom configuration.

    Uses truthound's ProfilerConfig for fine-grained control over:
    - Sampling: sample_size, random_seed
    - Features: include_patterns, include_correlations, include_distributions
    - Pattern detection: pattern_sample_size, min_pattern_match_ratio
    - Output: top_n_values, correlation_threshold
    - Performance: n_jobs

    Args:
        service: Injected profile service.
        source_service: Injected source service.
        source_id: Source to profile.
        request: Advanced profiling configuration.

    Returns:
        Profiling result with column statistics.

    Raises:
        HTTPException: 404 if source not found, 501 if not supported, 500 on error.
    """
    # Verify source exists
    source = await source_service.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    try:
        # Convert request to config dict
        config = {
            "sample_size": request.sample_size,
            "random_seed": request.random_seed,
            "include_patterns": request.include_patterns,
            "include_correlations": request.include_correlations,
            "include_distributions": request.include_distributions,
            "top_n_values": request.top_n_values,
            "pattern_sample_size": request.pattern_sample_size,
            "correlation_threshold": request.correlation_threshold,
            "min_pattern_match_ratio": request.min_pattern_match_ratio,
            "n_jobs": request.n_jobs,
        }
        result = await service.profile_source_advanced(source_id, config=config)
        return ProfileResponse.from_result(result)
    except ImportError as e:
        raise HTTPException(
            status_code=501,
            detail=f"Advanced profiling not available: {e}. "
            "Please upgrade truthound to the latest version.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Profile History and Comparison Endpoints
# =============================================================================


@router.get(
    "/sources/{source_id}/profile/latest",
    response_model=ProfileResponse | None,
    summary="Get latest profile",
    description="Retrieve the most recent profile result for a source",
)
async def get_latest_profile(
    service: ProfileServiceDep,
    source_service: SourceServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
) -> ProfileResponse | None:
    """Get the latest profile for a source.

    Args:
        service: Injected profile service.
        source_service: Injected source service.
        source_id: Source ID.

    Returns:
        Latest profile result or null.

    Raises:
        HTTPException: 404 if source not found.
    """
    source = await source_service.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    profile = await service.get_latest_profile(source_id)
    if profile is None:
        return None

    return ProfileResponse.from_result(profile)


@router.get(
    "/sources/{source_id}/profiles",
    response_model=ProfileListResponse,
    summary="List profiles",
    description="Get profile history for a source.",
)
async def list_profiles(
    source_id: Annotated[str, Path(description="Source ID")],
    comparison_service: ProfileComparisonServiceDep,
    source_service: SourceServiceDep,
    limit: int = Query(default=20, ge=1, le=100, description="Maximum profiles to return"),
    offset: int = Query(default=0, ge=0, description="Number to skip"),
) -> ProfileListResponse:
    """List profile history for a source.

    Args:
        source_id: Source ID.
        comparison_service: Profile comparison service.
        source_service: Source service.
        limit: Maximum profiles to return.
        offset: Number to skip.

    Returns:
        List of profile summaries.
    """
    # Verify source exists
    source = await source_service.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    profiles = await comparison_service.list_profiles(
        source_id, limit=limit, offset=offset
    )

    return ProfileListResponse(
        profiles=profiles,
        total=len(profiles),
        source_id=source_id,
    )


@router.post(
    "/profiles/compare",
    response_model=ProfileComparisonResponse,
    summary="Compare profiles",
    description="Compare two specific profiles.",
)
async def compare_profiles(
    request: ProfileComparisonRequest,
    comparison_service: ProfileComparisonServiceDep,
    profile_service: ProfileServiceDep,
    source_service: SourceServiceDep,
) -> ProfileComparisonResponse:
    """Compare two profiles.

    Args:
        request: Comparison request with profile IDs.
        comparison_service: Profile comparison service.
        profile_service: Profile service.
        source_service: Source service.

    Returns:
        Profile comparison result.
    """
    # Get baseline profile to determine source
    baseline = await profile_service.get(request.baseline_profile_id)
    if baseline is None:
        raise HTTPException(
            status_code=404,
            detail=f"Baseline profile {request.baseline_profile_id} not found",
        )

    # Get source
    source = await source_service.get_by_id(baseline.source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    try:
        result = await comparison_service.compare_profiles(
            source,
            request.baseline_profile_id,
            request.current_profile_id,
            significance_threshold=request.significance_threshold,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/sources/{source_id}/profiles/trend",
    response_model=ProfileTrendResponse,
    summary="Get profile trends",
    description="Get time-series profile trends for a source.",
)
async def get_profile_trend(
    source_id: Annotated[str, Path(description="Source ID")],
    comparison_service: ProfileComparisonServiceDep,
    source_service: SourceServiceDep,
    period: str = Query(default="30d", description="Time period (e.g., 7d, 30d, 90d)"),
    granularity: str = Query(default="daily", description="Data granularity"),
) -> ProfileTrendResponse:
    """Get profile trends for a source.

    Args:
        source_id: Source ID.
        comparison_service: Profile comparison service.
        source_service: Source service.
        period: Time period to analyze.
        granularity: Data granularity.

    Returns:
        Profile trend data.
    """
    # Verify source exists
    source = await source_service.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    result = await comparison_service.get_profile_trend(
        source, period=period, granularity=granularity
    )

    return result


@router.get(
    "/sources/{source_id}/profiles/latest-comparison",
    response_model=LatestComparisonResponse,
    summary="Compare latest profiles",
    description="Compare the latest profile with the previous one.",
)
async def get_latest_profile_comparison(
    source_id: Annotated[str, Path(description="Source ID")],
    comparison_service: ProfileComparisonServiceDep,
    source_service: SourceServiceDep,
) -> LatestComparisonResponse:
    """Compare latest profile with previous.

    Args:
        source_id: Source ID.
        comparison_service: Profile comparison service.
        source_service: Source service.

    Returns:
        Latest comparison result.
    """
    # Verify source exists
    source = await source_service.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    return await comparison_service.get_latest_comparison(source)


# =============================================================================
# Rule Generation from Profile
# =============================================================================


@router.post(
    "/sources/{source_id}/profiles/generate-rules",
    summary="Generate validation rules from profile",
    description="Automatically generate validation rules based on profiled data characteristics.",
)
async def generate_rules_from_profile(
    source_id: Annotated[str, Path(description="Source ID")],
    service: ProfileServiceDep,
    source_service: SourceServiceDep,
    strictness: str = Query(
        default="medium",
        description="Rule strictness: loose, medium, strict",
    ),
    preset: str = Query(
        default="default",
        description="Rule preset: default, strict, loose, minimal, comprehensive, ci_cd, schema_only, format_only",
    ),
    include_categories: list[str] | None = Query(
        default=None,
        description="Rule categories to include (schema, stats, pattern, completeness, uniqueness, distribution)",
    ),
    exclude_categories: list[str] | None = Query(
        default=None,
        description="Rule categories to exclude",
    ),
    profile_if_needed: bool = Query(
        default=True,
        description="Profile source if no recent profile exists",
    ),
    sample_size: int | None = Query(
        default=None,
        description="Sample size for profiling if needed",
    ),
) -> dict:
    """Generate validation rules from source profile.

    Uses truthound's generate_suite() to automatically create validation
    rules based on the profiled data characteristics.

    The generated rules can be used directly with th.check() or saved
    as a schema file for repeated validation.

    Args:
        source_id: Source ID to generate rules for.
        service: Profile service.
        source_service: Source service.
        strictness: Rule strictness level.
        preset: Rule generation preset.
        include_categories: Rule categories to include.
        exclude_categories: Rule categories to exclude.
        profile_if_needed: Profile source if no recent profile exists.
        sample_size: Sample size for profiling if needed.

    Returns:
        Generated rules with YAML content and metadata.

    Raises:
        HTTPException: 404 if source not found, 400 if no profile available.
    """
    # Verify source exists
    source = await source_service.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    try:
        result = await service.generate_rules_from_profile(
            source_id,
            strictness=strictness,
            preset=preset,
            include_categories=include_categories,
            exclude_categories=exclude_categories,
            profile_if_needed=profile_if_needed,
            sample_size=sample_size,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ImportError as e:
        raise HTTPException(
            status_code=501,
            detail=f"Rule generation not available: {e}. "
            "Please upgrade truthound to the latest version.",
        )
