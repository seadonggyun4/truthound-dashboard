from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from truthound_dashboard.api.notifications import _channel_response
from truthound_dashboard.core import ArtifactService, SavedViewService, SourceService
from truthound_dashboard.core.control_plane import ControlPlaneService
from truthound_dashboard.core.incidents import IncidentQueueService, IncidentService
from truthound_dashboard.core.overview import OverviewService
from truthound_dashboard.db import ArtifactRecord
from truthound_dashboard.db.base import Base
from truthound_dashboard.db.database import init_db
from truthound_dashboard.db.models import EscalationIncidentModel, EscalationPolicyModel, Validation
from truthound_dashboard.schemas.source import SourceResponse
from truthound_dashboard.time import utc_now

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_no_legacy_surface_gate() -> None:
    active_targets = [
        REPO_ROOT / "frontend/src/pages/Reports.tsx",
        REPO_ROOT / "frontend/src/hooks/useArtifacts.ts",
        REPO_ROOT / "frontend/src/api/modules/artifacts.ts",
        REPO_ROOT / "frontend/src/components/reporters/ReportPreview.tsx",
        REPO_ROOT / "frontend/src/components/reporters/ReporterSelector.tsx",
        REPO_ROOT / "frontend/src/components/reporters/ReportDownloadButton.tsx",
        REPO_ROOT / "frontend/src/App.tsx",
        REPO_ROOT / "src/truthound_dashboard/api/artifacts.py",
        REPO_ROOT / "src/truthound_dashboard/api/control_plane.py",
        REPO_ROOT / "src/truthound_dashboard/core/authz.py",
    ]

    banned_markers = [
        "GeneratedReport",
        "/reports/history",
        "/reports/validations",
        "/reports/formats",
        "/reports/locales",
        "sources/:id/versions",
        "Role.permissions",
        "versioning.py",
        "ReportResponse",
        "ReportGenerateRequest",
    ]

    for target in active_targets:
        text_value = target.read_text(encoding="utf-8")
        for marker in banned_markers:
            assert marker not in text_value, f"{marker!r} found in {target}"

    removed_paths = [
        REPO_ROOT / "frontend/src/pages/VersionHistory.tsx",
        REPO_ROOT / "frontend/src/api/modules/versioning.ts",
        REPO_ROOT / "frontend/src/api/modules/reports.ts",
        REPO_ROOT / "src/truthound_dashboard/api/versioning.py",
        REPO_ROOT / "src/truthound_dashboard/core/versioning.py",
        REPO_ROOT / "src/truthound_dashboard/schemas/versioning.py",
        REPO_ROOT / "src/truthound_dashboard/api/reports.py",
        REPO_ROOT / "src/truthound_dashboard/schemas/reports.py",
        REPO_ROOT / "src/truthound_dashboard/core/report_history.py",
    ]
    for path in removed_paths:
        assert not path.exists(), path


def test_no_monolith_services_gate() -> None:
    services_file = REPO_ROOT / "src/truthound_dashboard/core/services.py"
    services_text = services_file.read_text(encoding="utf-8")
    assert not (REPO_ROOT / "src/truthound_dashboard/core/domains/_services_impl.py").exists()

    for forbidden in ("class ", "async def ", "await ", "select(", "mapped_column("):
        assert forbidden not in services_text, f"{forbidden!r} found in {services_file}"

    domain_files = sorted((REPO_ROOT / "src/truthound_dashboard/core/domains").glob("*.py"))
    for path in domain_files:
        if path.name == "__init__.py":
            continue
        text_value = path.read_text(encoding="utf-8")
        assert "from ._services_impl import" not in text_value, f"Legacy wrapper found in {path}"
        assert ("class " in text_value or "def " in text_value), f"No direct implementation found in {path}"

    for path in (REPO_ROOT / "src").rglob("*.py"):
        if path == services_file:
            continue
        if path == REPO_ROOT / "src/truthound_dashboard/core/__init__.py":
            continue
        text_value = path.read_text(encoding="utf-8")
        assert "core.services" not in text_value, f"Legacy core.services import found in {path}"
        assert "from .services import" not in text_value, f"Direct .services import found in {path}"


