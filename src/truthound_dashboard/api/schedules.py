"""Schedule management API endpoints.

Provides CRUD endpoints for validation schedules.

API Design: Direct Response Style
- Single resources return the resource directly
- List endpoints return PaginatedResponse with data, total, offset, limit
- Errors are handled via HTTPException
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from truthound_dashboard.core import ScheduleService, ValidationService
from truthound_dashboard.schemas import (
    MessageResponse,
    ScheduleActionResponse,
    ScheduleCreate,
    ScheduleListResponse,
    ScheduleResponse,
    ScheduleUpdate,
)
from truthound_dashboard.schemas.schedule import ScheduleListItem

from .deps import SessionDep

router = APIRouter()


async def get_schedule_service(session: SessionDep) -> ScheduleService:
    """Get schedule service dependency."""
    return ScheduleService(session)


ScheduleServiceDep = Annotated[ScheduleService, Depends(get_schedule_service)]


def _schedule_to_response(schedule) -> ScheduleResponse:
    """Convert schedule model to response schema."""
    return ScheduleResponse(
        id=schedule.id,
        name=schedule.name,
        source_id=schedule.source_id,
        cron_expression=schedule.cron_expression,
        is_active=schedule.is_active,
        notify_on_failure=schedule.notify_on_failure,
        last_run_at=(
            schedule.last_run_at.isoformat() if schedule.last_run_at else None
        ),
        next_run_at=(
            schedule.next_run_at.isoformat() if schedule.next_run_at else None
        ),
        config=schedule.config,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


def _schedule_to_list_item(schedule) -> ScheduleListItem:
    """Convert schedule model to list item schema."""
    return ScheduleListItem(
        id=schedule.id,
        name=schedule.name,
        source_id=schedule.source_id,
        cron_expression=schedule.cron_expression,
        is_active=schedule.is_active,
        notify_on_failure=schedule.notify_on_failure,
        last_run_at=(
            schedule.last_run_at.isoformat() if schedule.last_run_at else None
        ),
        next_run_at=(
            schedule.next_run_at.isoformat() if schedule.next_run_at else None
        ),
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


@router.get(
    "/schedules",
    response_model=ScheduleListResponse,
    summary="List schedules",
    description="List all validation schedules.",
)
async def list_schedules(
    service: ScheduleServiceDep,
    source_id: str | None = Query(None, description="Filter by source ID"),
    active_only: bool = Query(False, description="Only return active schedules"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
) -> ScheduleListResponse:
    """List validation schedules.

    Args:
        service: Schedule service.
        source_id: Optional source ID filter.
        active_only: Only return active schedules.
        offset: Offset for pagination.
        limit: Maximum results.

    Returns:
        Paginated list of schedules.
    """
    schedules = await service.list_schedules(
        source_id=source_id,
        active_only=active_only,
        limit=limit,
    )

    return ScheduleListResponse(
        data=[_schedule_to_list_item(s) for s in schedules],
        total=len(schedules),
        offset=offset,
        limit=limit,
    )


@router.post(
    "/schedules",
    response_model=ScheduleResponse,
    status_code=201,
    summary="Create schedule",
    description="Create a new validation schedule.",
)
async def create_schedule(
    request: ScheduleCreate,
    service: ScheduleServiceDep,
) -> ScheduleResponse:
    """Create a new schedule.

    Args:
        request: Schedule creation request.
        service: Schedule service.

    Returns:
        Created schedule.
    """
    try:
        schedule = await service.create_schedule(
            source_id=request.source_id,
            name=request.name,
            cron_expression=request.cron_expression,
            notify_on_failure=request.notify_on_failure,
            config=request.config,
        )
        return _schedule_to_response(schedule)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/schedules/{schedule_id}",
    response_model=ScheduleResponse,
    summary="Get schedule",
    description="Get a specific schedule by ID.",
)
async def get_schedule(
    schedule_id: str,
    service: ScheduleServiceDep,
) -> ScheduleResponse:
    """Get a schedule by ID.

    Args:
        schedule_id: Schedule ID.
        service: Schedule service.

    Returns:
        Schedule details.
    """
    schedule = await service.get_schedule(schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return _schedule_to_response(schedule)


@router.put(
    "/schedules/{schedule_id}",
    response_model=ScheduleResponse,
    summary="Update schedule",
    description="Update an existing schedule.",
)
async def update_schedule(
    schedule_id: str,
    request: ScheduleUpdate,
    service: ScheduleServiceDep,
) -> ScheduleResponse:
    """Update a schedule.

    Args:
        schedule_id: Schedule ID.
        request: Update request.
        service: Schedule service.

    Returns:
        Updated schedule.
    """
    try:
        schedule = await service.update_schedule(
            schedule_id,
            name=request.name,
            cron_expression=request.cron_expression,
            notify_on_failure=request.notify_on_failure,
            config=request.config,
        )

        if schedule is None:
            raise HTTPException(status_code=404, detail="Schedule not found")

        return _schedule_to_response(schedule)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/schedules/{schedule_id}",
    response_model=MessageResponse,
    summary="Delete schedule",
    description="Delete a schedule.",
)
async def delete_schedule(
    schedule_id: str,
    service: ScheduleServiceDep,
) -> MessageResponse:
    """Delete a schedule.

    Args:
        schedule_id: Schedule ID.
        service: Schedule service.

    Returns:
        Success message.
    """
    deleted = await service.delete_schedule(schedule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return MessageResponse(message="Schedule deleted")


@router.post(
    "/schedules/{schedule_id}/pause",
    response_model=ScheduleActionResponse,
    summary="Pause schedule",
    description="Pause a schedule.",
)
async def pause_schedule(
    schedule_id: str,
    service: ScheduleServiceDep,
) -> ScheduleActionResponse:
    """Pause a schedule.

    Args:
        schedule_id: Schedule ID.
        service: Schedule service.

    Returns:
        Action result with updated schedule.
    """
    schedule = await service.pause_schedule(schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return ScheduleActionResponse(
        message="Schedule paused",
        schedule=_schedule_to_response(schedule),
    )


@router.post(
    "/schedules/{schedule_id}/resume",
    response_model=ScheduleActionResponse,
    summary="Resume schedule",
    description="Resume a paused schedule.",
)
async def resume_schedule(
    schedule_id: str,
    service: ScheduleServiceDep,
) -> ScheduleActionResponse:
    """Resume a paused schedule.

    Args:
        schedule_id: Schedule ID.
        service: Schedule service.

    Returns:
        Action result with updated schedule.
    """
    schedule = await service.resume_schedule(schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return ScheduleActionResponse(
        message="Schedule resumed",
        schedule=_schedule_to_response(schedule),
    )


from pydantic import BaseModel


class ScheduleRunResponse(BaseModel):
    """Response for schedule run action."""

    message: str
    validation_id: str
    passed: bool


@router.post(
    "/schedules/{schedule_id}/run",
    response_model=ScheduleRunResponse,
    summary="Run schedule now",
    description="Trigger immediate execution of a scheduled validation.",
)
async def run_schedule_now(
    schedule_id: str,
    service: ScheduleServiceDep,
    session: SessionDep,
) -> ScheduleRunResponse:
    """Run a scheduled validation immediately.

    Args:
        schedule_id: Schedule ID.
        service: Schedule service.
        session: Database session.

    Returns:
        Validation result.
    """
    schedule = await service.get_schedule(schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Run validation using ValidationService
    validation_service = ValidationService(session)
    config = schedule.config or {}

    try:
        validation = await validation_service.run_validation(
            schedule.source_id,
            validators=config.get("validators"),
            schema_path=config.get("schema_path"),
            auto_schema=config.get("auto_schema", False),
        )

        return ScheduleRunResponse(
            message="Validation triggered",
            validation_id=validation.id,
            passed=validation.passed,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
