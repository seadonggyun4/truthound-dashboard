"""Notification management API endpoints.

This module provides REST API endpoints for managing notification
channels, rules, and viewing delivery logs.

API Design: Direct Response Style
- Single resources return the resource directly
- List endpoints return data array with count
- Errors are handled via HTTPException
- Success is indicated by HTTP status codes (200, 201, 204)

Endpoints:
    Channels:
        GET    /notifications/channels              - List channels
        POST   /notifications/channels              - Create channel
        GET    /notifications/channels/{id}         - Get channel
        PUT    /notifications/channels/{id}         - Update channel
        DELETE /notifications/channels/{id}         - Delete channel
        POST   /notifications/channels/{id}/test    - Test channel
        GET    /notifications/channels/types        - Get available types

    Rules:
        GET    /notifications/rules                 - List rules
        POST   /notifications/rules                 - Create rule
        GET    /notifications/rules/{id}            - Get rule
        PUT    /notifications/rules/{id}            - Update rule
        DELETE /notifications/rules/{id}            - Delete rule
        GET    /notifications/rules/conditions      - Get valid conditions

    Logs:
        GET    /notifications/logs                  - List logs
        GET    /notifications/logs/stats            - Get statistics
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.deps import get_session
from ..core.notifications.dispatcher import create_dispatcher
from ..core.notifications.service import (
    NotificationChannelService,
    NotificationLogService,
    NotificationRuleService,
)

router = APIRouter(prefix="/notifications")


# =============================================================================
# Request/Response Schemas
# =============================================================================


class ChannelCreate(BaseModel):
    """Request schema for creating a notification channel."""

    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., description="Channel type (slack, email, webhook)")
    config: dict[str, Any] = Field(..., description="Channel-specific configuration")
    is_active: bool = Field(default=True)


class ChannelUpdate(BaseModel):
    """Request schema for updating a notification channel."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    config: dict[str, Any] | None = Field(default=None)
    is_active: bool | None = Field(default=None)


class ChannelResponse(BaseModel):
    """Response schema for a notification channel."""

    id: str
    name: str
    type: str
    is_active: bool
    config_summary: str
    created_at: str
    updated_at: str


class ChannelListResponse(BaseModel):
    """Response schema for channel list."""

    data: list[ChannelResponse]
    count: int


class RuleCreate(BaseModel):
    """Request schema for creating a notification rule."""

    name: str = Field(..., min_length=1, max_length=255)
    condition: str = Field(..., description="Trigger condition type")
    channel_ids: list[str] = Field(..., min_length=1)
    condition_config: dict[str, Any] | None = Field(default=None)
    source_ids: list[str] | None = Field(
        default=None, description="Source IDs to filter (null = all sources)"
    )
    is_active: bool = Field(default=True)