def test_no_secret_leak_gate() -> None:
    source = SimpleNamespace(
        id="src-1",
        name="Warehouse",
        type="postgresql",
        config={
            "host": "db.internal",
            "password": {"_secret_ref": "secret-1", "hint": "su******et"},
            "token": {"_encrypted": "gAAAAAabcdef"},
        },
        description="primary warehouse",
        environment="production",
        workspace_id="ws-1",
        is_active=True,
        created_at="2026-03-22T12:00:00",
        updated_at="2026-03-22T12:00:00",
        credential_updated_at="2026-03-22T12:00:00",
        config_version=2,
        last_validated_at=None,
        latest_schema=None,
        latest_validation=None,
    )

    response = SourceResponse.from_model(source)

    response_text = response.model_dump_json()
    assert "super-secret" not in response_text
    assert '"_secret_ref"' not in response_text
    assert '"_encrypted"' not in response_text
    assert response.config["password"]["_redacted"] is True
    assert response.config["token"]["_redacted"] is True

    notification_channel = SimpleNamespace(
        id="channel-1",
        name="Slack Alerts",
        type="slack",
        is_active=True,
        config={
            "webhook_url": {
                "_secret_ref": "secret-ref-1",
                "_redacted": True,
                "hint": "ht********************yz",
            },
            "channel": "#alerts",
        },
        config_version=3,
        credential_updated_at=utc_now(),
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    channel_response = _channel_response(notification_channel, include_config=True)
    channel_response_text = channel_response.model_dump_json()
    assert "hooks.slack.com" not in channel_response_text
    assert '"_secret_ref":"secret-ref-1"' in channel_response_text
    assert '"hint":"ht' in channel_response_text


@pytest.mark.asyncio
async def test_migration_smoke_gate_cuts_over_roles_generated_reports_and_secret_refs(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "migration-smoke.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    try:
        async with engine.begin() as conn:
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

        await init_db(engine)

        async with engine.begin() as conn:
            table_rows = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = {row[0] for row in table_rows.fetchall()}
            role_columns = await conn.execute(text("PRAGMA table_info(roles)"))
            role_column_names = {row[1] for row in role_columns.fetchall()}

        assert "generated_reports" not in tables
        assert "artifact_records" in tables
        assert "secret_refs" in tables
        assert "permissions" in tables
        assert "role_permissions" in tables
        assert "permissions" not in role_column_names
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_canonical_e2e_gate_smoke(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "canonical-e2e.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    try:
        await init_db(engine)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as session:
            context = await ControlPlaneService(session).ensure_bootstrap_state()

            source_service = SourceService(session)
            source = await source_service.create(
                name="Warehouse",
                type="postgresql",
                config={
                    "host": "db.internal",
                    "database": "analytics",
                    "user": "service_user",
                    "password": "super-secret",
                },
                environment="production",
                workspace_id=context.workspace.id,
                created_by=context.user.id,
            )

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

            session.add_all(
                [
                    ArtifactRecord(
                        workspace_id=context.workspace.id,
                        source_id=source.id,
                        validation_id=validation.id,
                        artifact_type="report",
                        format="html",
                        status="completed",
                        title="Warehouse Report",
                        description="Validation report",
                        file_path="/tmp/warehouse-report.html",
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
                        title="Warehouse Data Docs",
                        description="Validation docs",
                        file_path="/tmp/warehouse-datadocs.html",
                        file_size=512,
                        content_hash="datadocs-hash",
                        artifact_metadata={},
                        locale="en",
                        theme="professional",
                    ),
                ]
            )

            queue = await IncidentQueueService(session).create_queue(
                workspace_id=context.workspace.id,
                name="Primary Queue",
                description="Default queue",
                member_ids=[context.user.id],
            )
            policy = EscalationPolicyModel(
                workspace_id=context.workspace.id,
                name="Primary Policy",
                description="Default policy",
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
                    "title": "Warehouse validation failed",
                    "message": "Warehouse validation failed",
                },
                events=[],
            )
            session.add(incident)
            await session.flush()

            saved_view_service = SavedViewService(session)
            await saved_view_service.create_view(
                workspace_id=context.workspace.id,
                owner_id=context.user.id,
                scope="artifacts",
                name="Report artifacts",
                filters={"artifact_type": "report", "status": "completed"},
                description="Reusable artifact filter",
                is_default=True,
            )
            await session.commit()

            stored_source = await source_service.get_by_id(source.id)
            assert stored_source is not None
            assert '"super-secret"' not in str(stored_source.config)
            assert "_secret_ref" in str(stored_source.config)

            incident_service = IncidentService(session)
            assigned = await incident_service.assign_incident(
                incident_id=incident.id,
                workspace_id=context.workspace.id,
                actor_user_id=context.user.id,
                actor_name=context.user.display_name,
                assignee_user_id=context.user.id,
                queue_id=queue.id,
                message="Assigned during smoke test",
            )
            assert assigned is not None

            acknowledged = await incident_service.acknowledge_incident(
                incident_id=incident.id,
                workspace_id=context.workspace.id,
                actor=context.user.display_name,
                message="Acknowledged during smoke test",
            )
            resolved = await incident_service.resolve_incident(
                incident_id=incident.id,
                workspace_id=context.workspace.id,
                actor=context.user.display_name,
                message="Resolved during smoke test",
            )
            overview = await OverviewService(session).get_overview(
                workspace_id=context.workspace.id
            )
            views = await saved_view_service.list_views(
                workspace_id=context.workspace.id,
                scope="artifacts",
            )

        assert acknowledged is not None
        assert resolved is not None
        assert overview["artifacts"]["total"] == 2
        assert overview["saved_views"][0]["scope"] == "artifacts"
        assert len(views) == 1
    finally:
        await engine.dispose()
