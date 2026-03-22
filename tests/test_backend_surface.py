from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from truthound_dashboard.db.database import init_db
from truthound_dashboard.main import create_app
from truthound_dashboard.schemas.source import SourceResponse
from truthound_dashboard.schemas.validation import ValidationResponse

REPO_ROOT = Path(__file__).resolve().parents[1]


def _route_paths() -> set[str]:
    app = create_app()
    return {
        route.path
        for route in app.routes
        if hasattr(route, "path")
    }


def test_kept_api_surfaces_are_exposed() -> None:
    paths = _route_paths()

    expected_prefixes = [
        "/api/v1/auth/session",
        "/api/v1/me",
        "/api/v1/workspaces",
        "/api/v1/users",
        "/api/v1/roles",
        "/api/v1/permissions",
        "/api/v1/views",
        "/api/v1/overview",
        "/api/v1/artifacts",
        "/api/v1/incident-queues",
        "/api/v1/sources",
        "/api/v1/validations",
        "/api/v1/drift",
        "/api/v1/schedules",
        "/api/v1/notifications",
        "/api/v1/plugins",
        "/api/v1/observability",
    ]

    for prefix in expected_prefixes:
        assert any(path.startswith(prefix) for path in paths), prefix


def test_removed_api_surfaces_are_not_registered() -> None:
    paths = _route_paths()

    removed_prefixes = [
        "/api/v1/glossary",
        "/api/v1/catalog",
        "/api/v1/maintenance",
        "/api/v1/model-monitoring",
        "/api/v1/schema-watchers",
        "/api/v1/quality-reporter",
        "/api/v1/versions",
        "/api/v1/reports",
        "/api/v1/validators/custom",
        "/api/v1/reporters/custom",
    ]

    for prefix in removed_prefixes:
        assert not any(path.startswith(prefix) for path in paths), prefix


def test_truthound_3_contract_files_drop_mock_and_legacy_compare() -> None:
    backend_source = (
        REPO_ROOT
        / "src/truthound_dashboard/core/backends/truthound_backend.py"
    ).read_text(encoding="utf-8")
    adapter_source = (
        REPO_ROOT
        / "src/truthound_dashboard/core/truthound_adapter.py"
    ).read_text(encoding="utf-8")
    checkpoint_source = (
        REPO_ROOT
        / "src/truthound_dashboard/core/checkpoint/adapters.py"
    ).read_text(encoding="utf-8")
    scheduler_source = (
        REPO_ROOT
        / "src/truthound_dashboard/core/scheduler.py"
    ).read_text(encoding="utf-8")

    assert "from truthound.drift import compare" in backend_source
    assert "from truthound.drift import compare" in adapter_source
    assert "th.compare" not in backend_source
    assert "th.compare" not in adapter_source
    assert "profiler.generators import Strictness" not in backend_source
    assert "profiler.generators import Strictness" not in adapter_source
    assert "validation_run" in checkpoint_source
    assert "validation_view" in checkpoint_source
    assert "process_due_watchers" not in scheduler_source
    assert "schema_watcher_check" not in scheduler_source
    assert not (
        REPO_ROOT / "src/truthound_dashboard/core/backends/mock_backend.py"
    ).exists()


def test_validation_response_exposes_truthound_3_canonical_run_fields() -> None:
    validation = SimpleNamespace(
        id="val-1",
        source_id="src-1",
        status="failed",
        passed=False,
        has_critical=True,
        has_high=True,
        total_issues=2,
        critical_issues=1,
        high_issues=1,
        medium_issues=0,
        low_issues=0,
        row_count=128,
        column_count=6,
        error_message=None,
        duration_ms=345,
        started_at=None,
        completed_at=None,
        created_at="2026-03-21T12:00:00",
        result_json={
            "run_id": "run_20260321_120000_abcd1234",
            "run_time": "2026-03-21T12:00:00",
            "result_format": "summary",
            "checks": [
                {
                    "name": "null.customer_id",
                    "category": "completeness",
                    "success": False,
                    "issue_count": 1,
                    "issues": [
                        {
                            "column": "customer_id",
                            "issue_type": "null_values",
                            "count": 1,
                            "severity": "critical",
                            "validator_name": "null.customer_id",
                        }
                    ],
                    "metadata": {"column": "customer_id"},
                }
            ],
            "issues": [
                {
                    "column": "customer_id",
                    "issue_type": "null_values",
                    "count": 1,
                    "severity": "critical",
                    "validator_name": "null.customer_id",
                },
                {
                    "column": "email",
                    "issue_type": "invalid_email",
                    "count": 1,
                    "severity": "high",
                    "validator_name": "regex.email",
                },
            ],
            "execution_issues": [
                {
                    "check_name": "regex.email",
                    "message": "temporary adapter failure",
                    "exception_type": "TimeoutError",
                    "failure_category": "transient",
                    "retry_count": 2,
                }
            ],
            "metadata": {"context_root": "/tmp/truthound"},
        },
    )

    response = ValidationResponse.from_model(validation)

    assert response.run_id == "run_20260321_120000_abcd1234"
    assert response.run_time is not None
    assert len(response.checks) == 1
    assert response.checks[0].name == "null.customer_id"
    assert len(response.execution_issues) == 1
    assert response.execution_issues[0].check_name == "regex.email"
    assert response.metadata["context_root"] == "/tmp/truthound"
    assert response.statistics is not None
    assert response.statistics.total_validations == 1
    assert response.exception_summary is not None
    assert response.exception_summary.total_exceptions == 1


