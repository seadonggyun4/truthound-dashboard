"""Reports API endpoints.

This module provides endpoints for generating and downloading validation reports.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import Response

from truthound_dashboard.core.reporters import (
    ReportFormat,
    ReportTheme,
    generate_report,
    get_available_formats,
)
from truthound_dashboard.schemas import (
    AvailableFormatsResponse,
    ReportGenerateRequest,
    ReportMetadataResponse,
    ReportResponse,
)

from .deps import ValidationServiceDep

router = APIRouter()


@router.get(
    "/formats",
    response_model=AvailableFormatsResponse,
    summary="Get available report formats",
    description="List all available report formats and themes",
)
async def list_formats() -> AvailableFormatsResponse:
    """Get list of available report formats and themes.

    Returns:
        Available formats and themes.
    """
    formats = get_available_formats()
    themes = [t.value for t in ReportTheme]

    return AvailableFormatsResponse(formats=formats, themes=themes)


@router.post(
    "/validations/{validation_id}/report",
    response_model=ReportResponse,
    summary="Generate validation report metadata",
    description="Generate a report and return metadata (use download endpoint for content)",
)
async def generate_validation_report(
    service: ValidationServiceDep,
    validation_id: Annotated[str, Path(description="Validation ID")],
    request: ReportGenerateRequest,
) -> ReportResponse:
    """Generate a validation report.

    This endpoint returns report metadata. Use the download endpoint
    to get the actual report content.

    Args:
        service: Injected validation service.
        validation_id: Validation to generate report for.
        request: Report generation options.

    Returns:
        Report metadata and download information.

    Raises:
        HTTPException: 404 if validation not found.
        HTTPException: 400 if format is not supported.
    """
    # Get validation
    validation = await service.get_validation(validation_id)
    if validation is None:
        raise HTTPException(status_code=404, detail="Validation not found")

    try:
        # Generate report
        result = await generate_report(
            validation,
            format=request.format,
            theme=request.theme,
            title=request.title,
            include_samples=request.include_samples,
            include_statistics=request.include_statistics,
            custom_metadata=request.custom_metadata,
        )

        return ReportResponse(
            filename=result.filename,
            content_type=result.content_type,
            size_bytes=result.size_bytes,
            generation_time_ms=result.generation_time_ms,
            metadata=ReportMetadataResponse(
                title=result.metadata.title,
                generated_at=result.metadata.generated_at,
                source_name=result.metadata.source_name,
                source_id=result.metadata.source_id,
                validation_id=result.metadata.validation_id,
                theme=result.metadata.theme.value,
                format=result.metadata.format.value,
            ),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/validations/{validation_id}/download",
    summary="Download validation report",
    description="Generate and download a validation report as a file",
    responses={
        200: {
            "description": "Report file",
            "content": {
                "text/html": {},
                "text/csv": {},
                "application/json": {},
                "text/markdown": {},
                "application/pdf": {},
            },
        },
        404: {"description": "Validation not found"},
        400: {"description": "Invalid format"},
    },
)
async def download_validation_report(
    service: ValidationServiceDep,
    validation_id: Annotated[str, Path(description="Validation ID")],
    format: Annotated[str, Query(description="Report format")] = "html",
    theme: Annotated[str, Query(description="Visual theme")] = "professional",
    include_samples: Annotated[
        bool, Query(description="Include sample values")
    ] = True,
    include_statistics: Annotated[
        bool, Query(description="Include statistics")
    ] = True,
) -> Response:
    """Download a validation report.

    Generates and returns the report as a downloadable file.

    Args:
        service: Injected validation service.
        validation_id: Validation to generate report for.
        format: Report format (html, csv, json, markdown).
        theme: Visual theme for the report.
        include_samples: Include sample problematic values.
        include_statistics: Include data statistics.

    Returns:
        Report file as download response.

    Raises:
        HTTPException: 404 if validation not found.
        HTTPException: 400 if format is not supported.
    """
    # Get validation
    validation = await service.get_validation(validation_id)
    if validation is None:
        raise HTTPException(status_code=404, detail="Validation not found")

    try:
        # Generate report
        result = await generate_report(
            validation,
            format=format,
            theme=theme,
            include_samples=include_samples,
            include_statistics=include_statistics,
        )

        # Return as file download
        content = result.content
        if isinstance(content, str):
            content = content.encode("utf-8")

        return Response(
            content=content,
            media_type=result.content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{result.filename}"',
                "Content-Length": str(result.size_bytes),
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/validations/{validation_id}/preview",
    summary="Preview validation report",
    description="Generate and return report for inline viewing (not as download)",
    responses={
        200: {
            "description": "Report content for preview",
            "content": {
                "text/html": {},
                "text/csv": {},
                "application/json": {},
                "text/markdown": {},
            },
        },
        404: {"description": "Validation not found"},
        400: {"description": "Invalid format"},
    },
)
async def preview_validation_report(
    service: ValidationServiceDep,
    validation_id: Annotated[str, Path(description="Validation ID")],
    format: Annotated[str, Query(description="Report format")] = "html",
    theme: Annotated[str, Query(description="Visual theme")] = "professional",
) -> Response:
    """Preview a validation report inline.

    Similar to download but without Content-Disposition header,
    allowing browser to render the content inline.

    Args:
        service: Injected validation service.
        validation_id: Validation to generate report for.
        format: Report format (html, csv, json, markdown).
        theme: Visual theme for the report.

    Returns:
        Report content for inline viewing.

    Raises:
        HTTPException: 404 if validation not found.
        HTTPException: 400 if format is not supported.
    """
    # Get validation
    validation = await service.get_validation(validation_id)
    if validation is None:
        raise HTTPException(status_code=404, detail="Validation not found")

    try:
        # Generate report
        result = await generate_report(
            validation,
            format=format,
            theme=theme,
            include_samples=True,
            include_statistics=True,
        )

        # Return for inline viewing
        content = result.content
        if isinstance(content, str):
            content = content.encode("utf-8")

        return Response(
            content=content,
            media_type=result.content_type,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
