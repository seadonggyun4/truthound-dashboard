"""Validation domain services and repositories."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from truthound_dashboard.db import BaseRepository, Validation
from truthound_dashboard.time import utc_now

from ..datasource_factory import SourceType
from ..truthound_adapter import CheckResult, get_adapter
from .source_io import get_async_data_input_from_source, get_data_input_from_source
from .sources import SourceRepository


class ValidationRepository(BaseRepository[Validation]):
    model = Validation

    async def get_for_source(
        self,
        source_id: str,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Validation], int]:
        filters = [Validation.source_id == source_id]
        validations = await self.list(
            offset=offset,
            limit=limit,
            filters=filters,
            order_by=Validation.created_at.desc(),
        )
        total = await self.count(filters=filters)
        return validations, total

    async def get_latest_for_source(self, source_id: str) -> Validation | None:
        result = await self.session.execute(
            select(Validation)
            .where(Validation.source_id == source_id)
            .order_by(Validation.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_with_source(self, validation_id: str) -> Validation | None:
        result = await self.session.execute(
            select(Validation)
            .options(selectinload(Validation.source))
            .where(Validation.id == validation_id)
        )
        return result.scalar_one_or_none()


class ValidationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.source_repo = SourceRepository(session)
        from .schemas import SchemaRepository

        self.schema_repo = SchemaRepository(session)
        self.validation_repo = ValidationRepository(session)
        self.adapter = get_adapter()

    async def run_validation(
        self,
        source_id: str,
        *,
        validators: list[str] | None = None,
        validator_config: dict[str, dict[str, Any]] | None = None,
        schema_path: str | None = None,
        auto_schema: bool = False,
        min_severity: str | None = None,
        parallel: bool = False,
        max_workers: int | None = None,
        pushdown: bool | None = None,
        result_format: str | None = None,
        include_unexpected_rows: bool = False,
        max_unexpected_rows: int | None = None,
        catch_exceptions: bool = True,
        max_retries: int = 3,
    ) -> Validation:
        source = await self.source_repo.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")

        validation = await self.validation_repo.create(
            source_id=source_id,
            status="running",
            started_at=utc_now(),
        )

        try:
            if SourceType.is_async_type(source.type):
                data_input = await get_async_data_input_from_source(source, self.session)
            else:
                data_input = await get_data_input_from_source(source, self.session)

            result = await self.adapter.check(
                data_input,
                validators=validators,
                validator_config=validator_config,
                schema=schema_path,
                auto_schema=auto_schema,
                min_severity=min_severity,
                parallel=parallel,
                max_workers=max_workers,
                pushdown=pushdown,
                result_format=result_format,
                include_unexpected_rows=include_unexpected_rows,
                max_unexpected_rows=max_unexpected_rows,
                catch_exceptions=catch_exceptions,
                max_retries=max_retries,
            )

            await self._update_validation_success(validation, result)
            source.last_validated_at = utc_now()
        except Exception as exc:
            validation.mark_error(str(exc))

        await self.session.flush()
        await self.session.refresh(validation)
        return validation

    async def _update_validation_success(self, validation: Validation, result: CheckResult) -> None:
        validation.status = "success" if result.passed else "failed"
        validation.passed = result.passed
        validation.has_critical = result.has_critical
        validation.has_high = result.has_high
        validation.total_issues = result.total_issues
        validation.critical_issues = result.critical_issues
        validation.high_issues = result.high_issues
        validation.medium_issues = result.medium_issues
        validation.low_issues = result.low_issues
        validation.row_count = result.row_count
        validation.column_count = result.column_count
        validation.result_json = result.to_dict()
        validation.completed_at = utc_now()
        if validation.started_at:
            delta = validation.completed_at - validation.started_at
            validation.duration_ms = int(delta.total_seconds() * 1000)

    async def get_validation(
        self, validation_id: str, *, with_source: bool = False
    ) -> Validation | None:
        if with_source:
            return await self.validation_repo.get_with_source(validation_id)
        return await self.validation_repo.get_by_id(validation_id)

    async def list_for_source(
        self,
        source_id: str,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Validation], int]:
        return await self.validation_repo.get_for_source(
            source_id,
            offset=offset,
            limit=limit,
        )


__all__ = ["ValidationRepository", "ValidationService"]
