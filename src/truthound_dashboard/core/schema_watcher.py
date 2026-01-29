"""Schema Watcher Service.

This module provides schema monitoring functionality using truthound's
schema evolution module (truthound.profiler.evolution).

Architecture:
    API Endpoints
         ↓
    SchemaWatcherService
         ↓
    SchemaEvolutionAdapter (truthound_adapter.py)
         ↓
    truthound.profiler.evolution
        - SchemaEvolutionDetector
        - SchemaHistory
        - SchemaWatcher
        - ColumnRenameDetector
        - BreakingChangeAlertManager
        - ImpactAnalyzer

Features:
    - Schema change detection with breaking change identification
    - Column rename detection using multiple similarity algorithms
    - Version history with semantic/incremental/timestamp/git strategies
    - Continuous monitoring with configurable polling
    - Impact analysis for affected consumers
    - Alert management with acknowledgment and resolution
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from truthound_dashboard.db.models import (
    SchemaWatcherAlertModel,
    SchemaWatcherAlertSeverity as DBAlertSeverity,
    SchemaWatcherAlertStatus as DBAlertStatus,
    SchemaWatcherModel,
    SchemaWatcherRunModel,
    SchemaWatcherRunStatus as DBRunStatus,
    SchemaWatcherStatus as DBStatus,
    Source as SourceModel,
)
from truthound_dashboard.schemas.schema_watcher import (
    CompatibilityLevel,
    ImpactScope,
    RenameConfidence,
    SchemaChangeDetail,
    SchemaChangeSeverity,
    SchemaChangeType,
    SchemaDetectionResponse,
    SchemaDiffResponse,
    SchemaHistoryResponse,
    SchemaVersionResponse,
    SchemaVersionSummary,
    SchemaWatcherAlertResponse,
    SchemaWatcherAlertSeverity,
    SchemaWatcherAlertStatus,
    SchemaWatcherAlertSummary,
    SchemaWatcherCheckNowResponse,
    SchemaWatcherCreate,
    SchemaWatcherResponse,
    SchemaWatcherRunResponse,
    SchemaWatcherRunStatus,
    SchemaWatcherRunSummary,
    SchemaWatcherSchedulerStatus,
    SchemaWatcherStatistics,
    SchemaWatcherStatus,
    SchemaWatcherSummary,
    SchemaWatcherUpdate,
    RenameDetectionDetail,
    RenameDetectionResponse,
    VersionStrategy,
)

logger = logging.getLogger(__name__)

# Storage paths
SCHEMA_HISTORY_BASE_PATH = Path("./data/schema_history")
ALERT_STORAGE_PATH = Path("./data/schema_alerts.json")


def _generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid4())


def _map_db_status(status: DBStatus) -> SchemaWatcherStatus:
    """Map DB status enum to schema enum."""
    return SchemaWatcherStatus(status.value)


def _map_schema_status(status: SchemaWatcherStatus) -> DBStatus:
    """Map schema status enum to DB enum."""
    return DBStatus(status.value)


def _map_db_alert_status(status: DBAlertStatus) -> SchemaWatcherAlertStatus:
    """Map DB alert status enum to schema enum."""
    return SchemaWatcherAlertStatus(status.value)


def _map_db_alert_severity(severity: DBAlertSeverity) -> SchemaWatcherAlertSeverity:
    """Map DB alert severity enum to schema enum."""
    return SchemaWatcherAlertSeverity(severity.value)


def _map_db_run_status(status: DBRunStatus) -> SchemaWatcherRunStatus:
    """Map DB run status enum to schema enum."""
    return SchemaWatcherRunStatus(status.value)


class SchemaWatcherService:
    """Service for schema watcher operations.

    This service provides comprehensive schema monitoring using truthound's
    schema evolution module. It manages:
    - Watcher configuration and lifecycle
    - Schema change detection
    - Version history
    - Alerts and impact analysis
    - Background polling

    The service uses SchemaEvolutionAdapter to interact with truthound,
    maintaining loose coupling with the underlying library.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Async database session.
        """
        self._session = session
        self._adapter = None  # Lazy initialization

    @property
    def adapter(self):
        """Get schema evolution adapter (lazy initialization)."""
        if self._adapter is None:
            from truthound_dashboard.core.truthound_adapter import (
                get_schema_evolution_adapter,
            )
            self._adapter = get_schema_evolution_adapter()
        return self._adapter

    # =========================================================================
    # Watcher CRUD
    # =========================================================================

    async def create_watcher(
        self,
        data: SchemaWatcherCreate,
    ) -> SchemaWatcherResponse:
        """Create a new schema watcher.

        Args:
            data: Watcher creation data.

        Returns:
            Created watcher response.

        Raises:
            ValueError: If source not found.
        """
        # Verify source exists
        source = await self._session.get(SourceModel, data.source_id)
        if not source:
            raise ValueError(f"Source '{data.source_id}' not found")

        now = datetime.utcnow()
        next_check = now + timedelta(seconds=data.poll_interval_seconds)

        watcher = SchemaWatcherModel(
            id=_generate_id(),
            name=data.name,
            source_id=data.source_id,
            status=DBStatus.ACTIVE,
            poll_interval_seconds=data.poll_interval_seconds,
            only_breaking=data.only_breaking,
            enable_rename_detection=data.enable_rename_detection,
            rename_similarity_threshold=data.rename_similarity_threshold,
            version_strategy=data.version_strategy.value,
            notify_on_change=data.notify_on_change,
            track_history=data.track_history,
            next_check_at=next_check,
            watcher_config=data.config,
            created_at=now,
            updated_at=now,
        )

        self._session.add(watcher)
        await self._session.commit()
        await self._session.refresh(watcher)

        # Initialize schema history for this watcher
        if data.track_history:
            history_path = SCHEMA_HISTORY_BASE_PATH / watcher.id
            history_path.mkdir(parents=True, exist_ok=True)
            await self.adapter.create_history(
                history_id=watcher.id,
                storage_path=str(history_path),
                version_strategy=data.version_strategy.value,
            )

        return self._to_watcher_response(watcher, source)

    async def get_watcher(self, watcher_id: str) -> SchemaWatcherResponse | None:
        """Get a watcher by ID.

        Args:
            watcher_id: Watcher ID.

        Returns:
            Watcher response or None if not found.
        """
        stmt = (
            select(SchemaWatcherModel)
            .options(selectinload(SchemaWatcherModel.source))
            .where(SchemaWatcherModel.id == watcher_id)
        )
        result = await self._session.execute(stmt)
        watcher = result.scalar_one_or_none()

        if not watcher:
            return None

        return self._to_watcher_response(watcher, watcher.source)

    async def list_watchers(
        self,
        *,
        status: SchemaWatcherStatus | None = None,
        source_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SchemaWatcherSummary], int]:
        """List watchers with optional filters.

        Args:
            status: Filter by status.
            source_id: Filter by source.
            limit: Maximum results.
            offset: Skip first N results.

        Returns:
            Tuple of (watchers, total_count).
        """
        stmt = select(SchemaWatcherModel).options(
            selectinload(SchemaWatcherModel.source)
        )

        if status:
            stmt = stmt.where(
                SchemaWatcherModel.status == _map_schema_status(status)
            )
        if source_id:
            stmt = stmt.where(SchemaWatcherModel.source_id == source_id)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination
        stmt = (
            stmt.order_by(SchemaWatcherModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self._session.execute(stmt)
        watchers = result.scalars().all()

        summaries = [self._to_watcher_summary(w, w.source) for w in watchers]
        return summaries, total

    async def update_watcher(
        self,
        watcher_id: str,
        data: SchemaWatcherUpdate,
    ) -> SchemaWatcherResponse | None:
        """Update a watcher.

        Args:
            watcher_id: Watcher ID.
            data: Update data.

        Returns:
            Updated watcher response or None if not found.
        """
        stmt = (
            select(SchemaWatcherModel)
            .options(selectinload(SchemaWatcherModel.source))
            .where(SchemaWatcherModel.id == watcher_id)
        )
        result = await self._session.execute(stmt)
        watcher = result.scalar_one_or_none()

        if not watcher:
            return None

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "version_strategy" and value:
                setattr(watcher, key, value.value)
            elif hasattr(watcher, key):
                setattr(watcher, key, value)

        watcher.updated_at = datetime.utcnow()

        # Recalculate next_check_at if poll_interval changed
        if data.poll_interval_seconds and watcher.status == DBStatus.ACTIVE:
            watcher.next_check_at = datetime.utcnow() + timedelta(
                seconds=data.poll_interval_seconds
            )

        await self._session.commit()
        await self._session.refresh(watcher)

        return self._to_watcher_response(watcher, watcher.source)

    async def delete_watcher(self, watcher_id: str) -> bool:
        """Delete a watcher and all related data.

        Args:
            watcher_id: Watcher ID.

        Returns:
            True if deleted, False if not found.
        """
        watcher = await self._session.get(SchemaWatcherModel, watcher_id)
        if not watcher:
            return False

        # Delete related alerts and runs (cascade should handle this)
        await self._session.delete(watcher)
        await self._session.commit()

        # Clean up adapter resources
        try:
            await self.adapter.delete_watcher(watcher_id)
        except ValueError:
            pass  # Watcher not in adapter (not started)

        return True

    async def set_watcher_status(
        self,
        watcher_id: str,
        status: SchemaWatcherStatus,
    ) -> SchemaWatcherResponse | None:
        """Change watcher status.

        Args:
            watcher_id: Watcher ID.
            status: New status.

        Returns:
            Updated watcher response or None if not found.
        """
        stmt = (
            select(SchemaWatcherModel)
            .options(selectinload(SchemaWatcherModel.source))
            .where(SchemaWatcherModel.id == watcher_id)
        )
        result = await self._session.execute(stmt)
        watcher = result.scalar_one_or_none()

        if not watcher:
            return None

        old_status = watcher.status
        watcher.status = _map_schema_status(status)
        watcher.updated_at = datetime.utcnow()

        # Update next_check_at based on status change
        if status == SchemaWatcherStatus.ACTIVE:
            watcher.next_check_at = datetime.utcnow() + timedelta(
                seconds=watcher.poll_interval_seconds
            )
            watcher.error_count = 0
        elif status in (SchemaWatcherStatus.PAUSED, SchemaWatcherStatus.STOPPED):
            watcher.next_check_at = None

        await self._session.commit()
        await self._session.refresh(watcher)

        # Update adapter state
        try:
            if status == SchemaWatcherStatus.ACTIVE and old_status != DBStatus.ACTIVE:
                await self.adapter.resume_watcher(watcher_id)
            elif status == SchemaWatcherStatus.PAUSED:
                await self.adapter.pause_watcher(watcher_id)
            elif status == SchemaWatcherStatus.STOPPED:
                await self.adapter.stop_watcher(watcher_id)
        except ValueError:
            pass  # Watcher not in adapter

        return self._to_watcher_response(watcher, watcher.source)

    # =========================================================================
    # Schema Detection
    # =========================================================================

    async def detect_changes(
        self,
        current_schema: dict[str, Any],
        baseline_schema: dict[str, Any],
        *,
        detect_renames: bool = True,
        rename_similarity_threshold: float = 0.8,
    ) -> SchemaDetectionResponse:
        """Detect schema changes between two schemas.

        Uses truthound's SchemaEvolutionDetector for comprehensive change
        detection including additions, removals, type changes, and renames.

        Args:
            current_schema: Current schema {column: type}.
            baseline_schema: Baseline schema {column: type}.
            detect_renames: Enable rename detection.
            rename_similarity_threshold: Similarity threshold for renames.

        Returns:
            SchemaDetectionResponse with all detected changes.
        """
        result = await self.adapter.detect_changes(
            current_schema,
            baseline_schema,
            detect_renames=detect_renames,
            rename_similarity_threshold=rename_similarity_threshold,
        )

        changes = [
            SchemaChangeDetail(
                change_type=SchemaChangeType(c.change_type),
                column_name=c.column_name,
                old_value=c.old_value,
                new_value=c.new_value,
                severity=SchemaChangeSeverity(c.severity),
                breaking=c.breaking,
                description=c.description,
                migration_hint=c.migration_hint,
            )
            for c in result.changes
        ]

        return SchemaDetectionResponse(
            total_changes=result.total_changes,
            breaking_changes=result.breaking_changes,
            compatibility_level=CompatibilityLevel(result.compatibility_level),
            changes=changes,
        )

    async def detect_renames(
        self,
        added_columns: dict[str, str],
        removed_columns: dict[str, str],
        *,
        similarity_threshold: float = 0.8,
        require_type_match: bool = True,
        allow_compatible_types: bool = True,
        algorithm: str = "composite",
    ) -> RenameDetectionResponse:
        """Detect column renames.

        Uses truthound's ColumnRenameDetector with configurable similarity
        algorithms.

        Args:
            added_columns: Added columns {name: type}.
            removed_columns: Removed columns {name: type}.
            similarity_threshold: Similarity threshold (0.5-1.0).
            require_type_match: Require matching types.
            allow_compatible_types: Allow compatible types.
            algorithm: Similarity algorithm.

        Returns:
            RenameDetectionResponse with detected renames.
        """
        result = await self.adapter.detect_renames(
            added_columns,
            removed_columns,
            similarity_threshold=similarity_threshold,
            require_type_match=require_type_match,
            allow_compatible_types=allow_compatible_types,
            algorithm=algorithm,
        )

        confirmed = [
            RenameDetectionDetail(
                old_name=r.old_name,
                new_name=r.new_name,
                similarity=r.similarity,
                confidence=RenameConfidence(r.confidence),
                reasons=r.reasons,
            )
            for r in result.confirmed_renames
        ]

        possible = [
            RenameDetectionDetail(
                old_name=r.old_name,
                new_name=r.new_name,
                similarity=r.similarity,
                confidence=RenameConfidence(r.confidence),
                reasons=r.reasons,
            )
            for r in result.possible_renames
        ]

        return RenameDetectionResponse(
            confirmed_renames=confirmed,
            possible_renames=possible,
            unmatched_added=result.unmatched_added,
            unmatched_removed=result.unmatched_removed,
        )

    # =========================================================================
    # Version History
    # =========================================================================

    async def save_schema_version(
        self,
        watcher_id: str,
        schema: dict[str, Any],
        *,
        version: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SchemaVersionResponse:
        """Save a schema version to history.

        Args:
            watcher_id: Watcher ID (used as history ID).
            schema: Schema dictionary.
            version: Optional explicit version.
            metadata: Optional metadata.

        Returns:
            SchemaVersionResponse with version info.
        """
        result = await self.adapter.save_schema_version(
            history_id=watcher_id,
            schema=schema,
            version=version,
            metadata=metadata,
        )

        changes = None
        if result.changes_from_parent:
            changes = [
                SchemaChangeDetail(
                    change_type=SchemaChangeType(c.change_type),
                    column_name=c.column_name,
                    old_value=c.old_value,
                    new_value=c.new_value,
                    severity=SchemaChangeSeverity(c.severity),
                    breaking=c.breaking,
                    description=c.description,
                    migration_hint=c.migration_hint,
                )
                for c in result.changes_from_parent
            ]

        return SchemaVersionResponse(
            id=result.id,
            version=result.version,
            schema=result.schema,
            metadata=result.metadata,
            created_at=datetime.fromisoformat(result.created_at) if result.created_at else None,
            has_breaking_changes=result.has_breaking_changes,
            changes_from_parent=changes,
        )

    async def get_schema_version(
        self,
        watcher_id: str,
        version: str,
    ) -> SchemaVersionResponse | None:
        """Get a specific schema version.

        Args:
            watcher_id: Watcher ID.
            version: Version string or ID.

        Returns:
            SchemaVersionResponse or None.
        """
        result = await self.adapter.get_schema_version(watcher_id, version)
        if not result:
            return None

        return SchemaVersionResponse(
            id=result.id,
            version=result.version,
            schema=result.schema,
            metadata=result.metadata,
            created_at=datetime.fromisoformat(result.created_at) if result.created_at else None,
            has_breaking_changes=result.has_breaking_changes,
        )

    async def list_schema_versions(
        self,
        watcher_id: str,
        *,
        limit: int = 50,
    ) -> list[SchemaVersionSummary]:
        """List schema versions.

        Args:
            watcher_id: Watcher ID.
            limit: Maximum versions.

        Returns:
            List of SchemaVersionSummary.
        """
        versions = await self.adapter.list_schema_versions(
            history_id=watcher_id,
            limit=limit,
        )

        return [
            SchemaVersionSummary(
                id=v.id,
                version=v.version,
                column_count=len(v.schema) if v.schema else 0,
                created_at=datetime.fromisoformat(v.created_at) if v.created_at else None,
                has_breaking_changes=v.has_breaking_changes,
            )
            for v in versions
        ]

    async def diff_versions(
        self,
        watcher_id: str,
        from_version: str,
        to_version: str | None = None,
    ) -> SchemaDiffResponse:
        """Get diff between schema versions.

        Args:
            watcher_id: Watcher ID.
            from_version: Source version.
            to_version: Target version (None = latest).

        Returns:
            SchemaDiffResponse with changes.
        """
        result = await self.adapter.diff_versions(
            history_id=watcher_id,
            from_version=from_version,
            to_version=to_version,
        )

        changes = [
            SchemaChangeDetail(
                change_type=SchemaChangeType(c.change_type),
                column_name=c.column_name,
                old_value=c.old_value,
                new_value=c.new_value,
                severity=SchemaChangeSeverity(c.severity),
                breaking=c.breaking,
                description=c.description,
                migration_hint=c.migration_hint,
            )
            for c in result.changes
        ]

        return SchemaDiffResponse(
            from_version=result.from_version,
            to_version=result.to_version,
            changes=changes,
            text_diff=result.text_diff,
        )

    async def rollback_version(
        self,
        watcher_id: str,
        to_version: str,
        *,
        reason: str | None = None,
    ) -> SchemaVersionResponse:
        """Rollback to a previous version.

        Args:
            watcher_id: Watcher ID.
            to_version: Version to rollback to.
            reason: Reason for rollback.

        Returns:
            New SchemaVersionResponse after rollback.
        """
        result = await self.adapter.rollback_version(
            history_id=watcher_id,
            to_version=to_version,
            reason=reason,
        )

        return SchemaVersionResponse(
            id=result.id,
            version=result.version,
            schema=result.schema,
            metadata=result.metadata,
            created_at=datetime.fromisoformat(result.created_at) if result.created_at else None,
            has_breaking_changes=result.has_breaking_changes,
        )

    # =========================================================================
    # Check Now (Immediate Execution)
    # =========================================================================

    async def check_now(
        self,
        watcher_id: str,
    ) -> SchemaWatcherCheckNowResponse:
        """Execute immediate check for a watcher.

        This performs a full schema check:
        1. Get current schema from source
        2. Compare with previous version
        3. Save new version if changes detected
        4. Create alert if breaking changes
        5. Update watcher state

        Args:
            watcher_id: Watcher ID.

        Returns:
            SchemaWatcherCheckNowResponse with results.

        Raises:
            ValueError: If watcher not found.
        """
        from truthound_dashboard.core.truthound_adapter import get_adapter

        # Get watcher
        stmt = (
            select(SchemaWatcherModel)
            .options(selectinload(SchemaWatcherModel.source))
            .where(SchemaWatcherModel.id == watcher_id)
        )
        result = await self._session.execute(stmt)
        watcher = result.scalar_one_or_none()

        if not watcher:
            raise ValueError(f"Watcher '{watcher_id}' not found")

        source = watcher.source
        if not source:
            raise ValueError(f"Source for watcher '{watcher_id}' not found")

        # Create run record
        run = SchemaWatcherRunModel(
            id=_generate_id(),
            watcher_id=watcher_id,
            source_id=source.id,
            started_at=datetime.utcnow(),
            status=DBRunStatus.RUNNING,
        )
        self._session.add(run)
        await self._session.flush()

        try:
            # Learn current schema from source
            adapter = get_adapter()
            learn_result = await adapter.learn(
                source.path,
                infer_constraints=True,
                categorical_threshold=watcher.watcher_config.get(
                    "categorical_threshold", 20
                ) if watcher.watcher_config else 20,
            )
            current_schema = learn_result.schema.get("columns", {})

            # Get previous version
            previous_version = await self.adapter.get_latest_version(watcher_id)

            changes_detected = 0
            breaking_detected = 0
            alert_id = None
            version_id = None

            if previous_version:
                # Detect changes
                detection = await self.detect_changes(
                    current_schema,
                    previous_version.schema,
                    detect_renames=watcher.enable_rename_detection,
                    rename_similarity_threshold=watcher.rename_similarity_threshold,
                )

                changes_detected = detection.total_changes
                breaking_detected = detection.breaking_changes

                # Save new version if changes
                if changes_detected > 0:
                    new_version = await self.save_schema_version(
                        watcher_id,
                        current_schema,
                        metadata={"source_id": source.id, "run_id": run.id},
                    )
                    version_id = new_version.id

                    # Create alert if needed
                    should_alert = (
                        not watcher.only_breaking or breaking_detected > 0
                    )
                    if should_alert:
                        alert = await self._create_alert(
                            watcher=watcher,
                            source=source,
                            from_version_id=previous_version.id,
                            to_version_id=new_version.id,
                            detection=detection,
                        )
                        alert_id = alert.id

                    watcher.last_change_at = datetime.utcnow()
                    watcher.change_count += 1
            else:
                # First version
                new_version = await self.save_schema_version(
                    watcher_id,
                    current_schema,
                    metadata={"source_id": source.id, "run_id": run.id, "initial": True},
                )
                version_id = new_version.id

            # Update run
            run.status = DBRunStatus.COMPLETED
            run.completed_at = datetime.utcnow()
            run.changes_detected = changes_detected
            run.breaking_detected = breaking_detected
            run.version_created_id = version_id
            run.alert_created_id = alert_id
            run.duration_ms = (
                run.completed_at - run.started_at
            ).total_seconds() * 1000

            # Update watcher
            watcher.last_check_at = datetime.utcnow()
            watcher.check_count += 1
            watcher.next_check_at = datetime.utcnow() + timedelta(
                seconds=watcher.poll_interval_seconds
            )
            watcher.error_count = 0
            watcher.last_error = None
            watcher.updated_at = datetime.utcnow()

            await self._session.commit()

            return SchemaWatcherCheckNowResponse(
                watcher_id=watcher_id,
                run_id=run.id,
                status=SchemaWatcherRunStatus.COMPLETED,
                changes_detected=changes_detected,
                breaking_detected=breaking_detected,
                alert_created_id=alert_id,
                version_created_id=version_id,
                duration_ms=run.duration_ms,
                message=f"Check completed: {changes_detected} changes, {breaking_detected} breaking",
            )

        except Exception as e:
            # Update run as failed
            run.status = DBRunStatus.FAILED
            run.completed_at = datetime.utcnow()
            run.error_message = str(e)
            run.duration_ms = (
                run.completed_at - run.started_at
            ).total_seconds() * 1000

            # Update watcher error state
            watcher.error_count += 1
            watcher.last_error = str(e)
            watcher.updated_at = datetime.utcnow()

            # Set to error status after 3 consecutive failures
            if watcher.error_count >= 3:
                watcher.status = DBStatus.ERROR

            await self._session.commit()

            return SchemaWatcherCheckNowResponse(
                watcher_id=watcher_id,
                run_id=run.id,
                status=SchemaWatcherRunStatus.FAILED,
                changes_detected=0,
                breaking_detected=0,
                duration_ms=run.duration_ms,
                message=f"Check failed: {str(e)}",
            )

    async def _create_alert(
        self,
        watcher: SchemaWatcherModel,
        source: SourceModel,
        from_version_id: str | None,
        to_version_id: str,
        detection: SchemaDetectionResponse,
    ) -> SchemaWatcherAlertModel:
        """Create an alert for detected changes.

        Args:
            watcher: Watcher model.
            source: Source model.
            from_version_id: Previous version ID.
            to_version_id: New version ID.
            detection: Detection result.

        Returns:
            Created alert model.
        """
        # Determine severity
        if detection.breaking_changes >= 3:
            severity = DBAlertSeverity.CRITICAL
        elif detection.breaking_changes >= 1:
            severity = DBAlertSeverity.HIGH
        elif detection.total_changes >= 5:
            severity = DBAlertSeverity.MEDIUM
        else:
            severity = DBAlertSeverity.LOW

        # Generate title
        if detection.breaking_changes > 0:
            title = f"🚨 {detection.breaking_changes} breaking changes in {source.name}"
        else:
            title = f"Schema changed: {detection.total_changes} changes in {source.name}"

        # Generate recommendations
        recommendations = []
        for change in detection.changes[:5]:
            if change.breaking:
                recommendations.append(f"Review: {change.description}")
            if change.migration_hint:
                recommendations.append(f"Hint: {change.migration_hint}")

        # Serialize changes
        changes_summary = {
            "total_changes": detection.total_changes,
            "breaking_changes": detection.breaking_changes,
            "compatibility_level": detection.compatibility_level.value,
            "changes": [
                {
                    "change_type": c.change_type.value,
                    "column_name": c.column_name,
                    "old_value": c.old_value,
                    "new_value": c.new_value,
                    "severity": c.severity.value,
                    "breaking": c.breaking,
                    "description": c.description,
                }
                for c in detection.changes
            ],
        }

        alert = SchemaWatcherAlertModel(
            id=_generate_id(),
            watcher_id=watcher.id,
            source_id=source.id,
            from_version_id=from_version_id,
            to_version_id=to_version_id,
            title=title,
            severity=severity,
            status=DBAlertStatus.OPEN,
            total_changes=detection.total_changes,
            breaking_changes=detection.breaking_changes,
            changes_summary=changes_summary,
            impact_scope="local",  # Can be enhanced with ImpactAnalyzer
            recommendations=recommendations,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self._session.add(alert)
        await self._session.flush()

        return alert

    # =========================================================================
    # Alerts
    # =========================================================================

    async def get_alert(self, alert_id: str) -> SchemaWatcherAlertResponse | None:
        """Get an alert by ID.

        Args:
            alert_id: Alert ID.

        Returns:
            Alert response or None.
        """
        alert = await self._session.get(SchemaWatcherAlertModel, alert_id)
        if not alert:
            return None

        # Load related data
        source = await self._session.get(SourceModel, alert.source_id)
        watcher = await self._session.get(SchemaWatcherModel, alert.watcher_id)

        return self._to_alert_response(alert, source, watcher)

    async def list_alerts(
        self,
        *,
        watcher_id: str | None = None,
        status: SchemaWatcherAlertStatus | None = None,
        severity: SchemaWatcherAlertSeverity | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SchemaWatcherAlertSummary], int]:
        """List alerts with filters.

        Args:
            watcher_id: Filter by watcher.
            status: Filter by status.
            severity: Filter by severity.
            limit: Maximum results.
            offset: Skip first N results.

        Returns:
            Tuple of (alerts, total_count).
        """
        stmt = select(SchemaWatcherAlertModel)

        if watcher_id:
            stmt = stmt.where(SchemaWatcherAlertModel.watcher_id == watcher_id)
        if status:
            stmt = stmt.where(
                SchemaWatcherAlertModel.status == DBAlertStatus(status.value)
            )
        if severity:
            stmt = stmt.where(
                SchemaWatcherAlertModel.severity == DBAlertSeverity(severity.value)
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination
        stmt = (
            stmt.order_by(SchemaWatcherAlertModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self._session.execute(stmt)
        alerts = result.scalars().all()

        # Load source names
        summaries = []
        for alert in alerts:
            source = await self._session.get(SourceModel, alert.source_id)
            summaries.append(self._to_alert_summary(alert, source))

        return summaries, total

    async def acknowledge_alert(
        self,
        alert_id: str,
        *,
        acknowledged_by: str | None = None,
    ) -> SchemaWatcherAlertResponse | None:
        """Acknowledge an alert.

        Args:
            alert_id: Alert ID.
            acknowledged_by: Who acknowledged.

        Returns:
            Updated alert or None.
        """
        alert = await self._session.get(SchemaWatcherAlertModel, alert_id)
        if not alert:
            return None

        alert.status = DBAlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = acknowledged_by
        alert.updated_at = datetime.utcnow()

        await self._session.commit()
        await self._session.refresh(alert)

        source = await self._session.get(SourceModel, alert.source_id)
        watcher = await self._session.get(SchemaWatcherModel, alert.watcher_id)

        return self._to_alert_response(alert, source, watcher)

    async def resolve_alert(
        self,
        alert_id: str,
        *,
        resolved_by: str | None = None,
        resolution_notes: str | None = None,
    ) -> SchemaWatcherAlertResponse | None:
        """Resolve an alert.

        Args:
            alert_id: Alert ID.
            resolved_by: Who resolved.
            resolution_notes: Notes about resolution.

        Returns:
            Updated alert or None.
        """
        alert = await self._session.get(SchemaWatcherAlertModel, alert_id)
        if not alert:
            return None

        alert.status = DBAlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = resolved_by
        alert.resolution_notes = resolution_notes
        alert.updated_at = datetime.utcnow()

        await self._session.commit()
        await self._session.refresh(alert)

        source = await self._session.get(SourceModel, alert.source_id)
        watcher = await self._session.get(SchemaWatcherModel, alert.watcher_id)

        return self._to_alert_response(alert, source, watcher)

    # =========================================================================
    # Runs
    # =========================================================================

    async def get_run(self, run_id: str) -> SchemaWatcherRunResponse | None:
        """Get a run by ID.

        Args:
            run_id: Run ID.

        Returns:
            Run response or None.
        """
        run = await self._session.get(SchemaWatcherRunModel, run_id)
        if not run:
            return None

        source = await self._session.get(SourceModel, run.source_id)
        watcher = await self._session.get(SchemaWatcherModel, run.watcher_id)

        return self._to_run_response(run, source, watcher)

    async def list_runs(
        self,
        *,
        watcher_id: str | None = None,
        status: SchemaWatcherRunStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SchemaWatcherRunSummary], int]:
        """List runs with filters.

        Args:
            watcher_id: Filter by watcher.
            status: Filter by status.
            limit: Maximum results.
            offset: Skip first N results.

        Returns:
            Tuple of (runs, total_count).
        """
        stmt = select(SchemaWatcherRunModel)

        if watcher_id:
            stmt = stmt.where(SchemaWatcherRunModel.watcher_id == watcher_id)
        if status:
            stmt = stmt.where(
                SchemaWatcherRunModel.status == DBRunStatus(status.value)
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination
        stmt = (
            stmt.order_by(SchemaWatcherRunModel.started_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self._session.execute(stmt)
        runs = result.scalars().all()

        summaries = [self._to_run_summary(r) for r in runs]
        return summaries, total

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_statistics(self) -> SchemaWatcherStatistics:
        """Get overall statistics.

        Returns:
            SchemaWatcherStatistics with aggregate metrics.
        """
        # Watcher counts
        watcher_counts = {}
        for status in DBStatus:
            stmt = select(func.count()).where(
                SchemaWatcherModel.status == status
            )
            result = await self._session.execute(stmt)
            watcher_counts[status.value] = result.scalar() or 0

        # Alert counts
        alert_counts = {}
        for status in DBAlertStatus:
            stmt = select(func.count()).where(
                SchemaWatcherAlertModel.status == status
            )
            result = await self._session.execute(stmt)
            alert_counts[status.value] = result.scalar() or 0

        # Run counts
        run_counts = {}
        for status in DBRunStatus:
            stmt = select(func.count()).where(
                SchemaWatcherRunModel.status == status
            )
            result = await self._session.execute(stmt)
            run_counts[status.value] = result.scalar() or 0

        # Total changes
        stmt = select(func.sum(SchemaWatcherRunModel.changes_detected))
        result = await self._session.execute(stmt)
        total_changes = result.scalar() or 0

        stmt = select(func.sum(SchemaWatcherRunModel.breaking_detected))
        result = await self._session.execute(stmt)
        total_breaking = result.scalar() or 0

        # Calculate detection rate
        total_checks = sum(watcher_counts.values())
        total_with_changes = run_counts.get("completed", 0)
        detection_rate = (
            total_with_changes / total_checks if total_checks > 0 else 0.0
        )

        return SchemaWatcherStatistics(
            total_watchers=sum(watcher_counts.values()),
            active_watchers=watcher_counts.get("active", 0),
            paused_watchers=watcher_counts.get("paused", 0),
            error_watchers=watcher_counts.get("error", 0),
            total_alerts=sum(alert_counts.values()),
            open_alerts=alert_counts.get("open", 0),
            acknowledged_alerts=alert_counts.get("acknowledged", 0),
            resolved_alerts=alert_counts.get("resolved", 0),
            total_runs=sum(run_counts.values()),
            successful_runs=run_counts.get("completed", 0),
            failed_runs=run_counts.get("failed", 0),
            total_changes_detected=total_changes,
            total_breaking_changes=total_breaking,
            avg_detection_rate=detection_rate,
        )

    async def get_scheduler_status(self) -> SchemaWatcherSchedulerStatus:
        """Get scheduler status.

        Returns:
            SchemaWatcherSchedulerStatus.
        """
        # Count active watchers
        stmt = select(func.count()).where(
            SchemaWatcherModel.status == DBStatus.ACTIVE
        )
        result = await self._session.execute(stmt)
        active_count = result.scalar() or 0

        # Get next scheduled check
        stmt = (
            select(SchemaWatcherModel.next_check_at)
            .where(SchemaWatcherModel.status == DBStatus.ACTIVE)
            .where(SchemaWatcherModel.next_check_at.isnot(None))
            .order_by(SchemaWatcherModel.next_check_at.asc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        next_check = result.scalar_one_or_none()

        # Count pending checks (next_check_at <= now)
        stmt = select(func.count()).where(
            SchemaWatcherModel.status == DBStatus.ACTIVE,
            SchemaWatcherModel.next_check_at <= datetime.utcnow(),
        )
        result = await self._session.execute(stmt)
        pending = result.scalar() or 0

        return SchemaWatcherSchedulerStatus(
            is_running=active_count > 0,
            active_watchers=active_count,
            next_check_at=next_check,
            pending_checks=pending,
        )

    # =========================================================================
    # Response Converters
    # =========================================================================

    def _to_watcher_response(
        self,
        watcher: SchemaWatcherModel,
        source: SourceModel | None,
    ) -> SchemaWatcherResponse:
        """Convert watcher model to response."""
        return SchemaWatcherResponse(
            id=watcher.id,
            name=watcher.name,
            source_id=watcher.source_id,
            status=_map_db_status(watcher.status),
            poll_interval_seconds=watcher.poll_interval_seconds,
            only_breaking=watcher.only_breaking,
            enable_rename_detection=watcher.enable_rename_detection,
            rename_similarity_threshold=watcher.rename_similarity_threshold,
            version_strategy=VersionStrategy(watcher.version_strategy),
            notify_on_change=watcher.notify_on_change,
            track_history=watcher.track_history,
            last_check_at=watcher.last_check_at,
            last_change_at=watcher.last_change_at,
            next_check_at=watcher.next_check_at,
            check_count=watcher.check_count,
            change_count=watcher.change_count,
            error_count=watcher.error_count,
            last_error=watcher.last_error,
            config=watcher.watcher_config,
            is_active=watcher.is_active,
            is_healthy=watcher.is_healthy,
            detection_rate=watcher.detection_rate,
            source_name=source.name if source else None,
            created_at=watcher.created_at,
            updated_at=watcher.updated_at,
        )

    def _to_watcher_summary(
        self,
        watcher: SchemaWatcherModel,
        source: SourceModel | None,
    ) -> SchemaWatcherSummary:
        """Convert watcher model to summary."""
        return SchemaWatcherSummary(
            id=watcher.id,
            name=watcher.name,
            source_id=watcher.source_id,
            source_name=source.name if source else None,
            status=_map_db_status(watcher.status),
            poll_interval_seconds=watcher.poll_interval_seconds,
            check_count=watcher.check_count,
            change_count=watcher.change_count,
            last_check_at=watcher.last_check_at,
            next_check_at=watcher.next_check_at,
            created_at=watcher.created_at,
        )

    def _to_alert_response(
        self,
        alert: SchemaWatcherAlertModel,
        source: SourceModel | None,
        watcher: SchemaWatcherModel | None,
    ) -> SchemaWatcherAlertResponse:
        """Convert alert model to response."""
        # Calculate time metrics
        time_to_acknowledge = None
        time_to_resolve = None
        if alert.acknowledged_at and alert.created_at:
            time_to_acknowledge = (
                alert.acknowledged_at - alert.created_at
            ).total_seconds()
        if alert.resolved_at and alert.created_at:
            time_to_resolve = (
                alert.resolved_at - alert.created_at
            ).total_seconds()

        return SchemaWatcherAlertResponse(
            id=alert.id,
            watcher_id=alert.watcher_id,
            source_id=alert.source_id,
            from_version_id=alert.from_version_id,
            to_version_id=alert.to_version_id,
            title=alert.title,
            severity=_map_db_alert_severity(alert.severity),
            status=_map_db_alert_status(alert.status),
            total_changes=alert.total_changes,
            breaking_changes=alert.breaking_changes,
            changes_summary=alert.changes_summary,
            impact_scope=ImpactScope(alert.impact_scope) if alert.impact_scope else None,
            affected_consumers=alert.affected_consumers,
            recommendations=alert.recommendations,
            acknowledged_at=alert.acknowledged_at,
            acknowledged_by=alert.acknowledged_by,
            resolved_at=alert.resolved_at,
            resolved_by=alert.resolved_by,
            resolution_notes=alert.resolution_notes,
            is_open=alert.is_open,
            has_breaking_changes=alert.has_breaking_changes,
            time_to_acknowledge=time_to_acknowledge,
            time_to_resolve=time_to_resolve,
            source_name=source.name if source else None,
            watcher_name=watcher.name if watcher else None,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
        )

    def _to_alert_summary(
        self,
        alert: SchemaWatcherAlertModel,
        source: SourceModel | None,
    ) -> SchemaWatcherAlertSummary:
        """Convert alert model to summary."""
        return SchemaWatcherAlertSummary(
            id=alert.id,
            watcher_id=alert.watcher_id,
            source_id=alert.source_id,
            title=alert.title,
            severity=_map_db_alert_severity(alert.severity),
            status=_map_db_alert_status(alert.status),
            total_changes=alert.total_changes,
            breaking_changes=alert.breaking_changes,
            created_at=alert.created_at,
            source_name=source.name if source else None,
        )

    def _to_run_response(
        self,
        run: SchemaWatcherRunModel,
        source: SourceModel | None,
        watcher: SchemaWatcherModel | None,
    ) -> SchemaWatcherRunResponse:
        """Convert run model to response."""
        return SchemaWatcherRunResponse(
            id=run.id,
            watcher_id=run.watcher_id,
            source_id=run.source_id,
            started_at=run.started_at,
            completed_at=run.completed_at,
            status=_map_db_run_status(run.status),
            changes_detected=run.changes_detected,
            breaking_detected=run.breaking_detected,
            version_created_id=run.version_created_id,
            alert_created_id=run.alert_created_id,
            duration_ms=run.duration_ms,
            error_message=run.error_message,
            metadata=run.run_metadata,
            is_successful=run.is_successful,
            has_changes=run.has_changes,
            source_name=source.name if source else None,
            watcher_name=watcher.name if watcher else None,
        )

    def _to_run_summary(
        self,
        run: SchemaWatcherRunModel,
    ) -> SchemaWatcherRunSummary:
        """Convert run model to summary."""
        return SchemaWatcherRunSummary(
            id=run.id,
            watcher_id=run.watcher_id,
            source_id=run.source_id,
            started_at=run.started_at,
            status=_map_db_run_status(run.status),
            changes_detected=run.changes_detected,
            breaking_detected=run.breaking_detected,
            duration_ms=run.duration_ms,
        )


# =============================================================================
# Background Processing
# =============================================================================


async def process_due_watchers(session: AsyncSession) -> int:
    """Process all watchers due for checking.

    This function is called by the scheduler to run periodic checks.

    Args:
        session: Database session.

    Returns:
        Number of watchers processed.
    """
    service = SchemaWatcherService(session)

    # Get due watchers
    stmt = (
        select(SchemaWatcherModel)
        .where(
            SchemaWatcherModel.status == DBStatus.ACTIVE,
            SchemaWatcherModel.next_check_at <= datetime.utcnow(),
        )
        .order_by(SchemaWatcherModel.next_check_at.asc())
    )

    result = await session.execute(stmt)
    watchers = result.scalars().all()

    processed = 0
    for watcher in watchers:
        try:
            await service.check_now(watcher.id)
            processed += 1
        except Exception as e:
            logger.error(f"Error processing watcher {watcher.id}: {e}")

    return processed
