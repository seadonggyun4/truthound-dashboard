"""Schema evolution detection service.

This module provides functionality for detecting and tracking
schema changes over time, enabling schema evolution monitoring.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import (
    BaseRepository,
    Schema,
    Source,
)
from truthound_dashboard.db.models import SchemaChange, SchemaVersion
from truthound_dashboard.schemas.schema_evolution import (
    SchemaChangeResponse,
    SchemaChangeSeverity,
    SchemaChangeType,
    SchemaEvolutionResponse,
    SchemaEvolutionSummary,
    SchemaVersionResponse,
    SchemaVersionSummary,
)


class SchemaVersionRepository(BaseRepository[SchemaVersion]):
    """Repository for SchemaVersion model operations."""

    model = SchemaVersion

    async def get_latest_for_source(self, source_id: str) -> SchemaVersion | None:
        """Get the latest schema version for a source.

        Args:
            source_id: Source ID.

        Returns:
            Latest schema version or None.
        """
        result = await self.session.execute(
            select(SchemaVersion)
            .where(SchemaVersion.source_id == source_id)
            .order_by(SchemaVersion.version_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_for_source(
        self,
        source_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[SchemaVersion]:
        """Get schema versions for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.
            offset: Number to skip.

        Returns:
            Sequence of schema versions.
        """
        return await self.list(
            offset=offset,
            limit=limit,
            filters=[SchemaVersion.source_id == source_id],
            order_by=[SchemaVersion.version_number.desc()],
        )

    async def get_next_version_number(self, source_id: str) -> int:
        """Get the next version number for a source.

        Args:
            source_id: Source ID.

        Returns:
            Next version number (1 if no previous versions).
        """
        result = await self.session.execute(
            select(func.max(SchemaVersion.version_number)).where(
                SchemaVersion.source_id == source_id
            )
        )
        max_version = result.scalar_one_or_none()
        return (max_version or 0) + 1

    async def get_by_hash(
        self, source_id: str, schema_hash: str
    ) -> SchemaVersion | None:
        """Get schema version by hash.

        Args:
            source_id: Source ID.
            schema_hash: Schema hash.

        Returns:
            Schema version or None.
        """
        result = await self.session.execute(
            select(SchemaVersion)
            .where(SchemaVersion.source_id == source_id)
            .where(SchemaVersion.schema_hash == schema_hash)
            .limit(1)
        )
        return result.scalar_one_or_none()


class SchemaChangeRepository(BaseRepository[SchemaChange]):
    """Repository for SchemaChange model operations."""

    model = SchemaChange

    async def get_for_source(
        self,
        source_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[SchemaChange]:
        """Get schema changes for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.
            offset: Number to skip.

        Returns:
            Sequence of schema changes.
        """
        return await self.list(
            offset=offset,
            limit=limit,
            filters=[SchemaChange.source_id == source_id],
            order_by=[SchemaChange.created_at.desc()],
        )

    async def get_for_version(
        self, to_version_id: str
    ) -> Sequence[SchemaChange]:
        """Get changes for a specific version transition.

        Args:
            to_version_id: Target version ID.

        Returns:
            Sequence of changes.
        """
        return await self.list(
            filters=[SchemaChange.to_version_id == to_version_id],
            order_by=[SchemaChange.created_at.desc()],
        )

    async def count_breaking_changes(self, source_id: str) -> int:
        """Count breaking changes for a source.

        Args:
            source_id: Source ID.

        Returns:
            Count of breaking changes.
        """
        result = await self.session.execute(
            select(func.count(SchemaChange.id))
            .where(SchemaChange.source_id == source_id)
            .where(SchemaChange.severity == "breaking")
        )
        return result.scalar_one() or 0


class SchemaEvolutionService:
    """Service for schema evolution detection and tracking."""

    def __init__(self, session: AsyncSession):
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.version_repo = SchemaVersionRepository(session)
        self.change_repo = SchemaChangeRepository(session)

    def _compute_schema_hash(self, schema_json: dict[str, Any]) -> str:
        """Compute deterministic hash of schema structure.

        Args:
            schema_json: Schema JSON to hash.

        Returns:
            SHA256 hash string.
        """
        # Extract and normalize columns for consistent hashing
        columns = schema_json.get("columns", {})
        normalized = {}
        for col_name, col_def in sorted(columns.items()):
            # Only hash structural properties
            normalized[col_name] = {
                "dtype": col_def.get("dtype"),
                "nullable": col_def.get("nullable"),
            }

        # Create deterministic JSON string
        json_str = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def _extract_column_snapshot(
        self, schema_json: dict[str, Any]
    ) -> dict[str, Any]:
        """Extract column definitions for snapshot.

        Args:
            schema_json: Full schema JSON.

        Returns:
            Column definitions dictionary.
        """
        columns = schema_json.get("columns", {})
        snapshot = {}
        for col_name, col_def in columns.items():
            snapshot[col_name] = {
                "dtype": col_def.get("dtype"),
                "nullable": col_def.get("nullable"),
                "unique": col_def.get("unique"),
            }
        return snapshot

    def _detect_column_changes(
        self,
        old_columns: dict[str, Any],
        new_columns: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Detect changes between two column snapshots.

        Args:
            old_columns: Previous column definitions.
            new_columns: New column definitions.

        Returns:
            List of detected changes.
        """
        changes = []
        old_names = set(old_columns.keys())
        new_names = set(new_columns.keys())

        # Added columns
        for col_name in new_names - old_names:
            col_def = new_columns[col_name]
            changes.append({
                "change_type": SchemaChangeType.COLUMN_ADDED.value,
                "column_name": col_name,
                "old_value": None,
                "new_value": col_def.get("dtype"),
                "severity": SchemaChangeSeverity.NON_BREAKING.value,
            })

        # Removed columns (breaking change)
        for col_name in old_names - new_names:
            col_def = old_columns[col_name]
            changes.append({
                "change_type": SchemaChangeType.COLUMN_REMOVED.value,
                "column_name": col_name,
                "old_value": col_def.get("dtype"),
                "new_value": None,
                "severity": SchemaChangeSeverity.BREAKING.value,
            })

        # Type changes
        for col_name in old_names & new_names:
            old_type = old_columns[col_name].get("dtype")
            new_type = new_columns[col_name].get("dtype")
            if old_type != new_type:
                # Type changes are usually breaking
                changes.append({
                    "change_type": SchemaChangeType.TYPE_CHANGED.value,
                    "column_name": col_name,
                    "old_value": old_type,
                    "new_value": new_type,
                    "severity": SchemaChangeSeverity.BREAKING.value,
                })

        return changes

    async def create_version(
        self,
        source_id: str,
        schema: Schema,
    ) -> tuple[SchemaVersion, list[SchemaChange]]:
        """Create a new schema version snapshot.

        Args:
            source_id: Source ID.
            schema: Schema record.

        Returns:
            Tuple of (new version, list of changes).
        """
        schema_json = schema.schema_json or {}
        schema_hash = self._compute_schema_hash(schema_json)

        # Check if this exact schema already exists
        existing = await self.version_repo.get_by_hash(source_id, schema_hash)
        if existing:
            return existing, []

        # Get previous version
        previous = await self.version_repo.get_latest_for_source(source_id)
        next_version_number = await self.version_repo.get_next_version_number(
            source_id
        )

        # Create column snapshot
        column_snapshot = self._extract_column_snapshot(schema_json)

        # Create new version
        new_version = await self.version_repo.create(
            source_id=source_id,
            schema_id=schema.id,
            version_number=next_version_number,
            schema_hash=schema_hash,
            column_snapshot=column_snapshot,
        )

        # Detect changes
        changes = []
        if previous:
            detected = self._detect_column_changes(
                previous.column_snapshot,
                column_snapshot,
            )
            for change_data in detected:
                change = await self.change_repo.create(
                    source_id=source_id,
                    from_version_id=previous.id,
                    to_version_id=new_version.id,
                    **change_data,
                )
                changes.append(change)

        await self.session.commit()
        return new_version, changes

    async def detect_changes(
        self,
        source: Source,
        schema: Schema,
    ) -> SchemaEvolutionResponse:
        """Detect schema changes for a source.

        Args:
            source: Source record.
            schema: Current schema.

        Returns:
            Evolution detection response.
        """
        new_version, changes = await self.create_version(source.id, schema)

        # Get previous version info
        versions = await self.version_repo.get_for_source(source.id, limit=2)
        from_version = versions[1].version_number if len(versions) > 1 else None

        # Convert changes to response format
        change_responses = [
            SchemaChangeResponse(
                id=c.id,
                source_id=c.source_id,
                from_version_id=c.from_version_id,
                to_version_id=c.to_version_id,
                change_type=SchemaChangeType(c.change_type),
                column_name=c.column_name,
                old_value=c.old_value,
                new_value=c.new_value,
                severity=SchemaChangeSeverity(c.severity),
                description=c.description,
                created_at=c.created_at,
            )
            for c in changes
        ]

        breaking_count = sum(1 for c in changes if c.is_breaking)

        return SchemaEvolutionResponse(
            source_id=source.id,
            source_name=source.name,
            from_version=from_version,
            to_version=new_version.version_number,
            has_changes=len(changes) > 0,
            total_changes=len(changes),
            breaking_changes=breaking_count,
            changes=change_responses,
            detected_at=datetime.utcnow(),
        )

    async def get_version_history(
        self,
        source_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[SchemaVersionSummary]:
        """Get schema version history for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.
            offset: Number to skip.

        Returns:
            List of version summaries.
        """
        versions = await self.version_repo.get_for_source(
            source_id, limit=limit, offset=offset
        )
        return [
            SchemaVersionSummary(
                id=v.id,
                version_number=v.version_number,
                column_count=v.column_count,
                created_at=v.created_at,
            )
            for v in versions
        ]

    async def get_version(self, version_id: str) -> SchemaVersionResponse | None:
        """Get a specific schema version.

        Args:
            version_id: Version ID.

        Returns:
            Version response or None.
        """
        version = await self.version_repo.get_by_id(version_id)
        if not version:
            return None

        return SchemaVersionResponse(
            id=version.id,
            source_id=version.source_id,
            schema_id=version.schema_id,
            version_number=version.version_number,
            column_count=version.column_count,
            columns=version.column_names,
            schema_hash=version.schema_hash,
            column_snapshot=version.column_snapshot,
            created_at=version.created_at,
            updated_at=version.updated_at,
        )

    async def get_changes(
        self,
        source_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SchemaChangeResponse]:
        """Get schema changes for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.
            offset: Number to skip.

        Returns:
            List of change responses.
        """
        changes = await self.change_repo.get_for_source(
            source_id, limit=limit, offset=offset
        )
        return [
            SchemaChangeResponse(
                id=c.id,
                source_id=c.source_id,
                from_version_id=c.from_version_id,
                to_version_id=c.to_version_id,
                change_type=SchemaChangeType(c.change_type),
                column_name=c.column_name,
                old_value=c.old_value,
                new_value=c.new_value,
                severity=SchemaChangeSeverity(c.severity),
                description=c.description,
                created_at=c.created_at,
            )
            for c in changes
        ]

    async def get_evolution_summary(
        self, source_id: str
    ) -> SchemaEvolutionSummary:
        """Get evolution summary for a source.

        Args:
            source_id: Source ID.

        Returns:
            Evolution summary.
        """
        # Get version count
        versions = await self.version_repo.get_for_source(source_id, limit=1)
        latest_version = versions[0] if versions else None

        total_versions = 0
        if latest_version:
            total_versions = latest_version.version_number

        # Get change counts
        changes = await self.change_repo.get_for_source(source_id, limit=1000)
        total_changes = len(changes)
        breaking_changes = await self.change_repo.count_breaking_changes(source_id)

        # Get last change timestamp
        last_change_at = None
        if changes:
            last_change_at = changes[0].created_at

        return SchemaEvolutionSummary(
            source_id=source_id,
            current_version=latest_version.version_number if latest_version else 0,
            total_versions=total_versions,
            total_changes=total_changes,
            breaking_changes=breaking_changes,
            last_change_at=last_change_at,
        )