class RuleUpdate(BaseModel):
    """Request schema for updating a notification rule."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    condition: str | None = Field(default=None)
    channel_ids: list[str] | None = Field(default=None)
    condition_config: dict[str, Any] | None = Field(default=None)
    source_ids: list[str] | None = Field(default=None)
    is_active: bool | None = Field(default=None)


class RuleResponse(BaseModel):
    """Response schema for a notification rule."""

    id: str
    name: str
    condition: str
    condition_config: dict[str, Any] | None
    channel_ids: list[str]
    source_ids: list[str] | None
    is_active: bool
    created_at: str
    updated_at: str


class RuleListResponse(BaseModel):
    """Response schema for rule list."""

    data: list[RuleResponse]
    count: int


class LogResponse(BaseModel):
    """Response schema for a notification log."""

    id: str
    channel_id: str
    rule_id: str | None
    event_type: str
    status: str
    message_preview: str
    error_message: str | None
    created_at: str
    sent_at: str | None


class LogDetailResponse(BaseModel):
    """Detailed response schema for a notification log."""

    id: str
    channel_id: str
    rule_id: str | None
    event_type: str
    event_data: dict[str, Any] | None
    status: str
    message: str
    error_message: str | None
    created_at: str
    sent_at: str | None


class LogListResponse(BaseModel):
    """Response schema for log list."""

    data: list[LogResponse]
    count: int


class TestChannelResponse(BaseModel):
    """Response schema for channel test."""

    success: bool
    message: str
    error: str | None = None


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


# =============================================================================
# Channel Endpoints
# =============================================================================


@router.get("/channels/types", response_model=list[dict[str, Any]])
async def get_channel_types(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """Get available notification channel types with their configuration schemas."""
    service = NotificationChannelService(session)
    return service.get_available_types()


@router.get("/channels", response_model=ChannelListResponse)
async def list_channels(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    active_only: bool = Query(default=False),
    channel_type: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> ChannelListResponse:
    """List notification channels."""
    service = NotificationChannelService(session)
    channels = await service.list(
        offset=offset,
        limit=limit,
        active_only=active_only,
        channel_type=channel_type,
    )

    data = [
        ChannelResponse(
            id=c.id,
            name=c.name,
            type=c.type,
            is_active=c.is_active,
            config_summary=c.get_config_summary(),
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )
        for c in channels
    ]

    return ChannelListResponse(data=data, count=len(data))


@router.post("/channels", response_model=ChannelResponse, status_code=201)
async def create_channel(
    request: ChannelCreate,
    session: AsyncSession = Depends(get_session),
) -> ChannelResponse:
    """Create a new notification channel."""
    service = NotificationChannelService(session)

    try:
        channel = await service.create(
            name=request.name,
            channel_type=request.type,
            config=request.config,
            is_active=request.is_active,
        )
        await session.commit()

        return ChannelResponse(
            id=channel.id,
            name=channel.name,
            type=channel.type,
            is_active=channel.is_active,
            config_summary=channel.get_config_summary(),
            created_at=channel.created_at.isoformat(),
            updated_at=channel.updated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/channels/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: str,
    session: AsyncSession = Depends(get_session),
) -> ChannelResponse:
    """Get a notification channel by ID."""
    service = NotificationChannelService(session)
    channel = await service.get_by_id(channel_id)

    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    return ChannelResponse(
        id=channel.id,
        name=channel.name,
        type=channel.type,
        is_active=channel.is_active,
        config_summary=channel.get_config_summary(),
        created_at=channel.created_at.isoformat(),
        updated_at=channel.updated_at.isoformat(),
    )


@router.put("/channels/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: str,
    request: ChannelUpdate,
    session: AsyncSession = Depends(get_session),
) -> ChannelResponse:
    """Update a notification channel."""
    service = NotificationChannelService(session)

    try:
        channel = await service.update(
            channel_id,
            name=request.name,
            config=request.config,
            is_active=request.is_active,
        )
        await session.commit()

        if channel is None:
            raise HTTPException(status_code=404, detail="Channel not found")

        return ChannelResponse(
            id=channel.id,
            name=channel.name,
            type=channel.type,
            is_active=channel.is_active,
            config_summary=channel.get_config_summary(),
            created_at=channel.created_at.isoformat(),
            updated_at=channel.updated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/channels/{channel_id}", response_model=MessageResponse)
async def delete_channel(
    channel_id: str,
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Delete a notification channel."""
    service = NotificationChannelService(session)
    deleted = await service.delete(channel_id)
    await session.commit()

    if not deleted:
        raise HTTPException(status_code=404, detail="Channel not found")

    return MessageResponse(message="Channel deleted")


@router.post("/channels/{channel_id}/test", response_model=TestChannelResponse)
async def test_channel(
    channel_id: str,
    session: AsyncSession = Depends(get_session),
) -> TestChannelResponse:
    """Send a test notification to a channel."""
    dispatcher = create_dispatcher(session)
    result = await dispatcher.test_channel(channel_id)
    await session.commit()

    return TestChannelResponse(
        success=result.success,
        message="Test notification sent" if result.success else "Test failed",
        error=result.error,
    )


# =============================================================================
# Rule Endpoints
# =============================================================================


