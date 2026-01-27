"""Validation history API endpoints.

Provides endpoints for validation history and trend analysis.

API Design: Direct Response Style
- Returns data directly without success wrapper
- Errors handled via HTTPException
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from truthound_dashboard.core import HistoryService

from .deps import SessionDep

router = APIRouter()


async def get_history_service(session: SessionDep) -> HistoryService:
    """Get history service dependency."""
    return HistoryService(session)


HistoryServiceDep = Annotated[HistoryService, Depends(get_history_service)]


class HistorySummary(BaseModel):
    """Validation history summary."""

    total_runs: int
    passed_runs: int
    failed_runs: int
    success_rate: float


class TrendDataPoint(BaseModel):
    """Single data point in trend."""

    date: str
    success_rate: float
    run_count: int
    passed_count: int
    failed_count: int


class FailureFrequency(BaseModel):
    """Failure frequency item."""

    issue: str
    count: int


class RecentValidation(BaseModel):
    """Recent validation item."""

    id: str
    status: str
    passed: bool
    has_critical: bool
    has_high: bool
    total_issues: int
    created_at: str


class HistoryResponse(BaseModel):
    """Validation history response."""

    summary: HistorySummary
    trend: list[TrendDataPoint]
    failure_frequency: list[FailureFrequency]
    recent_validations: list[RecentValidation]


@router.get(
    "/sources/{source_id}/history",
    response_model=HistoryResponse,
    summary="Get validation history",
    description="Get validation history with trend analysis for a source.",
)
async def get_validation_history(
    source_id: str,
    service: HistoryServiceDep,
    period: Literal["7d", "30d", "90d"] = Query("30d", description="Time period"),
    granularity: Literal["hourly", "daily", "weekly"] = Query(
        "daily", description="Aggregation granularity"
    ),
) -> HistoryResponse:
    """Get validation history with trend data.

    Args:
        source_id: Source ID.
        service: History service.
        period: Time period to analyze (7d, 30d, 90d).
        granularity: Aggregation granularity (hourly, daily, weekly).

    Returns:
        History data with summary, trend, failure_frequency, and recent_validations.
    """
    try:
        data = await service.get_history(
            source_id,
            period=period,
            granularity=granularity,
        )
        return HistoryResponse(**data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
