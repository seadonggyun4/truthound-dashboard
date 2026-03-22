"""API dependencies for dependency injection.

This module provides FastAPI dependencies for injecting services
and database sessions into route handlers.

Example:
    @router.get("/sources")
    async def list_sources(
        service: SourceService = Depends(get_source_service)
    ):
        return await service.list()
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.core import (
    ArtifactService,
    AuthService,
    AuthorizationService,
    ControlPlaneContext,
    DriftService,
    HistoryService,
    IncidentQueueService,
    IncidentService,
    MaskService,
    OverviewService,
    PIIScanService,
    ProfileService,
    RuleService,
    SavedViewService,
    ScheduleService,
    SchemaService,
    SourceService,
    ValidationService,
)
from truthound_dashboard.core.schema_evolution import SchemaEvolutionService
from truthound_dashboard.core.rule_generator import RuleGeneratorService
from truthound_dashboard.core.profile_comparison import ProfileComparisonService
from truthound_dashboard.core.lineage import LineageService
from truthound_dashboard.core.anomaly import AnomalyDetectionService
from truthound_dashboard.core.anomaly_explainer import AnomalyExplainerService
from truthound_dashboard.core.openlineage import OpenLineageEmitterService, OpenLineageWebhookService
from truthound_dashboard.db import get_db_session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency.

    Yields:
        AsyncSession for database operations.
    """
    async for session in get_db_session():
        yield session


# Type alias for session dependency
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_source_service(session: SessionDep) -> SourceService:
    """Get source service dependency.

    Args:
        session: Database session.

    Returns:
        SourceService instance.
    """
    return SourceService(session)


async def get_auth_service(session: SessionDep) -> AuthService:
    """Get auth service dependency."""
    return AuthService(session)


async def get_saved_view_service(session: SessionDep) -> SavedViewService:
    """Get saved view service dependency."""
    return SavedViewService(session)


async def get_overview_service(session: SessionDep) -> OverviewService:
    """Get overview service dependency."""
    return OverviewService(session)


async def get_authorization_service(session: SessionDep) -> AuthorizationService:
    """Get authorization service dependency."""
    return AuthorizationService(session)


async def get_artifact_service(session: SessionDep) -> ArtifactService:
    """Get artifact service dependency."""
    return ArtifactService(session)


async def get_incident_service(session: SessionDep) -> IncidentService:
    """Get incident workbench dependency."""
    return IncidentService(session)


async def get_incident_queue_service(session: SessionDep) -> IncidentQueueService:
    """Get incident queue service dependency."""
    return IncidentQueueService(session)


async def get_control_plane_context(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    x_truthound_session: Annotated[str | None, Header(alias="X-Truthound-Session")] = None,
) -> ControlPlaneContext:
    """Resolve current user/workspace context."""
    try:
        return await auth_service.resolve_context(x_truthound_session)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def require_permission(permission_key: str):
    """Route-level permission dependency helper."""

    async def _require_permission(
        context: Annotated[ControlPlaneContext, Depends(get_control_plane_context)],
        authz: Annotated[AuthorizationService, Depends(get_authorization_service)],
    ) -> ControlPlaneContext:
        allowed = await authz.has_permission(
            user_id=context.user.id,
            workspace_id=context.workspace.id,
            permission_key=permission_key,
        )
        if not allowed:
            raise HTTPException(status_code=403, detail=f"Missing permission: {permission_key}")
        return context

    return _require_permission


async def get_validation_service(session: SessionDep) -> ValidationService:
    """Get validation service dependency.

    Args:
        session: Database session.

    Returns:
        ValidationService instance.
    """
    return ValidationService(session)


async def get_schema_service(session: SessionDep) -> SchemaService:
    """Get schema service dependency.

    Args:
        session: Database session.

    Returns:
        SchemaService instance.
    """
    return SchemaService(session)


async def get_profile_service(session: SessionDep) -> ProfileService:
    """Get profile service dependency.

    Args:
        session: Database session.

    Returns:
        ProfileService instance.
    """
    return ProfileService(session)


async def get_rule_service(session: SessionDep) -> RuleService:
    """Get rule service dependency.

    Args:
        session: Database session.

    Returns:
        RuleService instance.
    """
    return RuleService(session)


async def get_history_service(session: SessionDep) -> HistoryService:
    """Get history service dependency.

    Args:
        session: Database session.

    Returns:
        HistoryService instance.
    """
    return HistoryService(session)


async def get_drift_service(session: SessionDep) -> DriftService:
    """Get drift service dependency.

    Args:
        session: Database session.

    Returns:
        DriftService instance.
    """
    return DriftService(session)


async def get_schedule_service(session: SessionDep) -> ScheduleService:
    """Get schedule service dependency.

    Args:
        session: Database session.

    Returns:
        ScheduleService instance.
    """
    return ScheduleService(session)


