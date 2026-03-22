from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from truthound_dashboard.core.control_plane import ControlPlaneService
from truthound_dashboard.core.control_plane import SavedViewService
from truthound_dashboard.core.incidents import IncidentQueueService, IncidentService
from truthound_dashboard.core.overview import OverviewService
from truthound_dashboard.schemas.artifacts import ArtifactCapabilitiesResponse
from truthound_dashboard.db import (
    ArtifactRecord,
    Domain,
    SavedView,
    SourceOwnership,
    Team,
    User,
)
from truthound_dashboard.db.base import Base
from truthound_dashboard.db.database import MIGRATIONS, init_db
from truthound_dashboard.db.models import (
    EscalationIncidentModel,
    EscalationPolicyModel,
    Source,
    Validation,
)
from truthound_dashboard.time import utc_now


@pytest.mark.asyncio
async def test_init_db_creates_versioned_migration_registry_and_control_plane_tables(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "hardening.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    try:
        await init_db(engine)

        async with engine.begin() as conn:
            table_rows = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = {row[0] for row in table_rows.fetchall()}

            migration_rows = await conn.execute(
                text("SELECT version FROM schema_migrations ORDER BY version")
            )
            applied_versions = [row[0] for row in migration_rows.fetchall()]

            queue_rows = await conn.execute(
                text("SELECT slug FROM incident_queues ORDER BY slug")
            )
            queue_slugs = [row[0] for row in queue_rows.fetchall()]

        for table_name in (
            "schema_migrations",
            "permissions",
            "role_permissions",
            "artifact_records",
            "secret_refs",
            "teams",
            "domains",
            "source_ownerships",
            "incident_queues",
            "incident_queue_memberships",
        ):
            assert table_name in tables

        assert applied_versions == [version for version, _description, _fn in MIGRATIONS]
        assert "unassigned" in queue_slugs
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_rbac_permissions_are_normalized_from_legacy_role_json(tmp_path: Path) -> None:
    db_path = tmp_path / "rbac.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    try:
        async with engine.begin() as conn:
            now = utc_now()
            await conn.execute(
                text(
                    """
                    CREATE TABLE roles (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        permissions TEXT,
                        is_system BOOLEAN NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    )
                    """
                )
            )
            await conn.execute(
                text(
                    """
                    INSERT INTO roles (
                        id,
                        name,
                        description,
                        permissions,
                        is_system,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        :id,
                        :name,
                        :description,
                        :permissions,
                        :is_system,
                        :created_at,
                        :updated_at
                    )
                    """
                ),
                {
                    "id": "role-legacy",
                    "name": "legacy_role",
                    "description": "legacy",
                    "permissions": '["sources:read","artifacts:read"]',
                    "is_system": False,
                    "created_at": now,
                    "updated_at": now,
                },
            )

        await init_db(engine)

        async with engine.begin() as conn:
            permission_rows = await conn.execute(
                text("SELECT key FROM permissions ORDER BY key")
            )
            permission_keys = {row[0] for row in permission_rows.fetchall()}

            role_permission_rows = await conn.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM role_permissions rp
                    JOIN permissions p ON p.id = rp.permission_id
                    WHERE rp.role_id = :role_id
                    """
                ),
                {"role_id": "role-legacy"},
            )
            link_count = role_permission_rows.scalar_one()

        assert {"sources:read", "artifacts:read"}.issubset(permission_keys)
        assert link_count == 2
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_generated_reports_are_backfilled_into_artifact_records(tmp_path: Path) -> None:
    db_path = tmp_path / "artifacts.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    try:
        async with engine.begin() as conn:
            now = utc_now()
            await conn.execute(
                text(
                    """
                    CREATE TABLE generated_reports (
                        id TEXT PRIMARY KEY,
                        validation_id TEXT,
                        workspace_id TEXT,
                        source_id TEXT,
                        name TEXT NOT NULL,
                        artifact_type TEXT NOT NULL,
                        description TEXT,
                        format TEXT NOT NULL,
                        theme TEXT,
                        locale TEXT,
                        status TEXT NOT NULL,
                        file_path TEXT,
                        file_size INTEGER,
                        content_hash TEXT,
                        metadata TEXT,
                        error_message TEXT,
                        generation_time_ms REAL,
                        expires_at DATETIME,
                        downloaded_count INTEGER NOT NULL DEFAULT 0,
                        last_downloaded_at DATETIME,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    )
                    """
                )
            )
            await conn.execute(
                text(
                    """
                    INSERT INTO generated_reports (
                        id,
                        validation_id,
                        workspace_id,
                        source_id,
                        name,
                        artifact_type,
                        description,
                        format,
                        theme,
                        locale,
                        status,
                        file_path,
                        file_size,
                        content_hash,
                        metadata,
                        error_message,
                        generation_time_ms,
                        expires_at,
                        downloaded_count,
                        last_downloaded_at,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        :id,
                        NULL,
                        NULL,
                        NULL,
                        :name,
                        :artifact_type,
                        :description,
                        :format,
                        :theme,
                        :locale,
                        :status,
                        :file_path,
                        :file_size,
                        :content_hash,
                        :metadata,
                        NULL,
                        :generation_time_ms,
                        NULL,
                        :downloaded_count,
                        NULL,
                        :created_at,
                        :updated_at
                    )
                    """
                ),
                {
                    "id": "report-1",
                    "name": "Validation Report",
                    "artifact_type": "report",
                    "description": "legacy generated report",
                    "format": "html",
                    "theme": "professional",
                    "locale": "en",
                    "status": "completed",
                    "file_path": "/tmp/report-1.html",
                    "file_size": 128,
                    "content_hash": "abc123",
                    "metadata": '{"origin":"legacy"}',
                    "generation_time_ms": 32.5,
                    "downloaded_count": 3,
                    "created_at": now,
                    "updated_at": now,
                },
            )

        await init_db(engine)

        async with engine.begin() as conn:
            rows = await conn.execute(
                text(
                    """
                    SELECT title, artifact_type, format, status, downloaded_count
                    FROM artifact_records
                    WHERE id = 'report-1'
                    """
                )
            )
            row = rows.fetchone()

        assert row is not None
        assert row[0] == "Validation Report"
        assert row[1] == "report"
        assert row[2] == "html"
        assert row[3] == "completed"
        assert row[4] == 3
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_saved_view_scope_is_limited_to_supported_operational_screens(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "saved-views.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    try:
        await init_db(engine)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as session:
            context = await ControlPlaneService(session).ensure_bootstrap_state()
            with pytest.raises(ValueError):
                await SavedViewService(session).create_view(
                    workspace_id=context.workspace.id,
                    owner_id=context.user.id,
                    scope="validations",
                    name="Invalid scope",
                    description=None,
                    filters={},
                )
    finally:
        await engine.dispose()


def test_artifact_capabilities_contract_is_canonical() -> None:
    capabilities = ArtifactCapabilitiesResponse(
        formats=["html", "csv", "json"],
        themes=["professional", "light", "dark"],
        locales=[],
        artifact_types=["report", "datadocs"],
    )

    assert capabilities.artifact_types == ["report", "datadocs"]


@pytest.mark.asyncio
async def test_inline_source_secrets_are_migrated_to_secret_refs_and_ownership_rows(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "secret-refs.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            now = utc_now()
            await conn.execute(
                text(
                    """
                    INSERT INTO sources (
                        id,
                        name,
                        type,
                        config,
                        description,
                        environment,
                        is_active,
                        workspace_id,
                        created_at,
                        updated_at,
                        credential_updated_at,
                        config_version
                    )
                    VALUES (
                        :id,
                        :name,
                        :type,
                        :config,
                        :description,
                        :environment,
                        1,
                        NULL,
                        :created_at,
                        :updated_at,
                        NULL,
                        1
                    )
                    """
                ),
                {
                    "id": "source-legacy",
                    "name": "Legacy Warehouse",
                    "type": "postgresql",
                    "config": '{"host":"db.internal","password":"super-secret"}',
                    "description": "legacy source",
                    "environment": "production",
                    "created_at": now,
                    "updated_at": now,
                },
            )

        await init_db(engine)

        async with engine.begin() as conn:
            source_rows = await conn.execute(
                text("SELECT workspace_id, config FROM sources WHERE id = 'source-legacy'")
            )
            source_row = source_rows.fetchone()
            secret_ref_rows = await conn.execute(
                text(
                    """
                    SELECT provider, kind, redacted_hint
                    FROM secret_refs
                    WHERE name = 'source:source-legacy:password'
                    """
                )
            )
            secret_ref_row = secret_ref_rows.fetchone()
            ownership_rows = await conn.execute(
                text(
                    """
                    SELECT workspace_id, owner_user_id, team_id, domain_id
                    FROM source_ownerships
                    WHERE source_id = 'source-legacy'
                    """
                )
            )
            ownership_row = ownership_rows.fetchone()

        assert source_row is not None
        assert source_row[0] is not None
        assert '"_secret_ref"' in source_row[1]
        assert secret_ref_row is not None
        assert secret_ref_row[0] == "local-db"
        assert secret_ref_row[1] == "source"
        assert "*" in secret_ref_row[2]
        assert ownership_row is not None
        assert ownership_row[0] == source_row[0]
        assert ownership_row[1] is None
        assert ownership_row[2] is None
        assert ownership_row[3] is None
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_incident_assignment_and_overview_rollups_use_queues_and_artifacts(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "overview.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    try:
        await init_db(engine)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as session:
            context = await ControlPlaneService(session).ensure_bootstrap_state()

            responder = User(
                email="operator@truthound.local",
                display_name="Operator",
                is_active=True,
                is_system=False,
                preferences={},
            )
            session.add(responder)
            await session.flush()

            queue_service = IncidentQueueService(session)
            queue = await queue_service.create_queue(
                workspace_id=context.workspace.id,
                name="Platform Queue",
                description="Primary operational queue",
                member_ids=[responder.id],
            )

            team = Team(
                workspace_id=context.workspace.id,
                name="Platform",
                slug="platform",
                description="Platform team",
                is_active=True,
            )
            domain = Domain(
                workspace_id=context.workspace.id,
                name="Core Data",
                slug="core-data",
                description="Primary domain",
                is_active=True,
            )
            session.add_all([team, domain])
            await session.flush()

            source = Source(
                name="Orders Warehouse",
                type="file",
                workspace_id=context.workspace.id,
                environment="production",
                config={"path": "/tmp/orders.csv"},
                is_active=True,
            )
            session.add(source)
            await session.flush()
            session.add(
                SourceOwnership(
                    source_id=source.id,
                    workspace_id=context.workspace.id,
                    owner_user_id=responder.id,
                    team_id=team.id,
                    domain_id=domain.id,
                )
            )
            await session.flush()

            validation = Validation(
                source_id=source.id,
                status="failed",
                passed=False,
                total_issues=2,
                row_count=128,
                column_count=6,
                result_json={"run_id": "run-1"},
            )
            session.add(validation)
            await session.flush()

            policy = EscalationPolicyModel(
                workspace_id=context.workspace.id,
                name="Primary Policy",
                description="Default escalation policy",
                levels=[{"level": 1, "delay_minutes": 5, "targets": []}],
                auto_resolve_on_success=True,
                max_escalations=3,
                is_active=True,
            )
            session.add(policy)
            await session.flush()

            incident = EscalationIncidentModel(
                policy_id=policy.id,
                workspace_id=context.workspace.id,
                incident_ref=validation.id,
                state="triggered",
                current_level=1,
                escalation_count=0,
                context={
                    "source": "validation",
                    "severity": "high",
                    "source_name": source.name,
                    "title": "Orders validation failed",
                    "message": "Primary warehouse validation failed",
                },
                events=[],
            )
            session.add(incident)

            session.add_all(
                [
                    ArtifactRecord(
                        workspace_id=context.workspace.id,
                        source_id=source.id,
                        validation_id=validation.id,
                        artifact_type="report",
                        format="html",
                        status="completed",
                        title="Orders Report",
                        description="Validation report",
                        file_path="/tmp/orders-report.html",
                        file_size=256,
                        content_hash="report-hash",
                        artifact_metadata={},
                        locale="en",
                        theme="professional",
                    ),
                    ArtifactRecord(
                        workspace_id=context.workspace.id,
                        source_id=source.id,
                        validation_id=validation.id,
                        artifact_type="datadocs",
                        format="html",
                        status="completed",
                        title="Orders Data Docs",
                        description="Validation Data Docs",
                        file_path="/tmp/orders-datadocs.html",
                        file_size=512,
                        content_hash="datadocs-hash",
                        artifact_metadata={},
                        locale="en",
                        theme="professional",
                        created_at=utc_now() - timedelta(days=10),
                    ),
                    SavedView(
                        workspace_id=context.workspace.id,
                        owner_id=context.user.id,
                        scope="alerts",
                        name="Open incidents",
                        description="Open alert workbench filter",
                        filters={"status": "open"},
                        is_default=True,
                    ),
                ]
            )
            await session.commit()

            incident_service = IncidentService(session)
            assigned = await incident_service.assign_incident(
                incident_id=incident.id,
                workspace_id=context.workspace.id,
                actor_user_id=context.user.id,
                actor_name=context.user.display_name,
                assignee_user_id=responder.id,
                queue_id=queue.id,
                message="Assigned during triage",
            )
            await session.commit()

            assert assigned is not None
            assert assigned.queue_id == queue.id
            assert assigned.assignee_user_id == responder.id
            assert any(event.get("type") == "assignment" for event in assigned.timeline or [])

            overview = await OverviewService(session).get_overview(
                workspace_id=context.workspace.id
            )

        backlog = {item["queue_name"]: item["count"] for item in overview["incident_backlog"]}
        artifact_types = {item["artifact_type"]: item["count"] for item in overview["artifact_types"]}
        assignee_names = {item["user_name"]: item["count"] for item in overview["assignee_workload"]}

        assert overview["workspace"]["name"] == "Default Workspace"
        assert overview["sources"]["total"] == 1
        assert overview["incidents"]["active"] == 1
        assert overview["artifacts"]["total"] == 2
        assert overview["artifacts"]["stale"] == 1
        assert backlog["Platform Queue"] == 1
        assert artifact_types["report"] == 1
        assert artifact_types["datadocs"] == 1
        assert assignee_names["Operator"] == 1
        assert overview["sources"]["unowned"] == 0
        assert overview["sources_by_owner"][0]["name"] == "Operator"
        assert overview["sources_by_team"][0]["name"] == "Platform"
        assert overview["sources_by_domain"][0]["name"] == "Core Data"
    finally:
        await engine.dispose()
