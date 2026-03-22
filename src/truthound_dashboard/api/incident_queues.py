"""Incident queue API endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path

from truthound_dashboard.schemas.notifications_advanced import (
    IncidentQueueCreate,
    IncidentQueueListResponse,
    IncidentQueueMemberResponse,
    IncidentQueueMembershipUpdate,
    IncidentQueueResponse,
    IncidentQueueUpdate,
)

from .deps import IncidentQueueServiceDep, require_permission

router = APIRouter(prefix="/incident-queues", tags=["incident-queues"])


def _queue_response(queue: object) -> IncidentQueueResponse:
    members = [
        IncidentQueueMemberResponse(
            id=membership.id,
            user_id=membership.user_id,
            user_name=membership.user.display_name,
            email=membership.user.email,
            is_default_responder=membership.is_default_responder,
            created_at=membership.created_at,
            updated_at=membership.updated_at,
        )
        for membership in getattr(queue, "memberships", [])
        if getattr(membership, "user", None) is not None
    ]
    return IncidentQueueResponse(
        id=queue.id,
        workspace_id=queue.workspace_id,
        name=queue.name,
        slug=queue.slug,
        description=queue.description,
        is_default=queue.is_default,
        is_active=queue.is_active,
        members=members,
        created_at=queue.created_at,
        updated_at=queue.updated_at,
    )


@router.get("", response_model=IncidentQueueListResponse)
async def list_queues(
    service: IncidentQueueServiceDep,
    context=Depends(require_permission("queues:read")),
) -> IncidentQueueListResponse:
    queues = await service.list_queues(workspace_id=context.workspace.id)
    return IncidentQueueListResponse(
        items=[_queue_response(queue) for queue in queues],
        total=len(queues),
        offset=0,
        limit=len(queues) or 100,
    )


@router.post("", response_model=IncidentQueueResponse, status_code=201)
async def create_queue(
    payload: IncidentQueueCreate,
    service: IncidentQueueServiceDep,
    context=Depends(require_permission("queues:write")),
) -> IncidentQueueResponse:
    queue = await service.create_queue(
        workspace_id=context.workspace.id,
        name=payload.name,
        description=payload.description,
        slug=payload.slug,
        is_default=payload.is_default,
        is_active=payload.is_active,
        member_ids=payload.member_ids,
    )
    queue = await service.get_queue(queue_id=queue.id, workspace_id=context.workspace.id)
    return _queue_response(queue)


@router.get("/{queue_id}", response_model=IncidentQueueResponse)
async def get_queue(
    queue_id: Annotated[str, Path()],
    service: IncidentQueueServiceDep,
    context=Depends(require_permission("queues:read")),
) -> IncidentQueueResponse:
    queue = await service.get_queue(queue_id=queue_id, workspace_id=context.workspace.id)
    if queue is None:
        raise HTTPException(status_code=404, detail="Queue not found")
    return _queue_response(queue)


@router.put("/{queue_id}", response_model=IncidentQueueResponse)
async def update_queue(
    queue_id: Annotated[str, Path()],
    payload: IncidentQueueUpdate,
    service: IncidentQueueServiceDep,
    context=Depends(require_permission("queues:write")),
) -> IncidentQueueResponse:
    queue = await service.update_queue(
        queue_id=queue_id,
        workspace_id=context.workspace.id,
        name=payload.name,
        description=payload.description,
        is_default=payload.is_default,
        is_active=payload.is_active,
        member_ids=payload.member_ids,
    )
    if queue is None:
        raise HTTPException(status_code=404, detail="Queue not found")
    queue = await service.get_queue(queue_id=queue.id, workspace_id=context.workspace.id)
    return _queue_response(queue)


@router.delete("/{queue_id}", response_model=dict[str, str])
async def delete_queue(
    queue_id: Annotated[str, Path()],
    service: IncidentQueueServiceDep,
    context=Depends(require_permission("queues:write")),
) -> dict[str, str]:
    deleted = await service.delete_queue(queue_id=queue_id, workspace_id=context.workspace.id)
    if not deleted:
        raise HTTPException(status_code=400, detail="Queue could not be deleted")
    return {"message": "Queue deleted"}


@router.get("/{queue_id}/members", response_model=list[IncidentQueueMemberResponse])
async def list_queue_members(
    queue_id: Annotated[str, Path()],
    service: IncidentQueueServiceDep,
    context=Depends(require_permission("queues:read")),
) -> list[IncidentQueueMemberResponse]:
    queue = await service.get_queue(queue_id=queue_id, workspace_id=context.workspace.id)
    if queue is None:
        raise HTTPException(status_code=404, detail="Queue not found")
    return _queue_response(queue).members


@router.put("/{queue_id}/members", response_model=list[IncidentQueueMemberResponse])
async def replace_queue_members(
    queue_id: Annotated[str, Path()],
    payload: IncidentQueueMembershipUpdate,
    service: IncidentQueueServiceDep,
    context=Depends(require_permission("queues:write")),
) -> list[IncidentQueueMemberResponse]:
    queue = await service.update_queue(
        queue_id=queue_id,
        workspace_id=context.workspace.id,
        member_ids=payload.member_ids,
    )
    if queue is None:
        raise HTTPException(status_code=404, detail="Queue not found")
    queue = await service.get_queue(queue_id=queue_id, workspace_id=context.workspace.id)
    if queue is None:
        raise HTTPException(status_code=404, detail="Queue not found")
    return _queue_response(queue).members


@router.delete("/{queue_id}/members/{user_id}", response_model=list[IncidentQueueMemberResponse])
async def remove_queue_member(
    queue_id: Annotated[str, Path()],
    user_id: Annotated[str, Path()],
    service: IncidentQueueServiceDep,
    context=Depends(require_permission("queues:write")),
) -> list[IncidentQueueMemberResponse]:
    queue = await service.get_queue(queue_id=queue_id, workspace_id=context.workspace.id)
    if queue is None:
        raise HTTPException(status_code=404, detail="Queue not found")
    remaining_member_ids = [
        membership.user_id
        for membership in queue.memberships
        if membership.user_id != user_id
    ]
    updated = await service.update_queue(
        queue_id=queue_id,
        workspace_id=context.workspace.id,
        member_ids=remaining_member_ids,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Queue not found")
    updated = await service.get_queue(queue_id=queue_id, workspace_id=context.workspace.id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Queue not found")
    return _queue_response(updated).members