@router.get("/rules/conditions", response_model=list[dict[str, Any]])
async def get_rule_conditions(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """Get valid notification rule conditions."""
    service = NotificationRuleService(session)
    return service.get_valid_conditions()


@router.get("/rules", response_model=RuleListResponse)
async def list_rules(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    active_only: bool = Query(default=False),
    condition: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> RuleListResponse:
    """List notification rules."""
    service = NotificationRuleService(session)
    rules = await service.list(
        offset=offset,
        limit=limit,
        active_only=active_only,
        condition=condition,
    )

    data = [
        RuleResponse(
            id=r.id,
            name=r.name,
            condition=r.condition,
            condition_config=r.condition_config,
            channel_ids=r.channel_ids,
            source_ids=r.source_ids,
            is_active=r.is_active,
            created_at=r.created_at.isoformat(),
            updated_at=r.updated_at.isoformat(),
        )
        for r in rules
    ]

    return RuleListResponse(data=data, count=len(data))


@router.post("/rules", response_model=RuleResponse, status_code=201)
async def create_rule(
    request: RuleCreate,
    session: AsyncSession = Depends(get_session),
) -> RuleResponse:
    """Create a new notification rule."""
    service = NotificationRuleService(session)

    try:
        rule = await service.create(
            name=request.name,
            condition=request.condition,
            channel_ids=request.channel_ids,
            condition_config=request.condition_config,
            source_ids=request.source_ids,
            is_active=request.is_active,
        )
        await session.commit()

        return RuleResponse(
            id=rule.id,
            name=rule.name,
            condition=rule.condition,
            condition_config=rule.condition_config,
            channel_ids=rule.channel_ids,
            source_ids=rule.source_ids,
            is_active=rule.is_active,
            created_at=rule.created_at.isoformat(),
            updated_at=rule.updated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rules/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: str,
    session: AsyncSession = Depends(get_session),
) -> RuleResponse:
    """Get a notification rule by ID."""
    service = NotificationRuleService(session)
    rule = await service.get_by_id(rule_id)

    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")

    return RuleResponse(
        id=rule.id,
        name=rule.name,
        condition=rule.condition,
        condition_config=rule.condition_config,
        channel_ids=rule.channel_ids,
        source_ids=rule.source_ids,
        is_active=rule.is_active,
        created_at=rule.created_at.isoformat(),
        updated_at=rule.updated_at.isoformat(),
    )


@router.put("/rules/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: str,
    request: RuleUpdate,
    session: AsyncSession = Depends(get_session),
) -> RuleResponse:
    """Update a notification rule."""
    service = NotificationRuleService(session)

    try:
        rule = await service.update(
            rule_id,
            name=request.name,
            condition=request.condition,
            channel_ids=request.channel_ids,
            condition_config=request.condition_config,
            source_ids=request.source_ids,
            is_active=request.is_active,
        )
        await session.commit()

        if rule is None:
            raise HTTPException(status_code=404, detail="Rule not found")

        return RuleResponse(
            id=rule.id,
            name=rule.name,
            condition=rule.condition,
            condition_config=rule.condition_config,
            channel_ids=rule.channel_ids,
            source_ids=rule.source_ids,
            is_active=rule.is_active,
            created_at=rule.created_at.isoformat(),
            updated_at=rule.updated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/rules/{rule_id}", response_model=MessageResponse)
async def delete_rule(
    rule_id: str,
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Delete a notification rule."""
    service = NotificationRuleService(session)
    deleted = await service.delete(rule_id)
    await session.commit()

    if not deleted:
        raise HTTPException(status_code=404, detail="Rule not found")

    return MessageResponse(message="Rule deleted")


# =============================================================================
# Log Endpoints
# =============================================================================


@router.get("/logs", response_model=LogListResponse)
async def list_logs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    channel_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    hours: int | None = Query(default=None, ge=1, le=168),
    session: AsyncSession = Depends(get_session),
) -> LogListResponse:
    """List notification delivery logs."""
    service = NotificationLogService(session)
    logs = await service.list(
        offset=offset,
        limit=limit,
        channel_id=channel_id,
        status=status,
        hours=hours,
    )

    data = [
        LogResponse(
            id=log.id,
            channel_id=log.channel_id,
            rule_id=log.rule_id,
            event_type=log.event_type,
            status=log.status,
            message_preview=(
                log.message[:100] + "..." if len(log.message) > 100 else log.message
            ),
            error_message=log.error_message,
            created_at=log.created_at.isoformat(),
            sent_at=log.sent_at.isoformat() if log.sent_at else None,
        )
        for log in logs
    ]

    return LogListResponse(data=data, count=len(data))


@router.get("/logs/stats", response_model=dict[str, Any])
async def get_log_stats(
    hours: int = Query(default=24, ge=1, le=168),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get notification delivery statistics."""
    service = NotificationLogService(session)
    return await service.get_stats(hours=hours)


@router.get("/logs/{log_id}", response_model=LogDetailResponse)
async def get_log(
    log_id: str,
    session: AsyncSession = Depends(get_session),
) -> LogDetailResponse:
    """Get a notification log by ID."""
    service = NotificationLogService(session)
    log = await service.get_by_id(log_id)

    if log is None:
        raise HTTPException(status_code=404, detail="Log not found")

    return LogDetailResponse(
        id=log.id,
        channel_id=log.channel_id,
        rule_id=log.rule_id,
        event_type=log.event_type,
        event_data=log.event_data,
        status=log.status,
        message=log.message,
        error_message=log.error_message,
        created_at=log.created_at.isoformat(),
        sent_at=log.sent_at.isoformat() if log.sent_at else None,
    )