def test_source_response_redacts_sensitive_config_fields() -> None:
    source = SimpleNamespace(
        id="src-1",
        name="Warehouse",
        type="postgresql",
        config={
            "host": "db.internal",
            "password": {"_encrypted": "gAAAAAabcdef"},
        },
        description="primary warehouse",
        environment="production",
        workspace_id="ws-1",
        is_active=True,
        created_at="2026-03-21T12:00:00",
        updated_at="2026-03-21T12:00:00",
        credential_updated_at="2026-03-21T12:00:00",
        config_version=2,
        last_validated_at=None,
        latest_schema=None,
        latest_validation=None,
    )

    response = SourceResponse.from_model(source)

    assert response.environment == "production"
    assert response.workspace_id == "ws-1"
    assert response.has_stored_secrets is True
    assert response.config["password"]["_redacted"] is True


def test_alerts_and_validations_drop_free_form_actor_and_custom_validator_inputs() -> None:
    alerts_api_source = (
        REPO_ROOT / "src/truthound_dashboard/api/alerts.py"
    ).read_text(encoding="utf-8")
    validation_api_source = (
        REPO_ROOT / "src/truthound_dashboard/api/validations.py"
    ).read_text(encoding="utf-8")
    validation_schema_source = (
        REPO_ROOT / "src/truthound_dashboard/schemas/validation.py"
    ).read_text(encoding="utf-8")

    assert "request.actor" not in alerts_api_source
    assert "custom_validators" not in validation_api_source
    assert "CustomValidatorConfig" not in validation_schema_source
    assert "custom_validators:" not in validation_schema_source


def test_physical_purge_removes_legacy_db_models_and_custom_reporter_links() -> None:
    db_init_source = (
        REPO_ROOT / "src/truthound_dashboard/db/__init__.py"
    ).read_text(encoding="utf-8")
    db_models_source = (
        REPO_ROOT / "src/truthound_dashboard/db/models.py"
    ).read_text(encoding="utf-8")
    plugin_registry_source = (
        REPO_ROOT / "src/truthound_dashboard/core/plugins/registry.py"
    ).read_text(encoding="utf-8")
    unified_alerts_source = (
        REPO_ROOT / "src/truthound_dashboard/core/unified_alerts.py"
    ).read_text(encoding="utf-8")

    removed_exports = [
        "GlossaryCategory",
        "CatalogAsset",
        "Comment",
        "Activity",
        "MonitoredModel",
        "ModelAlert",
        "DriftMonitor",
        "DriftAlert",
        "CrossAlertConfig",
        "CrossAlertCorrelation",
        "CrossAlertTriggerEvent",
    ]
    for name in removed_exports:
        assert f'"{name}"' not in db_init_source

    removed_tables = [
        '__tablename__ = "glossary_categories"',
        '__tablename__ = "catalog_assets"',
        '__tablename__ = "comments"',
        '__tablename__ = "activities"',
        '__tablename__ = "monitored_models"',
        '__tablename__ = "model_alerts"',
        '__tablename__ = "drift_monitors"',
        '__tablename__ = "drift_alerts"',
        '__tablename__ = "custom_validators"',
        '__tablename__ = "custom_reporters"',
        '__tablename__ = "plugin_execution_logs"',
        '__tablename__ = "plugin_ratings"',
        '__tablename__ = "trusted_signers"',
        '__tablename__ = "security_policies"',
        '__tablename__ = "plugin_signatures"',
        '__tablename__ = "hot_reload_configs"',
        '__tablename__ = "plugin_hooks"',
        '__tablename__ = "schema_watchers"',
        '__tablename__ = "cross_alert_configs"',
    ]
    for table_marker in removed_tables:
        assert table_marker not in db_models_source

    assert not (REPO_ROOT / "src/truthound_dashboard/core/report_history.py").exists()
    assert not (REPO_ROOT / "src/truthound_dashboard/api/reports.py").exists()
    assert not (REPO_ROOT / "src/truthound_dashboard/schemas/reports.py").exists()
    assert "CustomReporter" not in plugin_registry_source
    assert "CustomValidator" not in plugin_registry_source
    assert "AlertSource.MODEL" not in unified_alerts_source
    assert "AlertSource.DRIFT" not in unified_alerts_source
    assert not (
        REPO_ROOT / "src/truthound_dashboard/core/plugins/validator_executor.py"
    ).exists()
    assert not (
        REPO_ROOT / "src/truthound_dashboard/core/plugins/reporter_executor.py"
    ).exists()


