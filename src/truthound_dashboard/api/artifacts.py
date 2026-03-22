"""Canonical artifact API endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path as ApiPath, Query
from fastapi.responses import FileResponse, RedirectResponse

from truthound_dashboard.schemas.artifacts import (
    ArtifactCapabilitiesResponse,
    ArtifactGenerateRequest,
    ArtifactListResponse,
    ArtifactLocaleInfo,
    ArtifactResponse,
    ArtifactStatistics,
    DataDocsGenerateRequest,
)
from truthound_dashboard.core.reporters import ReportTheme, get_available_formats
from truthound_dashboard.core.reporters.registry import get_report_locales

from .deps import ArtifactServiceDep, ValidationServiceDep, require_permission

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


def _artifact_response(artifact: object) -> ArtifactResponse:
    response = ArtifactResponse.from_model(artifact)
    response.download_url = f"/api/v1/artifacts/{artifact.id}/download"
    return response


@router.get("/capabilities", response_model=ArtifactCapabilitiesResponse)
async def get_artifact_capabilities() -> ArtifactCapabilitiesResponse:
    return ArtifactCapabilitiesResponse(
        formats=get_available_formats(),
        themes=[theme.value for theme in ReportTheme],
        locales=[
            ArtifactLocaleInfo(
                code=loc["code"],
                english_name=loc["english_name"],
                native_name=loc["native_name"],
                flag=loc["flag"],
                rtl=loc["rtl"],
            )
            for loc in get_report_locales()
        ],
        artifact_types=["report", "datadocs"],
    )


@router.get("", response_model=ArtifactListResponse)
async def list_artifacts(
    service: ArtifactServiceDep,
    context=Depends(require_permission("artifacts:read")),
    workspace_id: Annotated[str | None, Query()] = None,
    saved_view_id: Annotated[str | None, Query()] = None,
    source_id: Annotated[str | None, Query()] = None,
    validation_id: Annotated[str | None, Query()] = None,
    artifact_type: Annotated[str | None, Query()] = None,
    format: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    include_expired: Annotated[bool, Query()] = False,
    search: Annotated[str | None, Query()] = None,
    offset: Annotated[int | None, Query(ge=0)] = None,
    limit: Annotated[int | None, Query(ge=1, le=100)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ArtifactListResponse:
    resolved_limit = limit or page_size
    resolved_page = page
    if offset is not None:
        resolved_page = (offset // resolved_limit) + 1

    artifacts, total = await service.list_artifacts(
        workspace_id=workspace_id or context.workspace.id,
        saved_view_id=saved_view_id,
        source_id=source_id,
        validation_id=validation_id,
        artifact_type=artifact_type,
        format=format,
        status=status,
        include_expired=include_expired,
        search=search,
        page=resolved_page,
        page_size=resolved_limit,
    )
    return ArtifactListResponse(
        data=[_artifact_response(artifact) for artifact in artifacts],
        total=total,
        offset=offset if offset is not None else (resolved_page - 1) * resolved_limit,
        limit=resolved_limit,
    )


@router.get("/statistics", response_model=ArtifactStatistics)
async def get_artifact_statistics(
    service: ArtifactServiceDep,
    context=Depends(require_permission("artifacts:read")),
) -> ArtifactStatistics:
    return ArtifactStatistics.model_validate(
        await service.statistics(workspace_id=context.workspace.id)
    )


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: Annotated[str, ApiPath()],
    service: ArtifactServiceDep,
    context=Depends(require_permission("artifacts:read")),
) -> ArtifactResponse:
    artifact = await service.get_artifact(
        artifact_id=artifact_id,
        workspace_id=context.workspace.id,
    )
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return _artifact_response(artifact)


@router.delete("/{artifact_id}", response_model=dict[str, str])
async def delete_artifact(
    artifact_id: Annotated[str, ApiPath()],
    service: ArtifactServiceDep,
    context=Depends(require_permission("artifacts:write")),
) -> dict[str, str]:
    deleted = await service.delete_artifact(
        artifact_id=artifact_id,
        workspace_id=context.workspace.id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {"message": "Artifact deleted"}


@router.post("/cleanup", response_model=dict[str, int])
async def cleanup_expired_artifacts(
    service: ArtifactServiceDep,
    context=Depends(require_permission("artifacts:write")),
) -> dict[str, int]:
    deleted = await service.cleanup_expired(workspace_id=context.workspace.id)
    return {"deleted": deleted}


@router.get("/{artifact_id}/download")
async def download_artifact(
    artifact_id: Annotated[str, ApiPath()],
    service: ArtifactServiceDep,
    context=Depends(require_permission("artifacts:read")),
):
    artifact = await service.record_download(
        artifact_id=artifact_id,
        workspace_id=context.workspace.id,
    )
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    if artifact.external_url:
        return RedirectResponse(url=artifact.external_url)
    if not artifact.file_path:
        raise HTTPException(status_code=404, detail="Artifact file is unavailable")
    file_path = Path(artifact.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Artifact file is unavailable")
    return FileResponse(path=file_path, filename=file_path.name)


@router.post("/validations/{validation_id}/report", response_model=ArtifactResponse, status_code=201)
async def generate_report_artifact(
    validation_id: Annotated[str, ApiPath()],
    payload: ArtifactGenerateRequest,
    service: ArtifactServiceDep,
    validation_service: ValidationServiceDep,
    context=Depends(require_permission("artifacts:write")),
) -> ArtifactResponse:
    validation = await validation_service.get_validation(validation_id, with_source=True)
    if validation is None:
        raise HTTPException(status_code=404, detail="Validation not found")
    artifact = await service.generate_report_artifact(
        workspace_id=context.workspace.id,
        validation=validation,
        format=payload.format,
        theme=payload.theme or "professional",
        locale=payload.locale,
        title=payload.title,
        include_samples=payload.include_samples,
        include_statistics=payload.include_statistics,
        custom_metadata=payload.custom_metadata,
    )
    return _artifact_response(artifact)


@router.post("/validations/{validation_id}/datadocs", response_model=ArtifactResponse, status_code=201)
async def generate_datadocs_artifact(
    validation_id: Annotated[str, ApiPath()],
    payload: DataDocsGenerateRequest,
    service: ArtifactServiceDep,
    validation_service: ValidationServiceDep,
    context=Depends(require_permission("artifacts:write")),
) -> ArtifactResponse:
    validation = await validation_service.get_validation(validation_id, with_source=True)
    if validation is None:
        raise HTTPException(status_code=404, detail="Validation not found")
    artifact = await service.generate_datadocs_artifact(
        workspace_id=context.workspace.id,
        validation=validation,
        theme=payload.theme or "professional",
        title=payload.title,
    )
    return _artifact_response(artifact)
