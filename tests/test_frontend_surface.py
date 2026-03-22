from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_removed_frontend_routes_are_absent() -> None:
    app_source = (REPO_ROOT / "frontend/src/App.tsx").read_text(encoding="utf-8")
    layout_source = (
        REPO_ROOT / "frontend/src/components/Layout.tsx"
    ).read_text(encoding="utf-8")

    removed_routes = [
        "glossary",
        "catalog",
        "activity",
        "maintenance",
        "drift-monitoring",
        "model-monitoring",
        "schema-watcher",
        "quality-reporter",
    ]

    for route in removed_routes:
        assert f'path="{route}"' not in app_source
        assert f"href: '/{route}'" not in layout_source


def test_kept_frontend_routes_are_present() -> None:
    app_source = (REPO_ROOT / "frontend/src/App.tsx").read_text(encoding="utf-8")
    layout_source = (
        REPO_ROOT / "frontend/src/components/Layout.tsx"
    ).read_text(encoding="utf-8")

    kept_routes = [
        "sources",
        "drift",
        "lineage",
        "schedules",
        "notifications",
        "alerts",
        "plugins",
        "observability",
    ]

    for route in kept_routes:
        assert route in app_source
        assert route in layout_source


def test_frontend_drops_cross_alerts_and_uses_canonical_validation_fields() -> None:
    anomaly_source = (
        REPO_ROOT / "frontend/src/pages/Anomaly.tsx"
    ).read_text(encoding="utf-8")
    validations_api_source = (
        REPO_ROOT / "frontend/src/api/modules/validations.ts"
    ).read_text(encoding="utf-8")

    assert "components/cross-alerts" not in anomaly_source
    assert "run_id?: string" in validations_api_source
    assert "checks: ValidationCheck[]" in validations_api_source
    assert "execution_issues: ExecutionIssue[]" in validations_api_source


def test_frontend_control_plane_and_registry_only_surfaces_are_wired() -> None:
    dashboard_source = (
        REPO_ROOT / "frontend/src/pages/Dashboard.tsx"
    ).read_text(encoding="utf-8")
    sources_source = (
        REPO_ROOT / "frontend/src/pages/Sources.tsx"
    ).read_text(encoding="utf-8")
    reports_source = (
        REPO_ROOT / "frontend/src/pages/Reports.tsx"
    ).read_text(encoding="utf-8")
    artifacts_hook_source = (
        REPO_ROOT / "frontend/src/hooks/useArtifacts.ts"
    ).read_text(encoding="utf-8")
    plugins_source = (
        REPO_ROOT / "frontend/src/pages/Plugins.tsx"
    ).read_text(encoding="utf-8")
    layout_source = (
        REPO_ROOT / "frontend/src/components/Layout.tsx"
    ).read_text(encoding="utf-8")
    source_detail_source = (
        REPO_ROOT / "frontend/src/pages/SourceDetail.tsx"
    ).read_text(encoding="utf-8")
    alerts_source = (
        REPO_ROOT / "frontend/src/pages/Alerts.tsx"
    ).read_text(encoding="utf-8")
    history_source = (
        REPO_ROOT / "frontend/src/pages/History.tsx"
    ).read_text(encoding="utf-8")
    notifications_advanced_source = (
        REPO_ROOT / "frontend/src/pages/NotificationsAdvanced.tsx"
    ).read_text(encoding="utf-8")
    notifications_components_source = (
        REPO_ROOT / "frontend/src/components/notifications/index.ts"
    ).read_text(encoding="utf-8")
    unified_alert_list_source = (
        REPO_ROOT / "frontend/src/components/alerts/UnifiedAlertList.tsx"
    ).read_text(encoding="utf-8")

    assert "getOverview" in dashboard_source
    assert "SavedViewBar" in sources_source
    assert "SavedViewBar" in reports_source
    assert "SavedViewBar" in history_source
    assert "useArtifactIndex" in reports_source
    assert "listArtifacts" in artifacts_hook_source
    assert "getSession" in layout_source
    assert "listCustomValidators" not in plugins_source
    assert "listCustomReporters" not in plugins_source
    assert "customValidators" not in source_detail_source
    assert "custom_validators" not in source_detail_source
    assert "actorName" not in alerts_source
    assert '"actor":' not in alerts_source
    assert "type AlertSource = 'anomaly' | 'validation'" in alerts_source
    assert 'scope="alerts"' in alerts_source
    assert "searchFilter" in alerts_source
    assert "QueuesTab" in notifications_advanced_source
    assert 'value="queues"' in notifications_advanced_source
    assert "QueuesTab" in notifications_components_source
    assert 'value="model"' not in unified_alert_list_source
    assert 'value="drift"' not in unified_alert_list_source
    assert "onAcknowledge" not in unified_alert_list_source
    assert "onResolve" not in unified_alert_list_source
    assert "Search incidents" in unified_alert_list_source


