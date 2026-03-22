from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
CI_MANIFESTS = REPO_ROOT / ".github" / "ci"


def _load_workflow(path: Path) -> dict[str, object]:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def test_expected_ci_workflow_files_exist() -> None:
    expected = [
        WORKFLOWS / "tests-pr.yml",
        WORKFLOWS / "tests-nightly.yml",
        WORKFLOWS / "docs.yml",
        WORKFLOWS / "release-verification.yml",
        WORKFLOWS / "codeql.yml",
        WORKFLOWS / "_backend-checks.yml",
        WORKFLOWS / "_backend-ratchet.yml",
        WORKFLOWS / "_frontend-checks.yml",
        WORKFLOWS / "_frontend-ratchet.yml",
        WORKFLOWS / "_docs-checks.yml",
        WORKFLOWS / "_security-checks.yml",
        WORKFLOWS / "_secret-integrations.yml",
        WORKFLOWS / "_release-verify.yml",
        CI_MANIFESTS / "backend-ruff-ratchet.txt",
        CI_MANIFESTS / "backend-mypy-ratchet.txt",
        CI_MANIFESTS / "frontend-eslint-ratchet.txt",
        REPO_ROOT / ".github" / "dependabot.yml",
    ]

    for path in expected:
        assert path.exists(), path

    assert not (WORKFLOWS / "trigger-docs.yml").exists()


def test_required_workflows_support_merge_queue_and_reusable_layout() -> None:
    tests_pr = _load_workflow(WORKFLOWS / "tests-pr.yml")
    docs = _load_workflow(WORKFLOWS / "docs.yml")

    assert "merge_group" in tests_pr["on"]
    assert "merge_group" in docs["on"]
    assert tests_pr["permissions"] == "read-all"
    assert docs["permissions"] == "read-all"

    jobs = tests_pr["jobs"]
    assert jobs["preflight"]["uses"] == "./.github/workflows/_security-checks.yml"
    assert jobs["backend-py311"]["uses"] == "./.github/workflows/_backend-checks.yml"
    assert jobs["backend-py312"]["uses"] == "./.github/workflows/_backend-checks.yml"
    assert jobs["backend-ratchet"]["uses"] == "./.github/workflows/_backend-ratchet.yml"
    assert jobs["frontend-node20"]["uses"] == "./.github/workflows/_frontend-checks.yml"
    assert jobs["frontend-ratchet"]["uses"] == "./.github/workflows/_frontend-ratchet.yml"
    assert jobs["docs"]["uses"] == "./.github/workflows/_docs-checks.yml"

    docs_jobs = docs["jobs"]
    assert docs_jobs["docs"]["uses"] == "./.github/workflows/_docs-checks.yml"
    assert docs_jobs["deploy-docs-hook"]["needs"] == "docs"
    assert docs_jobs["deploy-docs-hook"]["environment"] == "docs-deploy"


def test_nightly_workflow_has_matrix_advisory_and_secret_jobs() -> None:
    nightly = _load_workflow(WORKFLOWS / "tests-nightly.yml")
    jobs = nightly["jobs"]

    assert "workflow_dispatch" in nightly["on"]
    dispatch_inputs = nightly["on"]["workflow_dispatch"]["inputs"]
    assert "run_secret_integrations" in dispatch_inputs
    assert "python_matrix" in dispatch_inputs
    assert "node_matrix" in dispatch_inputs
    assert "integration_target" in dispatch_inputs

    assert jobs["backend"]["uses"] == "./.github/workflows/_backend-checks.yml"
    assert jobs["backend-ratchet"]["uses"] == "./.github/workflows/_backend-ratchet.yml"
    assert jobs["frontend"]["uses"] == "./.github/workflows/_frontend-checks.yml"
    assert jobs["frontend-ratchet"]["uses"] == "./.github/workflows/_frontend-ratchet.yml"
    assert jobs["docs"]["uses"] == "./.github/workflows/_docs-checks.yml"
    assert jobs["security-audit"]["uses"] == "./.github/workflows/_security-checks.yml"
    assert jobs["secret-integrations"]["uses"] == "./.github/workflows/_secret-integrations.yml"
    assert jobs["secret-integrations"]["environment"] == "ci-secrets"


def test_ratchet_manifests_are_present_and_non_empty() -> None:
    manifests = {
        "backend-ruff-ratchet.txt": {
            "src/truthound_dashboard/core/secrets.py",
            "src/truthound_dashboard/core/artifacts.py",
            "src/truthound_dashboard/api/artifacts.py",
        },
        "backend-mypy-ratchet.txt": {
            "src/truthound_dashboard/core/secrets.py",
            "src/truthound_dashboard/core/artifacts.py",
            "src/truthound_dashboard/api/artifacts.py",
        },
        "frontend-eslint-ratchet.txt": {
            "frontend/src/api/modules/artifacts.ts",
            "frontend/src/pages/Reports.tsx",
            "frontend/src/pages/Alerts.tsx",
            "frontend/src/pages/History.tsx",
        },
    }

    for filename, expected_entries in manifests.items():
        path = CI_MANIFESTS / filename
        entries = {
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        assert entries
        assert expected_entries <= entries


def test_actions_are_sha_pinned_or_local() -> None:
    uses_pattern = re.compile(r"uses:\s*([^\s]+)")

    for path in sorted(WORKFLOWS.glob("*.yml")):
        for match in uses_pattern.findall(path.read_text(encoding="utf-8")):
            if match.startswith("./"):
                continue
            if re.match(r".+@[0-9a-f]{40}$", match):
                continue
            raise AssertionError(f"Non-pinned third-party action in {path}: {match}")


def test_dependabot_targets_python_node_and_actions() -> None:
    config = _load_workflow(REPO_ROOT / ".github" / "dependabot.yml")
    ecosystems = [entry["package-ecosystem"] for entry in config["updates"]]

    assert "pip" in ecosystems
    assert "npm" in ecosystems
    assert "github-actions" in ecosystems