def test_legacy_schema_modules_and_compat_exports_are_physically_removed() -> None:
    schemas_init_source = (
        REPO_ROOT / "src/truthound_dashboard/schemas/__init__.py"
    ).read_text(encoding="utf-8")
    validator_base_source = (
        REPO_ROOT / "src/truthound_dashboard/schemas/validators/base.py"
    ).read_text(encoding="utf-8")
    plugins_schema_source = (
        REPO_ROOT / "src/truthound_dashboard/schemas/plugins.py"
    ).read_text(encoding="utf-8")

    removed_modules = [
        "src/truthound_dashboard/schemas/glossary.py",
        "src/truthound_dashboard/schemas/catalog.py",
        "src/truthound_dashboard/schemas/collaboration.py",
        "src/truthound_dashboard/schemas/cross_alerts.py",
        "src/truthound_dashboard/schemas/drift_monitor.py",
        "src/truthound_dashboard/schemas/maintenance.py",
        "src/truthound_dashboard/schemas/model_monitoring.py",
        "src/truthound_dashboard/schemas/schema_watcher.py",
        "src/truthound_dashboard/schemas/validators.py",
    ]

    for rel_path in removed_modules:
        assert not (REPO_ROOT / rel_path).exists(), rel_path

    assert ".glossary" not in schemas_init_source
    assert ".catalog" not in schemas_init_source
    assert ".collaboration" not in schemas_init_source
    assert ".cross_alerts" not in schemas_init_source
    assert ".drift_monitor" not in schemas_init_source
    assert ".maintenance" not in schemas_init_source
    assert ".model_monitoring" not in schemas_init_source
    assert ".schema_watcher" not in schemas_init_source
    assert "CustomValidatorExecuteRequest" not in validator_base_source
    assert "CustomValidatorExecuteResponse" not in validator_base_source
    assert "CustomValidatorBase" not in plugins_schema_source
    assert "CustomReporterBase" not in plugins_schema_source
    assert "class PluginSignature(" not in plugins_schema_source
    assert "class PluginCreate(" not in plugins_schema_source
    assert "class PluginUpdate(" not in plugins_schema_source
    assert "class PluginRatingRequest(" not in plugins_schema_source
    assert "class PluginRatingResponse(" not in plugins_schema_source
    assert "class PluginExecutionContext(" not in plugins_schema_source
    assert "class PluginExecutionResult(" not in plugins_schema_source


def test_db_models_drop_dead_enums_and_registry_only_plugin_aux_tables() -> None:
    db_models_source = (
        REPO_ROOT / "src/truthound_dashboard/db/models.py"
    ).read_text(encoding="utf-8")

    removed_enum_markers = [
        "class TermStatus(",
        "class RelationshipType(",
        "class AssetType(",
        "class SensitivityLevel(",
        "class ResourceType(",
        "class ActivityAction(",
        "class ModelStatus(",
        "class AlertSeverityLevel(",
        "class AlertRuleTypeEnum(",
        "class AlertHandlerTypeEnum(",
    ]

    removed_plugin_aux_markers = [
        "ratings: Mapped[list[\"PluginRating\"]]",
        "signatures: Mapped[list[\"PluginSignature\"]]",
        "hot_reload_config: Mapped[\"HotReloadConfig | None\"]",
        "hooks: Mapped[list[\"PluginHook\"]]",
        "class PluginRating(",
        "class TrustedSigner(",
        "class SecurityPolicy(",
        "class PluginSignature(",
        "class HotReloadConfig(",
        "class PluginHook(",
    ]

    for marker in removed_enum_markers + removed_plugin_aux_markers:
        assert marker not in db_models_source, marker