def test_frontend_physical_purge_removes_mock_and_legacy_feature_files() -> None:
    plugins_source = (
        REPO_ROOT / "frontend/src/pages/Plugins.tsx"
    ).read_text(encoding="utf-8")
    drift_api_source = (
        REPO_ROOT / "frontend/src/api/modules/drift.ts"
    ).read_text(encoding="utf-8")
    reports_hook_source = (
        REPO_ROOT / "frontend/src/hooks/useArtifacts.ts"
    ).read_text(encoding="utf-8")
    artifacts_api_source = (
        REPO_ROOT / "frontend/src/api/modules/artifacts.ts"
    ).read_text(encoding="utf-8")
    reporters_preview_source = (
        REPO_ROOT / "frontend/src/components/reporters/ReportPreview.tsx"
    ).read_text(encoding="utf-8")
    reporters_selector_source = (
        REPO_ROOT / "frontend/src/components/reporters/ReporterSelector.tsx"
    ).read_text(encoding="utf-8")
    reporters_download_source = (
        REPO_ROOT / "frontend/src/components/reporters/ReportDownloadButton.tsx"
    ).read_text(encoding="utf-8")

    removed_files = [
        "frontend/src/components/plugins/PluginDependencyGraph.tsx",
        "frontend/src/components/plugins/PluginInstallProgress.tsx",
        "frontend/src/components/drift/DriftMonitorForm.tsx",
        "frontend/src/components/drift/DriftMonitorList.tsx",
        "frontend/src/components/drift/DriftAlertList.tsx",
        "frontend/src/components/drift/DriftMonitorStats.tsx",
        "frontend/src/components/model-monitoring/index.ts",
        "frontend/src/content/catalog.content.ts",
        "frontend/src/content/glossary.content.ts",
        "frontend/src/content/collaboration.content.ts",
        "frontend/src/content/cross-alerts.content.ts",
        "frontend/src/content/drift-monitor.content.ts",
        "frontend/src/content/maintenance.content.ts",
        "frontend/src/content/model-monitoring.content.ts",
        "frontend/src/content/schema-watcher.content.ts",
        "frontend/src/pages/VersionHistory.tsx",
        "frontend/src/api/modules/versioning.ts",
        "frontend/src/api/modules/reports.ts",
        "frontend/src/content/versioning.content.ts",
        "frontend/src/components/versioning/index.ts",
    ]

    for rel_path in removed_files:
        assert not (REPO_ROOT / rel_path).exists(), rel_path

    assert "PluginInstallProgress" not in plugins_source
    assert "showInstallProgress" not in plugins_source
    assert "/drift/monitors" not in drift_api_source
    assert "/drift/alerts" not in drift_api_source
    assert "useArtifactIndex" in reports_hook_source
    assert '"/artifacts"' in artifacts_api_source or "/artifacts" in artifacts_api_source
    assert '"/artifacts/capabilities"' in artifacts_api_source or "/artifacts/capabilities" in artifacts_api_source
    assert "@/api/modules/reports" not in reporters_preview_source
    assert "@/api/modules/reports" not in reporters_selector_source
    assert "@/api/modules/reports" not in reporters_download_source
