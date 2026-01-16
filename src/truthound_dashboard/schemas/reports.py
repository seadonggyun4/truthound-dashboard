"""Report-related Pydantic schemas.

This module defines schemas for report generation API operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from .base import BaseSchema

# Report format types
ReportFormatType = Literal["html", "csv", "json", "markdown", "pdf"]

# Report theme types
ReportThemeType = Literal["light", "dark", "professional", "minimal", "high_contrast"]


class ReportGenerateRequest(BaseSchema):
    """Request to generate a validation report.

    All parameters are optional with sensible defaults.
    """

    format: ReportFormatType = Field(
        default="html",
        description="Output format for the report",
    )
    theme: ReportThemeType = Field(
        default="professional",
        description="Visual theme for the report (mainly for HTML)",
    )
    title: str | None = Field(
        default=None,
        description="Custom title for the report. Auto-generated if not provided.",
    )
    include_samples: bool = Field(
        default=True,
        description="Include sample problematic values in the report",
    )
    include_statistics: bool = Field(
        default=True,
        description="Include data statistics section",
    )
    custom_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata to include in the report",
    )


class ReportMetadataResponse(BaseSchema):
    """Report metadata returned in API responses."""

    title: str = Field(..., description="Report title")
    generated_at: datetime = Field(..., description="Generation timestamp")
    source_name: str | None = Field(default=None, description="Data source name")
    source_id: str | None = Field(default=None, description="Data source ID")
    validation_id: str | None = Field(default=None, description="Validation ID")
    theme: str = Field(..., description="Visual theme used")
    format: str = Field(..., description="Output format")


class ReportResponse(BaseSchema):
    """Response for report generation.

    Contains metadata about the generated report and download info.
    Note: The actual content is returned as a file download, not in this response.
    """

    filename: str = Field(..., description="Suggested filename for download")
    content_type: str = Field(..., description="MIME content type")
    size_bytes: int = Field(..., description="Size of report content in bytes")
    generation_time_ms: int = Field(
        ..., description="Time taken to generate in milliseconds"
    )
    metadata: ReportMetadataResponse = Field(..., description="Report metadata")


class AvailableFormatsResponse(BaseSchema):
    """Response listing available report formats."""

    formats: list[str] = Field(
        ...,
        description="List of available format names",
        examples=[["html", "csv", "json", "markdown"]],
    )
    themes: list[str] = Field(
        ...,
        description="List of available theme names",
        examples=[["light", "dark", "professional", "minimal", "high_contrast"]],
    )
