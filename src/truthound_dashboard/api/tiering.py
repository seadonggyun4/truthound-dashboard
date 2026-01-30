"""Storage tiering API endpoints.

This module provides REST API endpoints for managing storage tiering:
- Storage tiers (hot, warm, cold, archive)
- Tier policies (age-based, access-based, size-based, scheduled, composite, custom)
- Tiering configurations
- Migration history

Based on truthound 1.2.10+ storage tiering capabilities.

Endpoints:
    Storage Tiers:
        GET    /tiering/tiers              - List storage tiers
        POST   /tiering/tiers              - Create storage tier
        GET    /tiering/tiers/{id}         - Get storage tier
        PUT    /tiering/tiers/{id}         - Update storage tier
        DELETE /tiering/tiers/{id}         - Delete storage tier

    Tier Policies:
        GET    /tiering/policies           - List tier policies
        POST   /tiering/policies           - Create tier policy
        GET    /tiering/policies/{id}      - Get tier policy
        PUT    /tiering/policies/{id}      - Update tier policy
        DELETE /tiering/policies/{id}      - Delete tier policy
        GET    /tiering/policies/{id}/tree - Get policy with children (for composite)
        GET    /tiering/policies/types     - Get available policy types

    Tiering Configurations:
        GET    /tiering/configs            - List tiering configurations
        POST   /tiering/configs            - Create tiering configuration
        GET    /tiering/configs/{id}       - Get tiering configuration
        PUT    /tiering/configs/{id}       - Update tiering configuration
        DELETE /tiering/configs/{id}       - Delete tiering configuration

    Migration History:
        GET    /tiering/migrations         - List migration history
        GET    /tiering/migrations/{id}    - Get migration details

    Statistics:
        GET    /tiering/stats              - Get tiering statistics
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db import get_db_session as get_session
from ..db.models import (
    MigrationDirection,
    StorageTierModel,
    TierMigrationHistoryModel,
    TierPolicyModel,
    TierPolicyType,
    TierType,
    TieringConfigModel,
)
from ..schemas.base import MessageResponse
from ..schemas.tiering import (
    AgeBasedPolicyConfig,
    AccessBasedPolicyConfig,
    CompositePolicyConfig,
    CustomPolicyConfig,
    MigrationHistoryListResponse,
    MigrationHistoryResponse,
    MigrationItemResponse,
    MigrateItemRequest,
    PolicyExecutionRequest,
    PolicyExecutionResponse,
    PolicyExecutionSummary,
    PolicyTypeInfo,
    PolicyTypesResponse,
    ProcessPoliciesResponse,
    ScheduledPolicyConfig,
    SizeBasedPolicyConfig,
    StorageTierCreate,
    StorageTierListResponse,
    StorageTierResponse,
    StorageTierUpdate,
    TierPolicyCreate,
    TierPolicyListResponse,
    TierPolicyResponse,
    TierPolicyType as TierPolicyTypeEnum,
    TierPolicyUpdate,
    TierPolicyWithChildren,
    TierStatistics,
    TierType as TierTypeEnum,
    TieringConfigCreate,
    TieringConfigListResponse,
    TieringConfigResponse,
    TieringConfigUpdate,
    TieringStatistics,
    TieringStatusResponse,
)

router = APIRouter(prefix="/tiering", tags=["tiering"])


# =============================================================================
# Helper Functions
# =============================================================================


def _tier_to_response(tier: StorageTierModel) -> StorageTierResponse:
    """Convert storage tier model to response schema."""
    return StorageTierResponse(
        id=tier.id,
        name=tier.name,
        tier_type=TierTypeEnum(tier.tier_type),
        store_type=tier.store_type,
        store_config=tier.store_config,
        priority=tier.priority,
        cost_per_gb=tier.cost_per_gb,
        retrieval_time_ms=tier.retrieval_time_ms,
        metadata=tier.tier_metadata,
        is_active=tier.is_active,
        created_at=tier.created_at,
        updated_at=tier.updated_at,
    )


def _policy_to_response(
    policy: TierPolicyModel,
    from_tier_name: str | None = None,
    to_tier_name: str | None = None,
) -> TierPolicyResponse:
    """Convert tier policy model to response schema."""
    return TierPolicyResponse(
        id=policy.id,
        name=policy.name,
        description=policy.description,
        policy_type=TierPolicyTypeEnum(policy.policy_type),
        from_tier_id=policy.from_tier_id,
        to_tier_id=policy.to_tier_id,
        direction=policy.direction,
        config=policy.config,
        is_active=policy.is_active,
        priority=policy.priority,
        parent_id=policy.parent_id,
        child_count=policy.child_count,
        from_tier_name=from_tier_name or (policy.from_tier.name if policy.from_tier else None),
        to_tier_name=to_tier_name or (policy.to_tier.name if policy.to_tier else None),
        created_at=policy.created_at,
        updated_at=policy.updated_at,
    )


def _policy_to_tree(policy: TierPolicyModel) -> TierPolicyWithChildren:
    """Convert tier policy model to tree response with children."""
    return TierPolicyWithChildren(
        id=policy.id,
        name=policy.name,
        description=policy.description,
        policy_type=TierPolicyTypeEnum(policy.policy_type),
        from_tier_id=policy.from_tier_id,
        to_tier_id=policy.to_tier_id,
        direction=policy.direction,
        config=policy.config,
        is_active=policy.is_active,
        priority=policy.priority,
        parent_id=policy.parent_id,
        child_count=policy.child_count,
        from_tier_name=policy.from_tier.name if policy.from_tier else None,
        to_tier_name=policy.to_tier.name if policy.to_tier else None,
        created_at=policy.created_at,
        updated_at=policy.updated_at,
        children=[_policy_to_tree(child) for child in (policy.children or [])],
    )


def _config_to_response(config: TieringConfigModel) -> TieringConfigResponse:
    """Convert tiering configuration model to response schema."""
    return TieringConfigResponse(
        id=config.id,
        name=config.name,
        description=config.description,
        default_tier_id=config.default_tier_id,
        enable_promotion=config.enable_promotion,
        promotion_threshold=config.promotion_threshold,
        check_interval_hours=config.check_interval_hours,
        batch_size=config.batch_size,
        enable_parallel_migration=config.enable_parallel_migration,
        max_parallel_migrations=config.max_parallel_migrations,
        is_active=config.is_active,
        default_tier_name=config.default_tier.name if config.default_tier else None,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


def _migration_to_response(
    migration: TierMigrationHistoryModel,
    from_tier_name: str | None = None,
    to_tier_name: str | None = None,
    policy_name: str | None = None,
) -> MigrationHistoryResponse:
    """Convert migration history model to response schema."""
    return MigrationHistoryResponse(
        id=migration.id,
        policy_id=migration.policy_id,
        item_id=migration.item_id,
        from_tier_id=migration.from_tier_id,
        to_tier_id=migration.to_tier_id,
        size_bytes=migration.size_bytes,
        status=migration.status,
        error_message=migration.error_message,
        started_at=migration.started_at,
        completed_at=migration.completed_at,
        duration_ms=migration.duration_ms,
        from_tier_name=from_tier_name,
        to_tier_name=to_tier_name,
        policy_name=policy_name,
    )


# =============================================================================
# Storage Tiers Endpoints
# =============================================================================


@router.get("/tiers", response_model=StorageTierListResponse)
async def list_storage_tiers(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    active_only: bool = Query(default=False),
    tier_type: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> StorageTierListResponse:
    """List all storage tiers with optional filtering."""
    query = select(StorageTierModel)

    if active_only:
        query = query.where(StorageTierModel.is_active == True)  # noqa: E712

    if tier_type:
        query = query.where(StorageTierModel.tier_type == tier_type)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    # Apply pagination and ordering
    query = query.order_by(StorageTierModel.priority).offset(offset).limit(limit)
    result = await session.execute(query)
    tiers = result.scalars().all()

    return StorageTierListResponse(
        items=[_tier_to_response(tier) for tier in tiers],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("/tiers", response_model=StorageTierResponse, status_code=201)
async def create_storage_tier(
    request: StorageTierCreate,
    session: AsyncSession = Depends(get_session),
) -> StorageTierResponse:
    """Create a new storage tier."""
    # Check for duplicate name
    existing = await session.execute(
        select(StorageTierModel).where(StorageTierModel.name == request.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Storage tier with name '{request.name}' already exists",
        )

    tier = StorageTierModel(
        name=request.name,
        tier_type=request.tier_type.value,
        store_type=request.store_type,
        store_config=request.store_config,
        priority=request.priority,
        cost_per_gb=request.cost_per_gb,
        retrieval_time_ms=request.retrieval_time_ms,
        tier_metadata=request.metadata,
        is_active=request.is_active,
    )
    session.add(tier)
    await session.commit()
    await session.refresh(tier)

    return _tier_to_response(tier)


@router.get("/tiers/{tier_id}", response_model=StorageTierResponse)
async def get_storage_tier(
    tier_id: str,
    session: AsyncSession = Depends(get_session),
) -> StorageTierResponse:
    """Get a storage tier by ID."""
    result = await session.execute(
        select(StorageTierModel).where(StorageTierModel.id == tier_id)
    )
    tier = result.scalar_one_or_none()

    if not tier:
        raise HTTPException(status_code=404, detail="Storage tier not found")

    return _tier_to_response(tier)


@router.put("/tiers/{tier_id}", response_model=StorageTierResponse)
async def update_storage_tier(
    tier_id: str,
    request: StorageTierUpdate,
    session: AsyncSession = Depends(get_session),
) -> StorageTierResponse:
    """Update a storage tier."""
    result = await session.execute(
        select(StorageTierModel).where(StorageTierModel.id == tier_id)
    )
    tier = result.scalar_one_or_none()

    if not tier:
        raise HTTPException(status_code=404, detail="Storage tier not found")

    # Check for duplicate name if updating
    if request.name is not None and request.name != tier.name:
        existing = await session.execute(
            select(StorageTierModel).where(StorageTierModel.name == request.name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Storage tier with name '{request.name}' already exists",
            )

    # Apply updates
    if request.name is not None:
        tier.name = request.name
    if request.tier_type is not None:
        tier.tier_type = request.tier_type.value
    if request.store_type is not None:
        tier.store_type = request.store_type
    if request.store_config is not None:
        tier.store_config = request.store_config
    if request.priority is not None:
        tier.priority = request.priority
    if request.cost_per_gb is not None:
        tier.cost_per_gb = request.cost_per_gb
    if request.retrieval_time_ms is not None:
        tier.retrieval_time_ms = request.retrieval_time_ms
    if request.metadata is not None:
        tier.tier_metadata = request.metadata
    if request.is_active is not None:
        tier.is_active = request.is_active

    await session.commit()
    await session.refresh(tier)

    return _tier_to_response(tier)


@router.delete("/tiers/{tier_id}", response_model=MessageResponse)
async def delete_storage_tier(
    tier_id: str,
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Delete a storage tier."""
    result = await session.execute(
        select(StorageTierModel).where(StorageTierModel.id == tier_id)
    )
    tier = result.scalar_one_or_none()

    if not tier:
        raise HTTPException(status_code=404, detail="Storage tier not found")

    await session.delete(tier)
    await session.commit()

    return MessageResponse(message=f"Storage tier '{tier.name}' deleted successfully")


