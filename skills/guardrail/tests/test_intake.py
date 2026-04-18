"""Tests for intake.py"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def patch_quarantine(tmp_path):
    """Redirect all quarantine paths to tmp_path."""
    import scripts.intake as intake
    intake.QUARANTINE_ROOT = tmp_path / "quarantine"
    intake.BLACKLIST_FILE  = intake.QUARANTINE_ROOT / "blacklist.json"
    intake.APPROVED_FILE   = intake.QUARANTINE_ROOT / "approved.json"
    intake.INTAKE_LOG      = intake.QUARANTINE_ROOT / "intake.log"
    intake.QUARANTINE_ROOT.mkdir(parents=True, exist_ok=True)
    yield


def _make_asset(tmp_path: Path, content: str = "print('hello')") -> Path:
    f = tmp_path / "skill.py"
    f.write_text(content)
    return f


def test_quarantine_new_asset(tmp_path):
    from scripts.intake import intake_asset
    asset = _make_asset(tmp_path)
    result = intake_asset(str(asset), asset_name="test-skill", asset_type="manual")
    assert result["status"] == "quarantined"
    assert "asset_id" in result
    assert Path(result["path"]).exists()


def test_blacklisted_asset(tmp_path):
    from scripts import intake as m
    asset = _make_asset(tmp_path)
    from scripts.intake import intake_asset, _compute_sha256
    sha = _compute_sha256(asset)
    m.BLACKLIST_FILE.write_text(json.dumps([sha]))
    result = intake_asset(str(asset))
    assert result["status"] == "blacklisted"
    assert result["asset_id"] == sha


def test_already_approved_asset(tmp_path):
    from scripts import intake as m
    asset = _make_asset(tmp_path)
    from scripts.intake import intake_asset, _compute_sha256
    sha = _compute_sha256(asset)
    m.APPROVED_FILE.write_text(json.dumps([sha]))
    result = intake_asset(str(asset))
    assert result["status"] == "already_approved"


def test_intake_writes_metadata(tmp_path):
    from scripts.intake import intake_asset
    asset = _make_asset(tmp_path)
    result = intake_asset(str(asset), asset_name="my-skill", asset_type="ClawHub skill", source_url="https://clawhub.com/my-skill")
    dest = Path(result["path"])
    meta = json.loads((dest / "metadata.json").read_text())
    assert meta["name"] == "my-skill"
    assert meta["asset_type"] == "ClawHub skill"
    assert meta["source_url"] == "https://clawhub.com/my-skill"


def test_intake_logs_event(tmp_path):
    from scripts import intake as m
    from scripts.intake import intake_asset
    asset = _make_asset(tmp_path)
    intake_asset(str(asset))
    log_lines = m.INTAKE_LOG.read_text().strip().splitlines()
    assert len(log_lines) == 1
    event = json.loads(log_lines[0])
    assert event["status"] == "quarantined"


def test_intake_missing_source():
    from scripts.intake import intake_asset
    with pytest.raises(FileNotFoundError):
        intake_asset("/nonexistent/path/skill.py")


def test_intake_directory(tmp_path):
    from scripts.intake import intake_asset
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()
    (skill_dir / "main.py").write_text("print('hi')")
    (skill_dir / "utils.py").write_text("x = 1")
    result = intake_asset(str(skill_dir))
    assert result["status"] == "quarantined"


def test_sha256_deterministic(tmp_path):
    from scripts.intake import _compute_sha256
    f = tmp_path / "a.py"
    f.write_text("hello")
    assert _compute_sha256(f) == _compute_sha256(f)


def test_different_content_different_hash(tmp_path):
    from scripts.intake import _compute_sha256
    f1 = tmp_path / "a.py"; f1.write_text("hello")
    f2 = tmp_path / "b.py"; f2.write_text("world")
    assert _compute_sha256(f1) != _compute_sha256(f2)
