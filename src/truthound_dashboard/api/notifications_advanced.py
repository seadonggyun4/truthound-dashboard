"""Advanced notification management API endpoints.

This module provides REST API endpoints for managing advanced notification
features: routing rules, deduplication, throttling, and escalation.

Endpoints:
    Routing Rules:
        GET    /notifications/routing/rules              - List routing rules
        POST   /notifications/routing/rules              - Create routing rule
        GET    /notifications/routing/rules/{id}         - Get routing rule
        PUT    /notifications/routing/rules/{id}         - Update routing rule
        DELETE /notifications/routing/rules/{id}         - Delete routing rule
        GET    /notifications/routing/rules/types        - Get available rule types

    Deduplication:
        GET    /notifications/deduplication/configs      - List configs
        POST   /notifications/deduplication/configs      - Create config
        GET    /notifications/deduplication/configs/{id} - Get config
        PUT    /notifications/deduplication/configs/{id} - Update config
        DELETE /notifications/deduplication/configs/{id} - Delete config
        GET    /notifications/deduplication/stats        - Get statistics

    Throttling:
        GET    /notifications/throttling/configs         - List configs
        POST   /notifications/throttling/configs         - Create config
        GET    /notifications/throttling/configs/{id}    - Get config
        PUT    /notifications/throttling/configs/{id}    - Update config
        DELETE /notifications/throttling/configs/{id}    - Delete config
        GET    /notifications/throttling/stats           - Get statistics

    Escalation Policies:
        GET    /notifications/escalation/policies        - List policies
        POST   /notifications/escalation/policies        - Create policy
        GET    /notifications/escalation/policies/{id}   - Get policy
        PUT    /notifications/escalation/policies/{id}   - Update policy
        DELETE /notifications/escalation/policies/{id}   - Delete policy

    Escalation Incidents:
        GET    /notifications/escalation/incidents       - List incidents
        GET    /notifications/escalation/incidents/active - List active only
        GET    /notifications/escalation/incidents/{id}  - Get incident
        POST   /notifications/escalation/incidents/{id}/acknowledge - Acknowledge
        POST   /notifications/escalation/incidents/{id}/resolve - Resolve
        GET    /notifications/escalation/stats           - Get statistics
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.deps import get_session
from ..core.notifications.routing.rules import RuleRegistry
from ..db.models import (
    DeduplicationConfig,
    EscalationIncidentModel,
    EscalationPolicyModel,
    EscalationStateEnum,
    RoutingRuleModel,
    ThrottlingConfig,
)
from ..schemas.notifications_advanced import (
    AcknowledgeRequest,
    DeduplicationConfigCreate,
    DeduplicationConfigListResponse,
    DeduplicationConfigResponse,
    DeduplicationConfigUpdate,
    DeduplicationStats,
    EscalationEventBase,
    EscalationIncidentListResponse,
    EscalationIncidentResponse,
    EscalationPolicyCreate,
    EscalationPolicyListResponse,
    EscalationPolicyResponse,
    EscalationPolicyUpdate,
    EscalationStats,
    ResolveRequest,
    RoutingRuleCreate,
    RoutingRuleListResponse,
    RoutingRuleResponse,
    RoutingRuleUpdate,
    RuleTypeInfo,
    RuleTypesResponse,
    ThrottlingConfigCreate,
    ThrottlingConfigListResponse,
    ThrottlingConfigResponse,
    ThrottlingConfigUpdate,
    ThrottlingStats,
)

router = APIRouter(prefix="/notifications")


# =============================================================================
# Helper Functions
# =============================================================================


def _routing_rule_to_response(rule: RoutingRuleModel) -> RoutingRuleResponse:
    """Convert database model to response schema."""
    return RoutingRuleResponse(
        id=rule.id,
        name=rule.name,
        rule_config=rule.rule_config,
        actions=rule.actions,
        priority=rule.priority,
        is_active=rule.is_active,
        stop_on_match=rule.stop_on_match,
        metadata=rule.routing_metadata or {},
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def _dedup_config_to_response(config: DeduplicationConfig) -> DeduplicationConfigResponse:
    """Convert database model to response schema."""
    return DeduplicationConfigResponse(
        id=config.id,
        name=config.name,
        strategy=config.strategy,
        policy=config.policy,
        window_seconds=config.window_seconds,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


def _throttle_config_to_response(config: ThrottlingConfig) -> ThrottlingConfigResponse:
    """Convert database model to response schema."""
    return ThrottlingConfigResponse(
        id=config.id,
        name=config.name,
        per_minute=config.per_minute,
        per_hour=config.per_hour,
        per_day=config.per_day,
        burst_allowance=config.burst_allowance,
        channel_id=config.channel_id,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


def _escalation_policy_to_response(
    policy: EscalationPolicyModel,
) -> EscalationPolicyResponse:
    """Convert database model to response schema."""
    return EscalationPolicyResponse(
        id=policy.id,
        name=policy.name,
        description=policy.description or "",
        levels=policy.levels,
        auto_resolve_on_success=policy.auto_resolve_on_success,
        max_escalations=policy.max_escalations,
        is_active=policy.is_active,
        created_at=policy.created_at,
        updated_at=policy.updated_at,
    )


def _escalation_incident_to_response(
    incident: EscalationIncidentModel,
) -> EscalationIncidentResponse:
    """Convert database model to response schema."""
    events = []
    for event in incident.events or []:
        events.append(
            EscalationEventBase(
                from_state=event.get("from_state"),
                to_state=event.get("to_state", ""),
                actor=event.get("actor"),
                message=event.get("message", ""),
                timestamp=datetime.fromisoformat(event.get("timestamp", datetime.utcnow().isoformat())),
            )
        )

    return EscalationIncidentResponse(
        id=incident.id,
        policy_id=incident.policy_id,
        incident_ref=incident.incident_ref,
        state=incident.state,
        current_level=incident.current_level,
        escalation_count=incident.escalation_count,
        context=incident.context or {},
        acknowledged_by=incident.acknowledged_by,
        acknowledged_at=incident.acknowledged_at,
        resolved_by=incident.resolved_by,
        resolved_at=incident.resolved_at,
        next_escalation_at=incident.next_escalation_at,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        events=events,
    )


# =============================================================================
# Routing Rule Endpoints
# =============================================================================


@router.get("/routing/rules/types", response_model=RuleTypesResponse)
async def get_rule_types() -> RuleTypesResponse:
    """Get available routing rule types with their parameter schemas."""
    rule_types = []
    for rule_type in RuleRegistry.list_types():
        rule_class = RuleRegistry.get(rule_type)
        if rule_class:
            rule_types.append(
                RuleTypeInfo(
                    type=rule_type,
                    name=rule_class.__name__.replace("Rule", "").replace("_", " "),
                    description=rule_class.__doc__ or "",
                    param_schema=rule_class.get_param_schema(),
                )
            )

    return RuleTypesResponse(rule_types=rule_types)


@router.get("/routing/rules", response_model=RoutingRuleListResponse)
async def list_routing_rules(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    active_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
) -> RoutingRuleListResponse:
    """List routing rules ordered by priority."""
    query = select(RoutingRuleModel).order_by(
        RoutingRuleModel.priority.desc(),
        RoutingRuleModel.created_at.desc(),
    )

    if active_only:
        query = query.where(RoutingRuleModel.is_active == True)

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    rules = result.scalars().all()

    return RoutingRuleListResponse(
        items=[_routing_rule_to_response(r) for r in rules],
        total=len(rules),
        offset=offset,
        limit=limit,
    )


@router.post("/routing/rules", response_model=RoutingRuleResponse)
async def create_routing_rule(
    request: RoutingRuleCreate,
    session: AsyncSession = Depends(get_session),
) -> RoutingRuleResponse:
    """Create a new routing rule."""
    rule = RoutingRuleModel(
        name=request.name,
        rule_config=request.rule_config,
        actions=request.actions,
        priority=request.priority,
        is_active=request.is_active,
        stop_on_match=request.stop_on_match,
        routing_metadata=request.metadata,
    )
    session.add(rule)
    await session.commit()
    await session.refresh(rule)

    return _routing_rule_to_response(rule)


@router.get("/routing/rules/{rule_id}", response_model=RoutingRuleResponse)
async def get_routing_rule(
    rule_id: str,
    session: AsyncSession = Depends(get_session),
) -> RoutingRuleResponse:
    """Get a routing rule by ID."""
    result = await session.execute(
        select(RoutingRuleModel).where(RoutingRuleModel.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if rule is None:
        raise HTTPException(status_code=404, detail="Routing rule not found")

    return _routing_rule_to_response(rule)


@router.put("/routing/rules/{rule_id}", response_model=RoutingRuleResponse)
async def update_routing_rule(
    rule_id: str,
    request: RoutingRuleUpdate,
    session: AsyncSession = Depends(get_session),
) -> RoutingRuleResponse:
    """Update a routing rule."""
    result = await session.execute(
        select(RoutingRuleModel).where(RoutingRuleModel.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if rule is None:
        raise HTTPException(status_code=404, detail="Routing rule not found")

    if request.name is not None:
        rule.name = request.name
    if request.rule_config is not None:
        rule.rule_config = request.rule_config
    if request.actions is not None:
        rule.actions = request.actions
    if request.priority is not None:
        rule.priority = request.priority
    if request.is_active is not None:
        rule.is_active = request.is_active
    if request.stop_on_match is not None:
        rule.stop_on_match = request.stop_on_match
    if request.metadata is not None:
        rule.routing_metadata = request.metadata

    await session.commit()
    await session.refresh(rule)

    return _routing_rule_to_response(rule)


@router.delete("/routing/rules/{rule_id}")
async def delete_routing_rule(
    rule_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Delete a routing rule."""
    result = await session.execute(
        select(RoutingRuleModel).where(RoutingRuleModel.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if rule is None:
        raise HTTPException(status_code=404, detail="Routing rule not found")

    await session.delete(rule)
    await session.commit()

    return {"success": True, "message": "Routing rule deleted"}


# =============================================================================
# Deduplication Endpoints
# =============================================================================


@router.get("/deduplication/configs", response_model=DeduplicationConfigListResponse)
async def list_deduplication_configs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    active_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
) -> DeduplicationConfigListResponse:
    """List deduplication configurations."""
    query = select(DeduplicationConfig).order_by(DeduplicationConfig.created_at.desc())

    if active_only:
        query = query.where(DeduplicationConfig.is_active == True)

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    configs = result.scalars().all()

    return DeduplicationConfigListResponse(
        items=[_dedup_config_to_response(c) for c in configs],
        total=len(configs),
        offset=offset,
        limit=limit,
    )


@router.post("/deduplication/configs", response_model=DeduplicationConfigResponse)
async def create_deduplication_config(
    request: DeduplicationConfigCreate,
    session: AsyncSession = Depends(get_session),
) -> DeduplicationConfigResponse:
    """Create a new deduplication configuration."""
    config = DeduplicationConfig(
        name=request.name,
        strategy=request.strategy.value,
        policy=request.policy.value,
        window_seconds=request.window_seconds,
        is_active=request.is_active,
    )
    session.add(config)
    await session.commit()
    await session.refresh(config)

    return _dedup_config_to_response(config)


@router.get("/deduplication/configs/{config_id}", response_model=DeduplicationConfigResponse)
async def get_deduplication_config(
    config_id: str,
    session: AsyncSession = Depends(get_session),
) -> DeduplicationConfigResponse:
    """Get a deduplication config by ID."""
    result = await session.execute(
        select(DeduplicationConfig).where(DeduplicationConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(status_code=404, detail="Deduplication config not found")

    return _dedup_config_to_response(config)


@router.put("/deduplication/configs/{config_id}", response_model=DeduplicationConfigResponse)
async def update_deduplication_config(
    config_id: str,
    request: DeduplicationConfigUpdate,
    session: AsyncSession = Depends(get_session),
) -> DeduplicationConfigResponse:
    """Update a deduplication config."""
    result = await session.execute(
        select(DeduplicationConfig).where(DeduplicationConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(status_code=404, detail="Deduplication config not found")

    if request.name is not None:
        config.name = request.name
    if request.strategy is not None:
        config.strategy = request.strategy.value
    if request.policy is not None:
        config.policy = request.policy.value
    if request.window_seconds is not None:
        config.window_seconds = request.window_seconds
    if request.is_active is not None:
        config.is_active = request.is_active

    await session.commit()
    await session.refresh(config)

    return _dedup_config_to_response(config)


@router.delete("/deduplication/configs/{config_id}")
async def delete_deduplication_config(
    config_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Delete a deduplication config."""
    result = await session.execute(
        select(DeduplicationConfig).where(DeduplicationConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(status_code=404, detail="Deduplication config not found")

    await session.delete(config)
    await session.commit()

    return {"success": True, "message": "Deduplication config deleted"}


@router.get("/deduplication/stats", response_model=DeduplicationStats)
async def get_deduplication_stats(
    session: AsyncSession = Depends(get_session),
) -> DeduplicationStats:
    """Get deduplication statistics."""
    # In a real implementation, this would pull from actual metrics
    # For now, return placeholder stats
    return DeduplicationStats(
        total_received=0,
        total_deduplicated=0,
        total_passed=0,
        dedup_rate=0.0,
        active_fingerprints=0,
    )


# =============================================================================
# Throttling Endpoints
# =============================================================================


@router.get("/throttling/configs", response_model=ThrottlingConfigListResponse)
async def list_throttling_configs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    active_only: bool = Query(default=False),
    channel_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> ThrottlingConfigListResponse:
    """List throttling configurations."""
    query = select(ThrottlingConfig).order_by(ThrottlingConfig.created_at.desc())

    if active_only:
        query = query.where(ThrottlingConfig.is_active == True)
    if channel_id is not None:
        query = query.where(ThrottlingConfig.channel_id == channel_id)

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    configs = result.scalars().all()

    return ThrottlingConfigListResponse(
        items=[_throttle_config_to_response(c) for c in configs],
        total=len(configs),
        offset=offset,
        limit=limit,
    )


@router.post("/throttling/configs", response_model=ThrottlingConfigResponse)
async def create_throttling_config(
    request: ThrottlingConfigCreate,
    session: AsyncSession = Depends(get_session),
) -> ThrottlingConfigResponse:
    """Create a new throttling configuration."""
    config = ThrottlingConfig(
        name=request.name,
        per_minute=request.per_minute,
        per_hour=request.per_hour,
        per_day=request.per_day,
        burst_allowance=request.burst_allowance,
        channel_id=request.channel_id,
        is_active=request.is_active,
    )
    session.add(config)
    await session.commit()
    await session.refresh(config)

    return _throttle_config_to_response(config)


@router.get("/throttling/configs/{config_id}", response_model=ThrottlingConfigResponse)
async def get_throttling_config(
    config_id: str,
    session: AsyncSession = Depends(get_session),
) -> ThrottlingConfigResponse:
    """Get a throttling config by ID."""
    result = await session.execute(
        select(ThrottlingConfig).where(ThrottlingConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(status_code=404, detail="Throttling config not found")

    return _throttle_config_to_response(config)


@router.put("/throttling/configs/{config_id}", response_model=ThrottlingConfigResponse)
async def update_throttling_config(
    config_id: str,
    request: ThrottlingConfigUpdate,
    session: AsyncSession = Depends(get_session),
) -> ThrottlingConfigResponse:
    """Update a throttling config."""
    result = await session.execute(
        select(ThrottlingConfig).where(ThrottlingConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(status_code=404, detail="Throttling config not found")

    if request.name is not None:
        config.name = request.name
    if request.per_minute is not None:
        config.per_minute = request.per_minute
    if request.per_hour is not None:
        config.per_hour = request.per_hour
    if request.per_day is not None:
        config.per_day = request.per_day
    if request.burst_allowance is not None:
        config.burst_allowance = request.burst_allowance
    if request.channel_id is not None:
        config.channel_id = request.channel_id
    if request.is_active is not None:
        config.is_active = request.is_active

    await session.commit()
    await session.refresh(config)

    return _throttle_config_to_response(config)


@router.delete("/throttling/configs/{config_id}")
async def delete_throttling_config(
    config_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Delete a throttling config."""
    result = await session.execute(
        select(ThrottlingConfig).where(ThrottlingConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(status_code=404, detail="Throttling config not found")

    await session.delete(config)
    await session.commit()

    return {"success": True, "message": "Throttling config deleted"}


@router.get("/throttling/stats", response_model=ThrottlingStats)
async def get_throttling_stats(
    session: AsyncSession = Depends(get_session),
) -> ThrottlingStats:
    """Get throttling statistics."""
    # In a real implementation, this would pull from actual metrics
    return ThrottlingStats(
        total_received=0,
        total_throttled=0,
        total_passed=0,
        throttle_rate=0.0,
        current_window_count=0,
    )


# =============================================================================
# Escalation Policy Endpoints
# =============================================================================


@router.get("/escalation/policies", response_model=EscalationPolicyListResponse)
async def list_escalation_policies(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    active_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
) -> EscalationPolicyListResponse:
    """List escalation policies."""
    query = select(EscalationPolicyModel).order_by(
        EscalationPolicyModel.created_at.desc()
    )

    if active_only:
        query = query.where(EscalationPolicyModel.is_active == True)

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    policies = result.scalars().all()

    return EscalationPolicyListResponse(
        items=[_escalation_policy_to_response(p) for p in policies],
        total=len(policies),
        offset=offset,
        limit=limit,
    )


@router.post("/escalation/policies", response_model=EscalationPolicyResponse)
async def create_escalation_policy(
    request: EscalationPolicyCreate,
    session: AsyncSession = Depends(get_session),
) -> EscalationPolicyResponse:
    """Create a new escalation policy."""
    # Convert levels to dict format
    levels = [level.model_dump() for level in request.levels]

    policy = EscalationPolicyModel(
        name=request.name,
        description=request.description,
        levels=levels,
        auto_resolve_on_success=request.auto_resolve_on_success,
        max_escalations=request.max_escalations,
        is_active=request.is_active,
    )
    session.add(policy)
    await session.commit()
    await session.refresh(policy)

    return _escalation_policy_to_response(policy)


@router.get("/escalation/policies/{policy_id}", response_model=EscalationPolicyResponse)
async def get_escalation_policy(
    policy_id: str,
    session: AsyncSession = Depends(get_session),
) -> EscalationPolicyResponse:
    """Get an escalation policy by ID."""
    result = await session.execute(
        select(EscalationPolicyModel).where(EscalationPolicyModel.id == policy_id)
    )
    policy = result.scalar_one_or_none()

    if policy is None:
        raise HTTPException(status_code=404, detail="Escalation policy not found")

    return _escalation_policy_to_response(policy)


@router.put("/escalation/policies/{policy_id}", response_model=EscalationPolicyResponse)
async def update_escalation_policy(
    policy_id: str,
    request: EscalationPolicyUpdate,
    session: AsyncSession = Depends(get_session),
) -> EscalationPolicyResponse:
    """Update an escalation policy."""
    result = await session.execute(
        select(EscalationPolicyModel).where(EscalationPolicyModel.id == policy_id)
    )
    policy = result.scalar_one_or_none()

    if policy is None:
        raise HTTPException(status_code=404, detail="Escalation policy not found")

    if request.name is not None:
        policy.name = request.name
    if request.description is not None:
        policy.description = request.description
    if request.levels is not None:
        policy.levels = [level.model_dump() for level in request.levels]
    if request.auto_resolve_on_success is not None:
        policy.auto_resolve_on_success = request.auto_resolve_on_success
    if request.max_escalations is not None:
        policy.max_escalations = request.max_escalations
    if request.is_active is not None:
        policy.is_active = request.is_active

    await session.commit()
    await session.refresh(policy)

    return _escalation_policy_to_response(policy)


@router.delete("/escalation/policies/{policy_id}")
async def delete_escalation_policy(
    policy_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Delete an escalation policy."""
    result = await session.execute(
        select(EscalationPolicyModel).where(EscalationPolicyModel.id == policy_id)
    )
    policy = result.scalar_one_or_none()

    if policy is None:
        raise HTTPException(status_code=404, detail="Escalation policy not found")

    await session.delete(policy)
    await session.commit()

    return {"success": True, "message": "Escalation policy deleted"}


# =============================================================================
# Escalation Incident Endpoints
# =============================================================================


@router.get("/escalation/incidents", response_model=EscalationIncidentListResponse)
async def list_escalation_incidents(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    policy_id: str | None = Query(default=None),
    state: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> EscalationIncidentListResponse:
    """List escalation incidents."""
    query = select(EscalationIncidentModel).order_by(
        EscalationIncidentModel.created_at.desc()
    )

    if policy_id is not None:
        query = query.where(EscalationIncidentModel.policy_id == policy_id)
    if state is not None:
        query = query.where(EscalationIncidentModel.state == state)

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    incidents = result.scalars().all()

    return EscalationIncidentListResponse(
        items=[_escalation_incident_to_response(i) for i in incidents],
        total=len(incidents),
        offset=offset,
        limit=limit,
    )


@router.get("/escalation/incidents/active", response_model=EscalationIncidentListResponse)
async def list_active_incidents(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> EscalationIncidentListResponse:
    """List active (non-resolved) escalation incidents."""
    query = (
        select(EscalationIncidentModel)
        .where(EscalationIncidentModel.state != EscalationStateEnum.RESOLVED.value)
        .order_by(EscalationIncidentModel.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(query)
    incidents = result.scalars().all()

    return EscalationIncidentListResponse(
        items=[_escalation_incident_to_response(i) for i in incidents],
        total=len(incidents),
        offset=offset,
        limit=limit,
    )


@router.get("/escalation/incidents/{incident_id}", response_model=EscalationIncidentResponse)
async def get_escalation_incident(
    incident_id: str,
    session: AsyncSession = Depends(get_session),
) -> EscalationIncidentResponse:
    """Get an escalation incident by ID."""
    result = await session.execute(
        select(EscalationIncidentModel).where(EscalationIncidentModel.id == incident_id)
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(status_code=404, detail="Escalation incident not found")

    return _escalation_incident_to_response(incident)


@router.post("/escalation/incidents/{incident_id}/acknowledge", response_model=EscalationIncidentResponse)
async def acknowledge_incident(
    incident_id: str,
    request: AcknowledgeRequest,
    session: AsyncSession = Depends(get_session),
) -> EscalationIncidentResponse:
    """Acknowledge an escalation incident."""
    result = await session.execute(
        select(EscalationIncidentModel).where(EscalationIncidentModel.id == incident_id)
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(status_code=404, detail="Escalation incident not found")

    if incident.state == EscalationStateEnum.RESOLVED.value:
        raise HTTPException(status_code=400, detail="Cannot acknowledge resolved incident")

    if incident.state == EscalationStateEnum.ACKNOWLEDGED.value:
        raise HTTPException(status_code=400, detail="Incident already acknowledged")

    # Record state transition
    old_state = incident.state
    incident.state = EscalationStateEnum.ACKNOWLEDGED.value
    incident.acknowledged_by = request.actor
    incident.acknowledged_at = datetime.utcnow()
    incident.add_event(
        from_state=old_state,
        to_state=EscalationStateEnum.ACKNOWLEDGED.value,
        actor=request.actor,
        message=request.message or f"Acknowledged by {request.actor}",
    )

    await session.commit()
    await session.refresh(incident)

    return _escalation_incident_to_response(incident)


@router.post("/escalation/incidents/{incident_id}/resolve", response_model=EscalationIncidentResponse)
async def resolve_incident(
    incident_id: str,
    request: ResolveRequest,
    session: AsyncSession = Depends(get_session),
) -> EscalationIncidentResponse:
    """Resolve an escalation incident."""
    result = await session.execute(
        select(EscalationIncidentModel).where(EscalationIncidentModel.id == incident_id)
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(status_code=404, detail="Escalation incident not found")

    if incident.state == EscalationStateEnum.RESOLVED.value:
        raise HTTPException(status_code=400, detail="Incident already resolved")

    # Record state transition
    old_state = incident.state
    incident.state = EscalationStateEnum.RESOLVED.value
    incident.resolved_by = request.actor
    incident.resolved_at = datetime.utcnow()
    incident.next_escalation_at = None

    actor_msg = request.actor or "system"
    incident.add_event(
        from_state=old_state,
        to_state=EscalationStateEnum.RESOLVED.value,
        actor=request.actor,
        message=request.message or f"Resolved by {actor_msg}",
    )

    await session.commit()
    await session.refresh(incident)

    return _escalation_incident_to_response(incident)


@router.get("/escalation/stats", response_model=EscalationStats)
async def get_escalation_stats(
    session: AsyncSession = Depends(get_session),
) -> EscalationStats:
    """Get escalation statistics."""
    # Count all incidents
    result = await session.execute(select(EscalationIncidentModel))
    all_incidents = result.scalars().all()

    # Count by state
    by_state: dict[str, int] = {}
    active_count = 0
    for incident in all_incidents:
        state = incident.state
        by_state[state] = by_state.get(state, 0) + 1
        if state != EscalationStateEnum.RESOLVED.value:
            active_count += 1

    # Count policies
    result = await session.execute(select(EscalationPolicyModel))
    policies = result.scalars().all()

    return EscalationStats(
        total_incidents=len(all_incidents),
        by_state=by_state,
        active_count=active_count,
        total_policies=len(policies),
        avg_resolution_time_minutes=None,  # Would need more complex calculation
    )