# =============================================================================
# Tier Policies Endpoints
# =============================================================================


@router.get("/policies", response_model=TierPolicyListResponse)
async def list_tier_policies(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    active_only: bool = Query(default=False),
    policy_type: str | None = Query(default=None),
    from_tier_id: str | None = Query(default=None),
    to_tier_id: str | None = Query(default=None),
    parent_id: str | None = Query(default=None),
    root_only: bool = Query(default=False, description="Only show root policies (no parent)"),
    session: AsyncSession = Depends(get_session),
) -> TierPolicyListResponse:
    """List all tier policies with optional filtering."""
    query = select(TierPolicyModel).options(
        selectinload(TierPolicyModel.from_tier),
        selectinload(TierPolicyModel.to_tier),
    )

    if active_only:
        query = query.where(TierPolicyModel.is_active == True)  # noqa: E712

    if policy_type:
        query = query.where(TierPolicyModel.policy_type == policy_type)

    if from_tier_id:
        query = query.where(TierPolicyModel.from_tier_id == from_tier_id)

    if to_tier_id:
        query = query.where(TierPolicyModel.to_tier_id == to_tier_id)

    if parent_id:
        query = query.where(TierPolicyModel.parent_id == parent_id)

    if root_only:
        query = query.where(TierPolicyModel.parent_id == None)  # noqa: E711

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    # Apply pagination and ordering
    query = query.order_by(TierPolicyModel.priority, TierPolicyModel.name).offset(offset).limit(limit)
    result = await session.execute(query)
    policies = result.scalars().all()

    return TierPolicyListResponse(
        items=[_policy_to_response(policy) for policy in policies],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("/policies", response_model=TierPolicyResponse, status_code=201)
async def create_tier_policy(
    request: TierPolicyCreate,
    session: AsyncSession = Depends(get_session),
) -> TierPolicyResponse:
    """Create a new tier policy."""
    # Validate from_tier exists
    from_tier = await session.execute(
        select(StorageTierModel).where(StorageTierModel.id == request.from_tier_id)
    )
    if not from_tier.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Source tier not found")

    # Validate to_tier exists
    to_tier = await session.execute(
        select(StorageTierModel).where(StorageTierModel.id == request.to_tier_id)
    )
    if not to_tier.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Destination tier not found")

    # Validate parent if specified
    if request.parent_id:
        parent = await session.execute(
            select(TierPolicyModel).where(TierPolicyModel.id == request.parent_id)
        )
        parent_policy = parent.scalar_one_or_none()
        if not parent_policy:
            raise HTTPException(status_code=400, detail="Parent policy not found")
        if parent_policy.policy_type != TierPolicyType.COMPOSITE.value:
            raise HTTPException(
                status_code=400,
                detail="Parent policy must be a composite policy",
            )

    policy = TierPolicyModel(
        name=request.name,
        description=request.description,
        policy_type=request.policy_type.value,
        from_tier_id=request.from_tier_id,
        to_tier_id=request.to_tier_id,
        direction=request.direction.value,
        config=request.config,
        is_active=request.is_active,
        priority=request.priority,
        parent_id=request.parent_id,
    )
    session.add(policy)
    await session.commit()
    await session.refresh(policy, ["from_tier", "to_tier"])

    return _policy_to_response(policy)


@router.get("/policies/types", response_model=PolicyTypesResponse)
async def get_policy_types() -> PolicyTypesResponse:
    """Get available policy types with their configuration schemas."""
    policy_types = [
        PolicyTypeInfo(
            type=TierPolicyTypeEnum.AGE_BASED,
            name="Age-Based",
            description="Migrate items based on age (days/hours since creation)",
            config_schema=AgeBasedPolicyConfig.model_json_schema(),
        ),
        PolicyTypeInfo(
            type=TierPolicyTypeEnum.ACCESS_BASED,
            name="Access-Based",
            description="Migrate based on access patterns (inactive days or access count)",
            config_schema=AccessBasedPolicyConfig.model_json_schema(),
        ),
        PolicyTypeInfo(
            type=TierPolicyTypeEnum.SIZE_BASED,
            name="Size-Based",
            description="Migrate based on item size or tier capacity",
            config_schema=SizeBasedPolicyConfig.model_json_schema(),
        ),
        PolicyTypeInfo(
            type=TierPolicyTypeEnum.SCHEDULED,
            name="Scheduled",
            description="Migrate on a schedule (specific days/times)",
            config_schema=ScheduledPolicyConfig.model_json_schema(),
        ),
        PolicyTypeInfo(
            type=TierPolicyTypeEnum.COMPOSITE,
            name="Composite",
            description="Combine multiple policies with AND/OR logic",
            config_schema=CompositePolicyConfig.model_json_schema(),
        ),
        PolicyTypeInfo(
            type=TierPolicyTypeEnum.CUSTOM,
            name="Custom",
            description="Define custom migration logic with a predicate expression",
            config_schema=CustomPolicyConfig.model_json_schema(),
        ),
    ]
    return PolicyTypesResponse(policy_types=policy_types)


@router.get("/policies/{policy_id}", response_model=TierPolicyResponse)
async def get_tier_policy(
    policy_id: str,
    session: AsyncSession = Depends(get_session),
) -> TierPolicyResponse:
    """Get a tier policy by ID."""
    result = await session.execute(
        select(TierPolicyModel)
        .options(
            selectinload(TierPolicyModel.from_tier),
            selectinload(TierPolicyModel.to_tier),
        )
        .where(TierPolicyModel.id == policy_id)
    )
    policy = result.scalar_one_or_none()

    if not policy:
        raise HTTPException(status_code=404, detail="Tier policy not found")

    return _policy_to_response(policy)


@router.get("/policies/{policy_id}/tree", response_model=TierPolicyWithChildren)
async def get_tier_policy_tree(
    policy_id: str,
    session: AsyncSession = Depends(get_session),
) -> TierPolicyWithChildren:
    """Get a tier policy with all nested children (for composite policies)."""
    result = await session.execute(
        select(TierPolicyModel)
        .options(
            selectinload(TierPolicyModel.from_tier),
            selectinload(TierPolicyModel.to_tier),
            selectinload(TierPolicyModel.children).selectinload(TierPolicyModel.from_tier),
            selectinload(TierPolicyModel.children).selectinload(TierPolicyModel.to_tier),
            selectinload(TierPolicyModel.children).selectinload(TierPolicyModel.children),
        )
        .where(TierPolicyModel.id == policy_id)
    )
    policy = result.scalar_one_or_none()

    if not policy:
        raise HTTPException(status_code=404, detail="Tier policy not found")

    return _policy_to_tree(policy)


@router.put("/policies/{policy_id}", response_model=TierPolicyResponse)
async def update_tier_policy(
    policy_id: str,
    request: TierPolicyUpdate,
    session: AsyncSession = Depends(get_session),
) -> TierPolicyResponse:
    """Update a tier policy."""
    result = await session.execute(
        select(TierPolicyModel)
        .options(
            selectinload(TierPolicyModel.from_tier),
            selectinload(TierPolicyModel.to_tier),
        )
        .where(TierPolicyModel.id == policy_id)
    )
    policy = result.scalar_one_or_none()

    if not policy:
        raise HTTPException(status_code=404, detail="Tier policy not found")

    # Validate from_tier if updating
    if request.from_tier_id is not None:
        from_tier = await session.execute(
            select(StorageTierModel).where(StorageTierModel.id == request.from_tier_id)
        )
        if not from_tier.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Source tier not found")

    # Validate to_tier if updating
    if request.to_tier_id is not None:
        to_tier = await session.execute(
            select(StorageTierModel).where(StorageTierModel.id == request.to_tier_id)
        )
        if not to_tier.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Destination tier not found")

    # Apply updates
    if request.name is not None:
        policy.name = request.name
    if request.description is not None:
        policy.description = request.description
    if request.policy_type is not None:
        policy.policy_type = request.policy_type.value
    if request.from_tier_id is not None:
        policy.from_tier_id = request.from_tier_id
    if request.to_tier_id is not None:
        policy.to_tier_id = request.to_tier_id
    if request.direction is not None:
        policy.direction = request.direction.value
    if request.config is not None:
        policy.config = request.config
    if request.is_active is not None:
        policy.is_active = request.is_active
    if request.priority is not None:
        policy.priority = request.priority
    if request.parent_id is not None:
        policy.parent_id = request.parent_id

    await session.commit()
    await session.refresh(policy, ["from_tier", "to_tier"])

    return _policy_to_response(policy)


@router.delete("/policies/{policy_id}", response_model=MessageResponse)
async def delete_tier_policy(
    policy_id: str,
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Delete a tier policy."""
    result = await session.execute(
        select(TierPolicyModel).where(TierPolicyModel.id == policy_id)
    )
    policy = result.scalar_one_or_none()

    if not policy:
        raise HTTPException(status_code=404, detail="Tier policy not found")

    policy_name = policy.name
    await session.delete(policy)
    await session.commit()

    return MessageResponse(message=f"Tier policy '{policy_name}' deleted successfully")


# =============================================================================
# Tiering Configurations Endpoints
# =============================================================================


@router.get("/configs", response_model=TieringConfigListResponse)
async def list_tiering_configs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    active_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
) -> TieringConfigListResponse:
    """List all tiering configurations."""
    query = select(TieringConfigModel).options(
        selectinload(TieringConfigModel.default_tier)
    )

    if active_only:
        query = query.where(TieringConfigModel.is_active == True)  # noqa: E712

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    # Apply pagination and ordering
    query = query.order_by(TieringConfigModel.name).offset(offset).limit(limit)
    result = await session.execute(query)
    configs = result.scalars().all()

    return TieringConfigListResponse(
        items=[_config_to_response(config) for config in configs],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("/configs", response_model=TieringConfigResponse, status_code=201)
async def create_tiering_config(
    request: TieringConfigCreate,
    session: AsyncSession = Depends(get_session),
) -> TieringConfigResponse:
    """Create a new tiering configuration."""
    # Check for duplicate name
    existing = await session.execute(
        select(TieringConfigModel).where(TieringConfigModel.name == request.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Tiering configuration with name '{request.name}' already exists",
        )

    # Validate default_tier if specified
    if request.default_tier_id:
        default_tier = await session.execute(
            select(StorageTierModel).where(StorageTierModel.id == request.default_tier_id)
        )
        if not default_tier.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Default tier not found")

    config = TieringConfigModel(
        name=request.name,
        description=request.description,
        default_tier_id=request.default_tier_id,
        enable_promotion=request.enable_promotion,
        promotion_threshold=request.promotion_threshold,
        check_interval_hours=request.check_interval_hours,
        batch_size=request.batch_size,
        enable_parallel_migration=request.enable_parallel_migration,
        max_parallel_migrations=request.max_parallel_migrations,
        is_active=request.is_active,
    )
    session.add(config)
    await session.commit()
    await session.refresh(config, ["default_tier"])

    return _config_to_response(config)


@router.get("/configs/{config_id}", response_model=TieringConfigResponse)
async def get_tiering_config(
    config_id: str,
    session: AsyncSession = Depends(get_session),
) -> TieringConfigResponse:
    """Get a tiering configuration by ID."""
    result = await session.execute(
        select(TieringConfigModel)
        .options(selectinload(TieringConfigModel.default_tier))
        .where(TieringConfigModel.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Tiering configuration not found")

    return _config_to_response(config)


@router.put("/configs/{config_id}", response_model=TieringConfigResponse)
async def update_tiering_config(
    config_id: str,
    request: TieringConfigUpdate,
    session: AsyncSession = Depends(get_session),
) -> TieringConfigResponse:
    """Update a tiering configuration."""
    result = await session.execute(
        select(TieringConfigModel)
        .options(selectinload(TieringConfigModel.default_tier))
        .where(TieringConfigModel.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Tiering configuration not found")

    # Check for duplicate name if updating
    if request.name is not None and request.name != config.name:
        existing = await session.execute(
            select(TieringConfigModel).where(TieringConfigModel.name == request.name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Tiering configuration with name '{request.name}' already exists",
            )

    # Apply updates
    if request.name is not None:
        config.name = request.name
    if request.description is not None:
        config.description = request.description
    if request.default_tier_id is not None:
        config.default_tier_id = request.default_tier_id
    if request.enable_promotion is not None:
        config.enable_promotion = request.enable_promotion
    if request.promotion_threshold is not None:
        config.promotion_threshold = request.promotion_threshold
    if request.check_interval_hours is not None:
        config.check_interval_hours = request.check_interval_hours
    if request.batch_size is not None:
        config.batch_size = request.batch_size
    if request.enable_parallel_migration is not None:
        config.enable_parallel_migration = request.enable_parallel_migration
    if request.max_parallel_migrations is not None:
        config.max_parallel_migrations = request.max_parallel_migrations
    if request.is_active is not None:
        config.is_active = request.is_active

    await session.commit()
    await session.refresh(config, ["default_tier"])

    return _config_to_response(config)


@router.delete("/configs/{config_id}", response_model=MessageResponse)
async def delete_tiering_config(
    config_id: str,
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Delete a tiering configuration."""
    result = await session.execute(
        select(TieringConfigModel).where(TieringConfigModel.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Tiering configuration not found")

    config_name = config.name
    await session.delete(config)
    await session.commit()

    return MessageResponse(message=f"Tiering configuration '{config_name}' deleted successfully")


# =============================================================================
# Migration History Endpoints
# =============================================================================


@router.get("/migrations", response_model=MigrationHistoryListResponse)
async def list_migration_history(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    policy_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    from_tier_id: str | None = Query(default=None),
    to_tier_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> MigrationHistoryListResponse:
    """List migration history with optional filtering."""
    query = select(TierMigrationHistoryModel)

    if policy_id:
        query = query.where(TierMigrationHistoryModel.policy_id == policy_id)

    if status:
        query = query.where(TierMigrationHistoryModel.status == status)

    if from_tier_id:
        query = query.where(TierMigrationHistoryModel.from_tier_id == from_tier_id)

    if to_tier_id:
        query = query.where(TierMigrationHistoryModel.to_tier_id == to_tier_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    # Apply pagination and ordering
    query = query.order_by(TierMigrationHistoryModel.started_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    migrations = result.scalars().all()

    # Get tier names for display
    tier_ids = set()
    policy_ids = set()
    for m in migrations:
        tier_ids.add(m.from_tier_id)
        tier_ids.add(m.to_tier_id)
        if m.policy_id:
            policy_ids.add(m.policy_id)

    # Fetch tier names
    tier_names: dict[str, str] = {}
    if tier_ids:
        tiers_result = await session.execute(
            select(StorageTierModel).where(StorageTierModel.id.in_(tier_ids))
        )
        for tier in tiers_result.scalars():
            tier_names[tier.id] = tier.name

    # Fetch policy names
    policy_names: dict[str, str] = {}
    if policy_ids:
        policies_result = await session.execute(
            select(TierPolicyModel).where(TierPolicyModel.id.in_(policy_ids))
        )
        for policy in policies_result.scalars():
            policy_names[policy.id] = policy.name

    return MigrationHistoryListResponse(
        items=[
            _migration_to_response(
                m,
                from_tier_name=tier_names.get(m.from_tier_id),
                to_tier_name=tier_names.get(m.to_tier_id),
                policy_name=policy_names.get(m.policy_id) if m.policy_id else None,
            )
            for m in migrations
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/migrations/{migration_id}", response_model=MigrationHistoryResponse)
async def get_migration_history(
    migration_id: str,
    session: AsyncSession = Depends(get_session),
) -> MigrationHistoryResponse:
    """Get a migration history entry by ID."""
    result = await session.execute(
        select(TierMigrationHistoryModel).where(TierMigrationHistoryModel.id == migration_id)
    )
    migration = result.scalar_one_or_none()

    if not migration:
        raise HTTPException(status_code=404, detail="Migration history entry not found")

    # Get tier names
    tier_names: dict[str, str] = {}
    tiers_result = await session.execute(
        select(StorageTierModel).where(
            StorageTierModel.id.in_([migration.from_tier_id, migration.to_tier_id])
        )
    )
    for tier in tiers_result.scalars():
        tier_names[tier.id] = tier.name

    # Get policy name
    policy_name = None
    if migration.policy_id:
        policy_result = await session.execute(
            select(TierPolicyModel).where(TierPolicyModel.id == migration.policy_id)
        )
        policy = policy_result.scalar_one_or_none()
        if policy:
            policy_name = policy.name

    return _migration_to_response(
        migration,
        from_tier_name=tier_names.get(migration.from_tier_id),
        to_tier_name=tier_names.get(migration.to_tier_id),
        policy_name=policy_name,
    )


# =============================================================================
# Statistics Endpoints
# =============================================================================


@router.get("/stats", response_model=TieringStatistics)
async def get_tiering_statistics(
    session: AsyncSession = Depends(get_session),
) -> TieringStatistics:
    """Get overall tiering statistics."""
    # Count tiers
    total_tiers = (
        await session.execute(select(func.count()).select_from(StorageTierModel))
    ).scalar() or 0
    active_tiers = (
        await session.execute(
            select(func.count())
            .select_from(StorageTierModel)
            .where(StorageTierModel.is_active == True)  # noqa: E712
        )
    ).scalar() or 0

    # Count policies
    total_policies = (
        await session.execute(select(func.count()).select_from(TierPolicyModel))
    ).scalar() or 0
    active_policies = (
        await session.execute(
            select(func.count())
            .select_from(TierPolicyModel)
            .where(TierPolicyModel.is_active == True)  # noqa: E712
        )
    ).scalar() or 0
    composite_policies = (
        await session.execute(
            select(func.count())
            .select_from(TierPolicyModel)
            .where(TierPolicyModel.policy_type == TierPolicyType.COMPOSITE.value)
        )
    ).scalar() or 0

    # Count migrations
    total_migrations = (
        await session.execute(select(func.count()).select_from(TierMigrationHistoryModel))
    ).scalar() or 0
    successful_migrations = (
        await session.execute(
            select(func.count())
            .select_from(TierMigrationHistoryModel)
            .where(TierMigrationHistoryModel.status == "completed")
        )
    ).scalar() or 0
    failed_migrations = (
        await session.execute(
            select(func.count())
            .select_from(TierMigrationHistoryModel)
            .where(TierMigrationHistoryModel.status == "failed")
        )
    ).scalar() or 0

    # Total bytes migrated
    total_bytes_migrated = (
        await session.execute(
            select(func.sum(TierMigrationHistoryModel.size_bytes))
            .where(TierMigrationHistoryModel.status == "completed")
        )
    ).scalar() or 0

    # Per-tier statistics
    tier_stats: list[TierStatistics] = []
    tiers_result = await session.execute(select(StorageTierModel))
    for tier in tiers_result.scalars():
        # Count policies for this tier
        policy_count = (
            await session.execute(
                select(func.count())
                .select_from(TierPolicyModel)
                .where(TierPolicyModel.from_tier_id == tier.id)
            )
        ).scalar() or 0

        tier_stats.append(
            TierStatistics(
                tier_id=tier.id,
                tier_name=tier.name,
                tier_type=TierTypeEnum(tier.tier_type),
                item_count=0,  # Would need to track items per tier
                total_size_bytes=0,
                total_size_gb=0.0,
                estimated_cost=None,
                policy_count=policy_count,
            )
        )

    return TieringStatistics(
        total_tiers=total_tiers,
        active_tiers=active_tiers,
        total_policies=total_policies,
        active_policies=active_policies,
        composite_policies=composite_policies,
        total_migrations=total_migrations,
        successful_migrations=successful_migrations,
        failed_migrations=failed_migrations,
        total_bytes_migrated=total_bytes_migrated,
        tier_stats=tier_stats,
    )


# =============================================================================
# Policy Execution Endpoints
# =============================================================================


@router.post("/policies/{policy_id}/execute", response_model=PolicyExecutionResponse)
async def execute_policy(
    policy_id: str,
    request: PolicyExecutionRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> PolicyExecutionResponse:
    """Execute a tier policy to migrate eligible items.

    This endpoint triggers the actual migration of items based on the policy
    rules. Use dry_run=True to preview what would be migrated without making
    actual changes.

    Args:
        policy_id: Policy ID to execute.
        request: Execution options (dry_run, batch_size).
        session: Database session.

    Returns:
        Execution result with migration details.
    """
    from ..core.tiering import TieringService

    dry_run = request.dry_run if request else False
    batch_size = request.batch_size if request else 100

    service = TieringService(session)

    try:
        result = await service.execute_policy(
            policy_id=policy_id,
            dry_run=dry_run,
            batch_size=batch_size,
        )

        return PolicyExecutionResponse(
            policy_id=policy_id,
            dry_run=result.dry_run,
            start_time=result.start_time,
            end_time=result.end_time,
            duration_seconds=result.duration_seconds,
            items_scanned=result.items_scanned,
            items_migrated=result.items_migrated,
            items_failed=result.items_failed,
            bytes_migrated=result.bytes_migrated,
            success_rate=result.success_rate,
            errors=result.errors,
            migrations=[
                MigrationItemResponse(
                    item_id=m.item_id,
                    from_tier=m.from_tier,
                    to_tier=m.to_tier,
                    success=m.success,
                    size_bytes=m.size_bytes,
                    error_message=m.error_message,
                    duration_ms=m.duration_ms,
                )
                for m in result.migrations
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy execution failed: {str(e)}")


@router.post("/items/{item_id}/migrate", response_model=MigrationItemResponse)
async def migrate_item(
    item_id: str,
    request: MigrateItemRequest,
    session: AsyncSession = Depends(get_session),
) -> MigrationItemResponse:
    """Migrate a single item between tiers.

    Args:
        item_id: Item ID to migrate.
        request: Migration request with source and destination tiers.
        session: Database session.

    Returns:
        Migration result.
    """
    from ..core.tiering import TieringService

    service = TieringService(session)

    try:
        result = await service.migrate_item(
            item_id=item_id,
            from_tier_id=request.from_tier_id,
            to_tier_id=request.to_tier_id,
        )

        return MigrationItemResponse(
            item_id=result.item_id,
            from_tier=result.from_tier,
            to_tier=result.to_tier,
            success=result.success,
            size_bytes=result.size_bytes,
            error_message=result.error_message,
            duration_ms=result.duration_ms,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")


@router.post("/items/{item_id}/access", response_model=MessageResponse)
async def record_item_access(
    item_id: str,
    tier_id: str = Query(..., description="Current tier ID of the item"),
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Record an access to an item for intelligent tiering.

    Call this when an item is accessed to track access patterns for
    access-based tiering policies.

    Args:
        item_id: Accessed item ID.
        tier_id: Current tier ID.
        session: Database session.

    Returns:
        Success message.
    """
    from ..core.tiering import TieringService

    service = TieringService(session)
    await service.record_access(item_id, tier_id)

    return MessageResponse(message=f"Access recorded for item '{item_id}'")


@router.post("/process", response_model=ProcessPoliciesResponse)
async def process_all_policies(
    session: AsyncSession = Depends(get_session),
) -> ProcessPoliciesResponse:
    """Process all active tiering policies.

    This endpoint triggers evaluation and execution of all active policies.
    Use this for manual triggering or testing. In production, this is typically
    called by the background scheduler.

    Returns:
        Summary of all policy executions.
    """
    from ..core.tiering import TieringService

    service = TieringService(session)

    try:
        results = await service.process_due_policies()

        total_scanned = sum(r.items_scanned for r in results)
        total_migrated = sum(r.items_migrated for r in results)
        total_failed = sum(r.items_failed for r in results)
        total_bytes = sum(r.bytes_migrated for r in results)
        all_errors = [e for r in results for e in r.errors]

        return ProcessPoliciesResponse(
            policies_executed=len(results),
            total_items_scanned=total_scanned,
            total_items_migrated=total_migrated,
            total_items_failed=total_failed,
            total_bytes_migrated=total_bytes,
            errors=all_errors,
            policy_results=[
                PolicyExecutionSummary(
                    items_scanned=r.items_scanned,
                    items_migrated=r.items_migrated,
                    items_failed=r.items_failed,
                    bytes_migrated=r.bytes_migrated,
                    duration_seconds=r.duration_seconds,
                    success_rate=r.success_rate,
                    errors=r.errors,
                )
                for r in results
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy processing failed: {str(e)}")


@router.get("/status", response_model=TieringStatusResponse)
async def get_tiering_status(
    session: AsyncSession = Depends(get_session),
) -> TieringStatusResponse:
    """Get the current tiering system status.

    Returns information about truthound integration, active configurations,
    and system health.
    """
    from ..core.tiering import get_tiering_adapter

    adapter = get_tiering_adapter()

    # Get active config
    config_result = await session.execute(
        select(TieringConfigModel).where(TieringConfigModel.is_active == True)  # noqa: E712
    )
    active_config = config_result.scalar_one_or_none()

    # Get counts
    active_tiers = (
        await session.execute(
            select(func.count())
            .select_from(StorageTierModel)
            .where(StorageTierModel.is_active == True)  # noqa: E712
        )
    ).scalar() or 0

    active_policies = (
        await session.execute(
            select(func.count())
            .select_from(TierPolicyModel)
            .where(TierPolicyModel.is_active == True)  # noqa: E712
        )
    ).scalar() or 0

    # Recent migrations
    recent_migrations = (
        await session.execute(
            select(func.count())
            .select_from(TierMigrationHistoryModel)
            .where(
                TierMigrationHistoryModel.started_at
                >= func.datetime("now", "-24 hours")
            )
        )
    ).scalar() or 0

    return TieringStatusResponse(
        truthound_available=adapter.is_available,
        tiering_enabled=active_config is not None and active_config.is_active,
        active_config_id=active_config.id if active_config else None,
        active_config_name=active_config.name if active_config else None,
        check_interval_hours=active_config.check_interval_hours if active_config else None,
        active_tiers=active_tiers,
        active_policies=active_policies,
        migrations_last_24h=recent_migrations,
    )