def test_dormant_backend_helpers_are_physically_removed_and_plugins_are_registry_only() -> None:
    plugins_init_source = (
        REPO_ROOT / "src/truthound_dashboard/core/plugins/__init__.py"
    ).read_text(encoding="utf-8")

    removed_modules = [
        "src/truthound_dashboard/core/cached_services.py",
        "src/truthound_dashboard/core/charts.py",
        "src/truthound_dashboard/core/drift_sampling.py",
        "src/truthound_dashboard/core/plugins/loader.py",
        "src/truthound_dashboard/core/plugins/sandbox.py",
        "src/truthound_dashboard/core/plugins/security.py",
        "src/truthound_dashboard/core/plugins/docs/__init__.py",
        "src/truthound_dashboard/core/plugins/docs/extractor.py",
        "src/truthound_dashboard/core/plugins/docs/renderers.py",
        "src/truthound_dashboard/core/plugins/lifecycle/__init__.py",
        "src/truthound_dashboard/core/plugins/lifecycle/machine.py",
        "src/truthound_dashboard/core/plugins/lifecycle/states.py",
        "src/truthound_dashboard/core/plugins/sandbox/__init__.py",
        "src/truthound_dashboard/core/plugins/sandbox/code_validator.py",
        "src/truthound_dashboard/core/plugins/sandbox/engines.py",
        "src/truthound_dashboard/core/plugins/sandbox/protocols.py",
        "src/truthound_dashboard/core/plugins/security/__init__.py",
        "src/truthound_dashboard/core/plugins/security/analyzer.py",
        "src/truthound_dashboard/core/plugins/security/policies.py",
        "src/truthound_dashboard/core/plugins/security/protocols.py",
        "src/truthound_dashboard/core/plugins/security/signing.py",
        "src/truthound_dashboard/core/plugins/versioning/__init__.py",
        "src/truthound_dashboard/core/plugins/versioning/constraints.py",
        "src/truthound_dashboard/core/plugins/versioning/dependencies.py",
        "src/truthound_dashboard/core/plugins/versioning/semver.py",
    ]

    for rel_path in removed_modules:
        assert not (REPO_ROOT / rel_path).exists(), rel_path

    assert "PluginLoader" not in plugins_init_source
    assert "PluginSandbox" not in plugins_init_source
    assert "PluginSecurityManager" not in plugins_init_source
    assert "SignatureVerifier" not in plugins_init_source
    assert "plugin_registry" in plugins_init_source


def test_control_plane_hardening_surfaces_are_wired_to_permissions_artifacts_and_queues() -> None:
    control_plane_source = (
        REPO_ROOT / "src/truthound_dashboard/api/control_plane.py"
    ).read_text(encoding="utf-8")
    artifacts_api_source = (
        REPO_ROOT / "src/truthound_dashboard/api/artifacts.py"
    ).read_text(encoding="utf-8")
    incident_queues_api_source = (
        REPO_ROOT / "src/truthound_dashboard/api/incident_queues.py"
    ).read_text(encoding="utf-8")
    notifications_advanced_source = (
        REPO_ROOT / "src/truthound_dashboard/api/notifications_advanced.py"
    ).read_text(encoding="utf-8")

    assert '/permissions' in control_plane_source
    assert 'require_permission("permissions:read")' in control_plane_source
    assert 'require_permission("roles:read")' in control_plane_source
    assert 'prefix="/artifacts"' in artifacts_api_source
    assert '"/capabilities"' in artifacts_api_source
    assert "saved_view_id" in artifacts_api_source
    assert "workspace_id" in artifacts_api_source
    assert 'artifact_type="datadocs"' in artifacts_api_source or "/datadocs" in artifacts_api_source
    assert 'require_permission("artifacts:write")' in artifacts_api_source
    assert 'prefix="/incident-queues"' in incident_queues_api_source
    assert "/members" in incident_queues_api_source
    assert 'require_permission("queues:write")' in incident_queues_api_source
    assert "_workspace_filter(RoutingRuleModel" in notifications_advanced_source
    assert "_workspace_filter(DeduplicationConfig" in notifications_advanced_source
    assert "_workspace_filter(ThrottlingConfig" in notifications_advanced_source
    assert "_workspace_filter(EscalationPolicyModel" in notifications_advanced_source


def test_version_history_backend_surface_is_physically_removed() -> None:
    removed_paths = [
        REPO_ROOT / "src/truthound_dashboard/api/versioning.py",
        REPO_ROOT / "src/truthound_dashboard/core/versioning.py",
        REPO_ROOT / "src/truthound_dashboard/schemas/versioning.py",
    ]

    for path in removed_paths:
        assert not path.exists(), path


@pytest.mark.asyncio
async def test_init_db_drops_removed_plugin_aux_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    try:
        async with engine.begin() as conn:
            for table_name in (
                "plugin_ratings",
                "trusted_signers",
                "security_policies",
                "plugin_signatures",
                "hot_reload_configs",
                "plugin_hooks",
            ):
                await conn.execute(text(f"CREATE TABLE {table_name} (id TEXT PRIMARY KEY)"))

        await init_db(engine)

        async with engine.begin() as conn:
            table_rows = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = {row[0] for row in table_rows.fetchall()}

        for table_name in (
            "plugin_ratings",
            "trusted_signers",
            "security_policies",
            "plugin_signatures",
            "hot_reload_configs",
            "plugin_hooks",
        ):
            assert table_name not in tables
    finally:
        await engine.dispose()
