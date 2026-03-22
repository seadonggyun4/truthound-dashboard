"""Canonical artifact schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from .base import BaseSchema, IDMixin, ListResponseWrapper, TimestampMixin


class ArtifactGenerateRequest(BaseSchema):
    format: str = Field(default="html")
    theme: str | None = Field(default="professional")
    locale: str = Field(default="en")
    title: str | None = Field(default=None)
    include_samples: bool = Field(default=True)
    include_statistics: bool = Field(default=True)
    custom_metadata: dict[str, Any] | None = Field(default=None)


class DataDocsGenerateRequest(BaseSchema):
    theme: str | None = Field(default="professional")
    title: str | None = Field(default=None)


class ArtifactLocaleInfo(BaseSchema):
    code: str
    english_name: str
    native_name: str
    flag: str
    rtl: bool = False


class ArtifactCapabilitiesResponse(BaseSchema):
    formats: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    locales: list[ArtifactLocaleInfo] = Field(default_factory=list)
    artifact_types: list[str] = Field(default_factory=list)


class ArtifactResponse(BaseSchema, IDMixin, TimestampMixin):
    workspace_id: str | None = None
    source_id: str | None = None
    validation_id: str | None = None
    artifact_type: str
    format: str
    status: str
    title: str
    description: str | None = None
    file_path: str | None = None
    external_url: str | None = None
    file_size: int | None = None
    content_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    generation_time_ms: float | None = None
    expires_at: datetime | None = None
    downloaded_count: int = 0
    last_downloaded_at: datetime | None = None
    locale: str = "en"
    theme: str | None = None
    source_name: str | None = None
    validation_status: str | None = None
    is_expired: bool = False
    download_url: str | None = None

    @classmethod
    def from_model(cls, model: Any) -> "ArtifactResponse":
        return cls(
            id=str(model.id),
            workspace_id=str(model.workspace_id) if model.workspace_id else None,
            source_id=str(model.source_id) if model.source_id else None,
            validation_id=str(model.validation_id) if model.validation_id else None,
            artifact_type=model.artifact_type,
            format=model.format,
            status=model.status,
            title=model.title,
            description=model.description,
            file_path=model.file_path,
            external_url=model.external_url,
            file_size=model.file_size,
            content_hash=model.content_hash,
            metadata=model.artifact_metadata or {},
            error_message=model.error_message,
            generation_time_ms=model.generation_time_ms,
            expires_at=model.expires_at,
            downloaded_count=model.downloaded_count,
            last_downloaded_at=model.last_downloaded_at,
            locale=model.locale,
            theme=model.theme,
            source_name=model.source.name if getattr(model, "source", None) else None,
            validation_status=model.validation.status if getattr(model, "validation", None) else None,
            is_expired=model.is_expired,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class ArtifactListResponse(ListResponseWrapper[ArtifactResponse]):
    pass


class ArtifactStatistics(BaseSchema):
    total_artifacts: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)
    total_downloads: int = 0
    total_size_bytes: int = 0
