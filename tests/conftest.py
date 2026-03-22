from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


@pytest.fixture(autouse=True)
def isolate_dashboard_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Keep tests isolated from the user's real dashboard data directory."""
    from truthound_dashboard.config import reset_settings
    from truthound_dashboard.core.encryption import reset_encryptor

    data_dir = tmp_path / ".truthound-test"
    monkeypatch.setenv("TRUTHOUND_DATA_DIR", str(data_dir))
    reset_settings()
    reset_encryptor()
    yield
    reset_encryptor()
    reset_settings()
