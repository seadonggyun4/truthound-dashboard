from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"

GUIDE_TEMPLATE_HEADINGS = [
    "## What this page covers",
    "## Before you start",
    "## UI path or entry point",
    "## Step-by-step workflow",
    "## Expected outputs",
    "## Failure modes and troubleshooting",
    "## Related APIs",
    "## Next steps",
]

API_TEMPLATE_HEADINGS = [
    "## Purpose and permissions",
    "## Canonical endpoints",
    "## Query/filter contract",
    "## Request body shape",
    "## Response shape",
    "## Example request/response",
    "## UI screens that consume the API",
    "## Common errors",
]


def _load_nav() -> list[object]:
    return yaml.safe_load((REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8"))["nav"]


def _collect_nav_paths(nav: list[object]) -> set[Path]:
    collected: set[Path] = set()

    def visit(node: object) -> None:
        if isinstance(node, list):
            for item in node:
                visit(item)
            return
        if isinstance(node, dict):
            for value in node.values():
                visit(value)
            return
        if isinstance(node, str):
            collected.add(DOCS_ROOT / node)

    visit(nav)
    return collected


def _top_level_sections(nav: list[object]) -> dict[str, object]:
    sections: dict[str, object] = {}
    for entry in nav:
        if isinstance(entry, dict):
            sections.update(entry)
    return sections


def _read_all_docs() -> list[Path]:
    return sorted(DOCS_ROOT.rglob("*.md"))


def _all_docs_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in _read_all_docs())


def test_docs_and_readme_drop_stale_product_claims() -> None:
    banned_phrases = [
        "GX Cloud",
        "v1.3.0",
        "289+",
        "mock mode",
        "MSW",
    ]

    targets = [REPO_ROOT / "README.md", *_read_all_docs()]

    for target in targets:
        text = target.read_text(encoding="utf-8")
        for phrase in banned_phrases:
            assert phrase not in text, f"{phrase!r} found in {target}"


def test_readme_preserves_banner_badges_intlayer_and_docs_entrypoints() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert '<img width="1697" height="847"' in readme
    assert "[![PyPI version]" in readme
    assert "[![Powered by Intlayer]" in readme
    assert "## Docs Entry Points" in readme
    assert "https://truthound.netlify.app/dashboard/" in readme
    assert "## Application I18n with Intlayer" in readme
    assert "truthound translate -l ja,zh,de -p openai" in readme
    assert "truthound translate --list-languages" in readme


def test_docs_banner_assets_and_overrides_are_present() -> None:
    mkdocs = yaml.safe_load((REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
    overrides_path = REPO_ROOT / "docs" / "overrides" / "main.html"
    css_path = REPO_ROOT / "docs" / "assets" / "stylesheets" / "banner.css"
    asset_path = REPO_ROOT / "docs" / "assets" / "brand" / "truthound-dashboard-banner.png"

    assert mkdocs["theme"]["custom_dir"] == "docs/overrides"
    assert "assets/stylesheets/banner.css" in mkdocs["extra_css"]
    assert overrides_path.exists()
    assert css_path.exists()
    assert asset_path.exists()

    override_text = overrides_path.read_text(encoding="utf-8")
    assert "dashboard-docs-banner--hero" in override_text
    assert "dashboard-docs-banner--compact" in override_text
    assert "assets/brand/truthound-dashboard-banner.png" in override_text


def test_docs_information_architecture_matches_maturity_target() -> None:
    nav = _load_nav()
    sections = _top_level_sections(nav)

    for label in [
        "Overview",
        "Quickstart",
        "Concepts",
        "Guides",
        "Operations",
        "API Reference",
        "Reference",
        "Migration",
    ]:
        assert label in sections

    assert isinstance(sections["Quickstart"], list)
    assert isinstance(sections["Concepts"], list)
    assert isinstance(sections["Guides"], list)
    assert isinstance(sections["Operations"], list)
    assert isinstance(sections["API Reference"], list)
    assert isinstance(sections["Reference"], list)

    assert len(sections["Quickstart"]) == 6
    assert len(sections["Concepts"]) == 8
    assert len(sections["Operations"]) == 8
    assert len(sections["API Reference"]) == 8
    assert len(sections["Reference"]) == 6
    assert len(sections["Guides"]) >= 20

    nav_paths = _collect_nav_paths(nav)
    assert len(nav_paths) >= 45

    expected_docs = [
        DOCS_ROOT / "index.md",
        DOCS_ROOT / "quickstart/install-and-run.md",
        DOCS_ROOT / "concepts/architecture.md",
        DOCS_ROOT / "guides/source-onboarding.md",
        DOCS_ROOT / "guides/reports-and-datadocs.md",
        DOCS_ROOT / "operations/ci-and-quality-gates.md",
        DOCS_ROOT / "api-reference/artifacts.md",
        DOCS_ROOT / "reference/saved-view-scope-matrix.md",
        DOCS_ROOT / "migration/3.0.md",
    ]

    for path in expected_docs:
        assert path.exists(), path


def test_docs_nav_covers_all_pages_and_meets_budget() -> None:
    nav_paths = _collect_nav_paths(_load_nav())
    docs_files = set(_read_all_docs())

    assert nav_paths == docs_files
    assert len(docs_files) >= 45

    word_count = sum(len(path.read_text(encoding="utf-8").split()) for path in docs_files)
    assert word_count >= 15_000


def test_quickstart_guides_and_operations_use_standard_template() -> None:
    for directory in ["quickstart", "guides", "operations"]:
        for path in sorted((DOCS_ROOT / directory).glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for heading in GUIDE_TEMPLATE_HEADINGS:
                assert heading in text, f"{heading!r} missing in {path}"


def test_api_reference_pages_use_standard_template() -> None:
    for path in sorted((DOCS_ROOT / "api-reference").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for heading in API_TEMPLATE_HEADINGS:
            assert heading in text, f"{heading!r} missing in {path}"


def test_core_concepts_cover_required_product_model_topics() -> None:
    concepts_text = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted((DOCS_ROOT / "concepts").glob("*.md"))
    ).lower()

    for phrase in [
        "workspace",
        "permissions",
        "ownership",
        "secret_refs",
        "artifact",
        "incident",
        "queue",
    ]:
        assert phrase in concepts_text


def test_docs_describe_canonical_artifact_surface_and_saved_view_scope() -> None:
    docs_text = _all_docs_text()
    artifacts_reference = (DOCS_ROOT / "api-reference/artifacts.md").read_text(encoding="utf-8")
    artifact_guide = (DOCS_ROOT / "guides/reports-and-datadocs.md").read_text(encoding="utf-8")
    scope_matrix = (DOCS_ROOT / "reference/saved-view-scope-matrix.md").read_text(
        encoding="utf-8"
    )

    assert "/artifacts" in docs_text
    assert "/artifacts/capabilities" in docs_text
    assert "There is no canonical `/reports/*` REST family." in artifacts_reference
    assert "browser route `/reports`" in docs_text or "route `/reports`" in docs_text
    assert "/reports/validations" not in docs_text
    assert "/reports/formats" not in docs_text
    assert "/reports/locales" not in docs_text
    assert "canonical surface is `/artifacts`" in artifact_guide
    assert "`sources`" in scope_matrix
    assert "`alerts`" in scope_matrix
    assert "`artifacts`" in scope_matrix
    assert "`history`" in scope_matrix
    assert "Global validations list saved views" in scope_matrix
    assert "secret_refs" in docs_text


def test_removed_surfaces_are_absent_from_docs_and_nav() -> None:
    docs_text = _all_docs_text().lower()
    nav_repr = str(_load_nav()).lower()

    for banned in [
        "/reports/validations",
        "docs/data-management/catalog.md",
        "docs/system/maintenance.md",
        "docs/ml-monitoring/model-monitoring.md",
    ]:
        assert banned not in docs_text
        assert banned not in nav_repr

    assert "getting-started.md" not in nav_repr
    assert "advanced/" not in nav_repr
    assert "versioning" not in nav_repr


def test_ci_docs_page_describes_required_and_advisory_gates() -> None:
    ci_doc = (DOCS_ROOT / "operations/ci-and-quality-gates.md").read_text(encoding="utf-8")

    for phrase in [
        "Tests PR",
        "Docs / docs",
        "merge_group",
        "backend-py311",
        "backend-py312",
        "backend-ratchet",
        "frontend-node20",
        "frontend-ratchet",
        "preview-build",
        "backend-advisory-quality",
        "frontend-advisory-quality",
        "security-audit",
        "CodeQL",
        "Release Verification",
        "Dependabot",
        "Phase A",
        "Phase B",
        "Phase C",
        "Required ratchet subtree",
        "backend-ruff-ratchet.txt",
        "frontend-eslint-ratchet.txt",
    ]:
        assert phrase in ci_doc


def test_internal_markdown_links_resolve() -> None:
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

    for path in _read_all_docs():
        text = path.read_text(encoding="utf-8")
        for target in link_pattern.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean_target = target.split("#", 1)[0]
            if not clean_target:
                continue
            resolved = (path.parent / clean_target).resolve()
            assert resolved.exists(), f"Broken link {target!r} in {path}"
