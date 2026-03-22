"""Privacy domain services and repositories."""

from __future__ import annotations

import tempfile
from collections.abc import Sequence
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import BaseRepository, DataMask, PIIScan

from ..datasource_factory import SourceType
from ..truthound_adapter import MaskResult, ScanResult, get_adapter
from truthound_dashboard.time import utc_now
from .source_io import get_async_data_input_from_source, get_data_input_from_source
from .sources import SourceRepository


class PIIScanRepository(BaseRepository[PIIScan]):
    model = PIIScan

    async def get_for_source(
        self,
        source_id: str,
        *,
        limit: int = 20,
    ) -> Sequence[PIIScan]:
        return await self.list(
            limit=limit,
            filters=[PIIScan.source_id == source_id],
            order_by=PIIScan.created_at.desc(),
        )

    async def get_latest_for_source(self, source_id: str) -> PIIScan | None:
        result = await self.session.execute(
            select(PIIScan)
            .where(PIIScan.source_id == source_id)
            .order_by(PIIScan.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class PIIScanService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.source_repo = SourceRepository(session)
        self.scan_repo = PIIScanRepository(session)
        self.adapter = get_adapter()

    async def run_scan(self, source_id: str) -> PIIScan:
        source = await self.source_repo.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")

        scan = await self.scan_repo.create(
            source_id=source_id,
            status="running",
            started_at=utc_now(),
        )

        try:
            if SourceType.is_async_type(source.type):
                data_input = await get_async_data_input_from_source(source, self.session)
            else:
                data_input = await get_data_input_from_source(source, self.session)

            result = await self.adapter.scan(data_input)
            await self._update_scan_success(scan, result)
        except Exception as exc:
            scan.mark_error(str(exc))

        await self.session.flush()
        await self.session.refresh(scan)
        return scan

    async def _update_scan_success(
        self,
        scan: PIIScan,
        result: ScanResult,
    ) -> None:
        scan.status = "success" if not result.has_violations else "failed"
        scan.total_columns_scanned = result.total_columns_scanned
        scan.columns_with_pii = result.columns_with_pii
        scan.total_findings = result.total_findings
        scan.has_violations = result.has_violations
        scan.total_violations = result.total_violations
        scan.row_count = result.row_count
        scan.column_count = result.column_count
        scan.result_json = result.to_dict()
        scan.completed_at = utc_now()

        if scan.started_at:
            delta = scan.completed_at - scan.started_at
            scan.duration_ms = int(delta.total_seconds() * 1000)

    async def get_scan(self, scan_id: str) -> PIIScan | None:
        return await self.scan_repo.get_by_id(scan_id)

    async def list_for_source(
        self,
        source_id: str,
        *,
        limit: int = 20,
    ) -> Sequence[PIIScan]:
        return await self.scan_repo.get_for_source(source_id, limit=limit)

    async def get_latest_for_source(self, source_id: str) -> PIIScan | None:
        return await self.scan_repo.get_latest_for_source(source_id)


class DataMaskRepository(BaseRepository[DataMask]):
    model = DataMask

    async def get_for_source(
        self,
        source_id: str,
        *,
        limit: int = 20,
    ) -> Sequence[DataMask]:
        return await self.list(
            limit=limit,
            filters=[DataMask.source_id == source_id],
            order_by=DataMask.created_at.desc(),
        )

    async def get_latest_for_source(self, source_id: str) -> DataMask | None:
        result = await self.session.execute(
            select(DataMask)
            .where(DataMask.source_id == source_id)
            .order_by(DataMask.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class MaskService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.source_repo = SourceRepository(session)
        self.mask_repo = DataMaskRepository(session)
        self.adapter = get_adapter()

    async def run_mask(
        self,
        source_id: str,
        *,
        columns: list[str] | None = None,
        strategy: str = "redact",
    ) -> DataMask:
        if strategy not in ("redact", "hash", "fake"):
            raise ValueError(
                f"Invalid strategy: {strategy}. Use 'redact', 'hash', or 'fake'."
            )

        source = await self.source_repo.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")

        if SourceType.is_file_type(source.type):
            source_path = source.source_path or source.config.get("path", "")
            base_path = Path(source_path)
            output_dir = base_path.parent / "masked"
        else:
            output_dir = Path(tempfile.gettempdir()) / "truthound_masked"

        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"{source.name}_masked_{strategy}.csv")

        mask = await self.mask_repo.create(
            source_id=source_id,
            status="running",
            strategy=strategy,
            auto_detected=columns is None,
            started_at=utc_now(),
        )

        try:
            if SourceType.is_async_type(source.type):
                data_input = await get_async_data_input_from_source(source, self.session)
            else:
                data_input = await get_data_input_from_source(source, self.session)

            result = await self.adapter.mask(
                data_input,
                output_path,
                columns=columns,
                strategy=strategy,
            )
            await self._update_mask_success(mask, result)
        except Exception as exc:
            mask.mark_error(str(exc))

        await self.session.flush()
        await self.session.refresh(mask)
        return mask

    async def _update_mask_success(
        self,
        mask: DataMask,
        result: MaskResult,
    ) -> None:
        mask.status = "success"
        mask.output_path = result.output_path
        mask.columns_masked = result.columns_masked
        mask.row_count = result.row_count
        mask.column_count = result.column_count
        mask.result_json = result.to_dict()
        mask.completed_at = utc_now()

        if mask.started_at:
            delta = mask.completed_at - mask.started_at
            mask.duration_ms = int(delta.total_seconds() * 1000)

    async def get_mask(self, mask_id: str) -> DataMask | None:
        return await self.mask_repo.get_by_id(mask_id)

    async def list_for_source(
        self,
        source_id: str,
        *,
        limit: int = 20,
    ) -> Sequence[DataMask]:
        return await self.mask_repo.get_for_source(source_id, limit=limit)

    async def get_latest_for_source(self, source_id: str) -> DataMask | None:
        return await self.mask_repo.get_latest_for_source(source_id)


__all__ = ["DataMaskRepository", "MaskService", "PIIScanRepository", "PIIScanService"]
