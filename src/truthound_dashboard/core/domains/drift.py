"""Drift domain services and repositories."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import BaseRepository, DriftComparison

from ..datasource_factory import SourceType
from ..truthound_adapter import get_adapter
from .source_io import get_async_data_input_from_source, get_data_input_from_source
from .sources import SourceRepository


class DriftComparisonRepository(BaseRepository[DriftComparison]):
    model = DriftComparison

    async def get_for_sources(
        self,
        baseline_source_id: str | None = None,
        current_source_id: str | None = None,
        *,
        limit: int = 20,
    ) -> Sequence[DriftComparison]:
        filters = []
        if baseline_source_id:
            filters.append(DriftComparison.baseline_source_id == baseline_source_id)
        if current_source_id:
            filters.append(DriftComparison.current_source_id == current_source_id)
        return await self.list(
            limit=limit,
            filters=filters if filters else None,
            order_by=DriftComparison.created_at.desc(),
        )

    async def get_latest(
        self,
        baseline_source_id: str,
        current_source_id: str,
    ) -> DriftComparison | None:
        result = await self.session.execute(
            select(DriftComparison)
            .where(
                and_(
                    DriftComparison.baseline_source_id == baseline_source_id,
                    DriftComparison.current_source_id == current_source_id,
                )
            )
            .order_by(DriftComparison.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class DriftService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.source_repo = SourceRepository(session)
        self.drift_repo = DriftComparisonRepository(session)
        self.adapter = get_adapter()

    async def compare(
        self,
        baseline_source_id: str,
        current_source_id: str,
        *,
        columns: list[str] | None = None,
        method: str = "auto",
        threshold: float | None = None,
        sample_size: int | None = None,
        save: bool = True,
    ) -> DriftComparison:
        baseline = await self.source_repo.get_by_id(baseline_source_id)
        if baseline is None:
            raise ValueError(f"Baseline source '{baseline_source_id}' not found")
        current = await self.source_repo.get_by_id(current_source_id)
        if current is None:
            raise ValueError(f"Current source '{current_source_id}' not found")

        if SourceType.is_async_type(baseline.type):
            baseline_input = await get_async_data_input_from_source(baseline, self.session)
        else:
            baseline_input = await get_data_input_from_source(baseline, self.session)

        if SourceType.is_async_type(current.type):
            current_input = await get_async_data_input_from_source(current, self.session)
        else:
            current_input = await get_data_input_from_source(current, self.session)

        result = await self.adapter.compare(
            baseline_input,
            current_input,
            columns=columns,
            method=method,
            threshold=threshold,
            sample_size=sample_size,
        )
        config = {
            "columns": columns,
            "method": method,
            "threshold": threshold,
            "sample_size": sample_size,
        }
        if save:
            return await self.drift_repo.create(
                baseline_source_id=baseline_source_id,
                current_source_id=current_source_id,
                has_drift=result.has_drift,
                has_high_drift=result.has_high_drift,
                total_columns=result.total_columns,
                drifted_columns=len(result.drifted_columns),
                result_json=result.to_dict(),
                config=config,
            )
        return DriftComparison(
            baseline_source_id=baseline_source_id,
            current_source_id=current_source_id,
            has_drift=result.has_drift,
            has_high_drift=result.has_high_drift,
            total_columns=result.total_columns,
            drifted_columns=len(result.drifted_columns),
            result_json=result.to_dict(),
            config=config,
        )

    async def get_comparison(self, comparison_id: str) -> DriftComparison | None:
        return await self.drift_repo.get_by_id(comparison_id)

    async def list_comparisons(
        self,
        *,
        baseline_source_id: str | None = None,
        current_source_id: str | None = None,
        limit: int = 20,
    ) -> Sequence[DriftComparison]:
        return await self.drift_repo.get_for_sources(
            baseline_source_id=baseline_source_id,
            current_source_id=current_source_id,
            limit=limit,
        )


__all__ = ["DriftComparisonRepository", "DriftService"]
