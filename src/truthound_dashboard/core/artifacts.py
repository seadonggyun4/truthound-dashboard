"""Canonical artifact service for reports and Data Docs."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Any, Literal, cast

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from truthound_dashboard.config import get_settings
from truthound_dashboard.core.reporters import generate_report
from truthound_dashboard.db import ArtifactRecord, SavedView
from truthound_dashboard.db.models import Validation
from truthound_dashboard.time import utc_now


def _load_truthound_datadocs_runtime() -> tuple[type[Any], Callable[..., str]]:
    try:
        from truthound import ValidationRunResult
        from truthound.datadocs import (
            generate_validation_report as generate_validation_datadocs,
        )
    except Exception as exc:  # pragma: no cover - exercised via runtime integration
        raise RuntimeError(
            "truthound>=3.0 with Data Docs support is required for artifact generation"
        ) from exc

    return ValidationRunResult, generate_validation_datadocs


class ArtifactService:
    """Manage canonical artifact records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        settings = get_settings()
        settings.ensure_directories()
        self._artifacts_dir: Path = settings.artifacts_dir

    async def list_artifacts(
        self,
        *,
        workspace_id: str,
        saved_view_id: str | None = None,
        source_id: str | None = None,
        validation_id: str | None = None,
        artifact_type: str | None = None,
        format: str | None = None,
        status: str | None = None,
        include_expired: bool = False,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: Literal["asc", "desc"] = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ArtifactRecord], int]:
        saved_filters = await self._saved_view_filters(
            workspace_id=workspace_id,
            saved_view_id=saved_view_id,
        )
        query = select(ArtifactRecord).options(
            selectinload(ArtifactRecord.source),
            selectinload(ArtifactRecord.validation),
        )
        if workspace_id:
            query = query.where(or_(ArtifactRecord.workspace_id == workspace_id, ArtifactRecord.workspace_id.is_(None)))

        conditions = []
        if source_id or saved_filters.get("source_id"):
            conditions.append(ArtifactRecord.source_id == (source_id or saved_filters.get("source_id")))
        if validation_id or saved_filters.get("validation_id"):
            conditions.append(
                ArtifactRecord.validation_id == (validation_id or saved_filters.get("validation_id"))
            )
        if artifact_type or saved_filters.get("artifact_type"):
            conditions.append(ArtifactRecord.artifact_type == (artifact_type or saved_filters.get("artifact_type")))
        if format or saved_filters.get("format"):
            conditions.append(ArtifactRecord.format == (format or saved_filters.get("format")))
        if status or saved_filters.get("status"):
            conditions.append(ArtifactRecord.status == (status or saved_filters.get("status")))
        if not include_expired:
            conditions.append(
                or_(ArtifactRecord.expires_at.is_(None), ArtifactRecord.expires_at > utc_now())
            )
        if search or saved_filters.get("search"):
            conditions.append(ArtifactRecord.title.ilike(f"%{search or saved_filters.get('search')}%"))

        if conditions:
            query = query.where(and_(*conditions))

        total = await self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        sort_column = getattr(ArtifactRecord, sort_by, ArtifactRecord.created_at)
        query = query.order_by(desc(sort_column) if sort_order == "desc" else sort_column)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def _saved_view_filters(
        self,
        *,
        workspace_id: str,
        saved_view_id: str | None,
    ) -> dict[str, Any]:
        if not saved_view_id:
            return {}
        result = await self.session.execute(
            select(SavedView).where(
                SavedView.id == saved_view_id,
                SavedView.workspace_id == workspace_id,
                SavedView.scope == "artifacts",
            )
        )
        view = result.scalar_one_or_none()
        if view is None:
            return {}
        return dict(view.filters or {})

    async def get_artifact(self, *, artifact_id: str, workspace_id: str) -> ArtifactRecord | None:
        query = (
            select(ArtifactRecord)
            .options(
                selectinload(ArtifactRecord.source),
                selectinload(ArtifactRecord.validation),
            )
            .where(ArtifactRecord.id == artifact_id)
        )
        if workspace_id:
            query = query.where(
                or_(ArtifactRecord.workspace_id == workspace_id, ArtifactRecord.workspace_id.is_(None))
            )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def record_download(self, *, artifact_id: str, workspace_id: str) -> ArtifactRecord | None:
        artifact = await self.get_artifact(artifact_id=artifact_id, workspace_id=workspace_id)
        if artifact is None:
            return None
        artifact.increment_download()
        await self.session.flush()
        await self.session.refresh(artifact)
        return artifact

    async def delete_artifact(self, *, artifact_id: str, workspace_id: str) -> bool:
        artifact = await self.get_artifact(artifact_id=artifact_id, workspace_id=workspace_id)
        if artifact is None:
            return False
        if artifact.file_path:
            file_path = Path(artifact.file_path)
            if file_path.exists():
                file_path.unlink()
        await self.session.delete(artifact)
        return True

    async def cleanup_expired(self, *, workspace_id: str) -> int:
        artifacts, _ = await self.list_artifacts(
            workspace_id=workspace_id,
            include_expired=True,
            page=1,
            page_size=10_000,
        )
        deleted = 0
        for artifact in artifacts:
            if not artifact.is_expired:
                continue
            if artifact.file_path:
                file_path = Path(artifact.file_path)
                if file_path.exists():
                    file_path.unlink()
            await self.session.delete(artifact)
            deleted += 1
        return deleted

    async def generate_report_artifact(
        self,
        *,
        workspace_id: str,
        validation: Validation,
        format: str = "html",
        theme: str = "professional",
        locale: str = "en",
        title: str | None = None,
        include_samples: bool = True,
        include_statistics: bool = True,
        custom_metadata: dict[str, Any] | None = None,
        expires_in_days: int | None = 30,
    ) -> ArtifactRecord:
        artifact = await self._create_pending_artifact(
            workspace_id=workspace_id,
            source_id=validation.source_id,
            validation_id=validation.id,
            artifact_type="report",
            format=format,
            title=title or f"Validation Report {validation.id[:8]}",
            description="Generated validation report",
            locale=locale,
            theme=theme,
            metadata=custom_metadata or {},
            expires_in_days=expires_in_days,
        )

        started_at = utc_now()
        try:
            result = await generate_report(
                validation,
                format=format,
                theme=theme,
                locale=locale,
                title=title,
                include_samples=include_samples,
                include_statistics=include_statistics,
                custom_metadata=custom_metadata,
            )
            content_bytes = result.content.encode("utf-8") if isinstance(result.content, str) else result.content
            file_path = self._artifact_path(
                artifact_id=artifact.id,
                artifact_type="report",
                extension=Path(result.filename).suffix or f".{format}",
            )
            file_path.write_bytes(content_bytes)

            artifact.status = "completed"
            artifact.file_path = str(file_path)
            artifact.file_size = len(content_bytes)
            artifact.content_hash = hashlib.sha256(content_bytes).hexdigest()
            artifact.generation_time_ms = result.generation_time_ms or (
                (utc_now() - started_at).total_seconds() * 1000
            )
            artifact.artifact_metadata = {
                **artifact.artifact_metadata,
                "content_type": result.content_type,
                "filename": result.filename,
                "source_name": result.metadata.source_name,
                "validation_id": result.metadata.validation_id,
                "generated_at": result.metadata.generated_at.isoformat(),
            }
        except Exception as exc:
            artifact.status = "failed"
            artifact.error_message = str(exc)
        await self.session.flush()
        await self.session.refresh(artifact)
        return artifact

    async def generate_datadocs_artifact(
        self,
        *,
        workspace_id: str,
        validation: Validation,
        theme: str = "professional",
        title: str | None = None,
        expires_in_days: int | None = 30,
    ) -> ArtifactRecord:
        artifact = await self._create_pending_artifact(
            workspace_id=workspace_id,
            source_id=validation.source_id,
            validation_id=validation.id,
            artifact_type="datadocs",
            format="html",
            title=title or f"Data Docs {validation.id[:8]}",
            description="Generated validation Data Docs",
            locale="en",
            theme=theme,
            metadata={},
            expires_in_days=expires_in_days,
        )

        started_at = utc_now()
        try:
            if not validation.result_json:
                raise ValueError("Validation result is empty")
            ValidationRunResult, generate_validation_datadocs = _load_truthound_datadocs_runtime()
            run_result = ValidationRunResult.from_dict(validation.result_json)
            html_content = generate_validation_datadocs(
                run_result,
                title=title or "Truthound Validation Data Docs",
                theme=theme,
            )
            content_bytes = html_content.encode("utf-8")
            file_path = self._artifact_path(
                artifact_id=artifact.id,
                artifact_type="datadocs",
                extension=".html",
            )
            file_path.write_bytes(content_bytes)

            artifact.status = "completed"
            artifact.file_path = str(file_path)
            artifact.file_size = len(content_bytes)
            artifact.content_hash = hashlib.sha256(content_bytes).hexdigest()
            artifact.generation_time_ms = (utc_now() - started_at).total_seconds() * 1000
            artifact.artifact_metadata = {
                **artifact.artifact_metadata,
                "title": title or "Truthound Validation Data Docs",
            }
        except Exception as exc:
            artifact.status = "failed"
            artifact.error_message = str(exc)
        await self.session.flush()
        await self.session.refresh(artifact)
        return artifact

    async def statistics(self, *, workspace_id: str) -> dict[str, Any]:
        artifacts, _ = await self.list_artifacts(
            workspace_id=workspace_id,
            include_expired=True,
            page=1,
            page_size=10_000,
        )
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        total_size = 0
        total_downloads = 0
        for artifact in artifacts:
            by_type[artifact.artifact_type] = by_type.get(artifact.artifact_type, 0) + 1
            by_status[artifact.status] = by_status.get(artifact.status, 0) + 1
            total_size += artifact.file_size or 0
            total_downloads += artifact.downloaded_count
        return {
            "total_artifacts": len(artifacts),
            "by_type": by_type,
            "by_status": by_status,
            "total_downloads": total_downloads,
            "total_size_bytes": total_size,
        }

    async def _create_pending_artifact(
        self,
        *,
        workspace_id: str,
        source_id: str | None,
        validation_id: str | None,
        artifact_type: str,
        format: str,
        title: str,
        description: str | None,
        locale: str,
        theme: str | None,
        metadata: dict[str, Any],
        expires_in_days: int | None,
    ) -> ArtifactRecord:
        expires_at = None
        if expires_in_days:
            expires_at = utc_now() + timedelta(days=expires_in_days)
        artifact = ArtifactRecord(
            workspace_id=workspace_id,
            source_id=source_id,
            validation_id=validation_id,
            artifact_type=artifact_type,
            format=format,
            status="generating",
            title=title,
            description=description,
            artifact_metadata=metadata,
            locale=locale,
            theme=theme,
            expires_at=expires_at,
        )
        self.session.add(artifact)
        await self.session.flush()
        await self.session.refresh(artifact)
        return artifact

    def _artifact_path(self, *, artifact_id: str, artifact_type: str, extension: str) -> Path:
        artifact_dir = self._artifacts_dir / artifact_type
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return cast(Path, artifact_dir / f"{artifact_id}{extension}")