async def get_pii_scan_service(session: SessionDep) -> PIIScanService:
    """Get PII scan service dependency.

    Args:
        session: Database session.

    Returns:
        PIIScanService instance.
    """
    return PIIScanService(session)


async def get_mask_service(session: SessionDep) -> MaskService:
    """Get mask service dependency.

    Args:
        session: Database session.

    Returns:
        MaskService instance.
    """
    return MaskService(session)


async def get_schema_evolution_service(session: SessionDep) -> SchemaEvolutionService:
    """Get schema evolution service dependency.

    Args:
        session: Database session.

    Returns:
        SchemaEvolutionService instance.
    """
    return SchemaEvolutionService(session)


async def get_rule_generator_service(session: SessionDep) -> RuleGeneratorService:
    """Get rule generator service dependency.

    Args:
        session: Database session.

    Returns:
        RuleGeneratorService instance.
    """
    return RuleGeneratorService(session)


async def get_profile_comparison_service(session: SessionDep) -> ProfileComparisonService:
    """Get profile comparison service dependency.

    Args:
        session: Database session.

    Returns:
        ProfileComparisonService instance.
    """
    return ProfileComparisonService(session)


async def get_lineage_service(session: SessionDep) -> LineageService:
    """Get lineage service dependency.

    Args:
        session: Database session.

    Returns:
        LineageService instance.
    """
    return LineageService(session)


async def get_anomaly_detection_service(session: SessionDep) -> AnomalyDetectionService:
    """Get anomaly detection service dependency.

    Args:
        session: Database session.

    Returns:
        AnomalyDetectionService instance.
    """
    return AnomalyDetectionService(session)


async def get_anomaly_explainer_service(session: SessionDep) -> AnomalyExplainerService:
    """Get anomaly explainer service dependency.

    Args:
        session: Database session.

    Returns:
        AnomalyExplainerService instance for SHAP/LIME explanations.
    """
    return AnomalyExplainerService(session)


async def get_openlineage_emitter_service(session: SessionDep) -> OpenLineageEmitterService:
    """Get OpenLineage emitter service dependency.

    Args:
        session: Database session.

    Returns:
        OpenLineageEmitterService instance.
    """
    return OpenLineageEmitterService(session)


async def get_openlineage_webhook_service(session: SessionDep) -> OpenLineageWebhookService:
    """Get OpenLineage webhook service dependency.

    Args:
        session: Database session.

    Returns:
        OpenLineageWebhookService instance.
    """
    return OpenLineageWebhookService(session)


# Type aliases for service dependencies
SourceServiceDep = Annotated[SourceService, Depends(get_source_service)]
ValidationServiceDep = Annotated[ValidationService, Depends(get_validation_service)]
SchemaServiceDep = Annotated[SchemaService, Depends(get_schema_service)]
ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]
RuleServiceDep = Annotated[RuleService, Depends(get_rule_service)]
HistoryServiceDep = Annotated[HistoryService, Depends(get_history_service)]
DriftServiceDep = Annotated[DriftService, Depends(get_drift_service)]
ScheduleServiceDep = Annotated[ScheduleService, Depends(get_schedule_service)]
PIIScanServiceDep = Annotated[PIIScanService, Depends(get_pii_scan_service)]
MaskServiceDep = Annotated[MaskService, Depends(get_mask_service)]
SchemaEvolutionServiceDep = Annotated[
    SchemaEvolutionService, Depends(get_schema_evolution_service)
]
RuleGeneratorServiceDep = Annotated[
    RuleGeneratorService, Depends(get_rule_generator_service)
]
ProfileComparisonServiceDep = Annotated[
    ProfileComparisonService, Depends(get_profile_comparison_service)
]
LineageServiceDep = Annotated[LineageService, Depends(get_lineage_service)]
AnomalyDetectionServiceDep = Annotated[
    AnomalyDetectionService, Depends(get_anomaly_detection_service)
]
AnomalyExplainerServiceDep = Annotated[
    AnomalyExplainerService, Depends(get_anomaly_explainer_service)
]
OpenLineageEmitterServiceDep = Annotated[
    OpenLineageEmitterService, Depends(get_openlineage_emitter_service)
]
OpenLineageWebhookServiceDep = Annotated[
    OpenLineageWebhookService, Depends(get_openlineage_webhook_service)
]

AuthorizationServiceDep = Annotated[
    AuthorizationService, Depends(get_authorization_service)
]
ArtifactServiceDep = Annotated[
    ArtifactService, Depends(get_artifact_service)
]
IncidentServiceDep = Annotated[
    IncidentService, Depends(get_incident_service)
]
IncidentQueueServiceDep = Annotated[
    IncidentQueueService, Depends(get_incident_queue_service)
]
