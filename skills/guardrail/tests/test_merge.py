"""Tests for merge.py"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def patch_paths(tmp_path):
    import scripts.merge as m
    m.QUARANTINE_ROOT = tmp_path / "quarantine"
    m.BLACKLIST_FILE  = m.QUARANTINE_ROOT / "blacklist.json"
    m.APPROVED_FILE   = m.QUARANTINE_ROOT / "approved.json"
    m.SKILLS_ROOT     = tmp_path / "skills"
    m.QUARANTINE_ROOT.mkdir(parents=True, exist_ok=True)
    m.SKILLS_ROOT.mkdir(parents=True, exist_ok=True)
    yield tmp_path


def _make_quarantine(tmp_path, asset_id="abc123", name="test-skill", content="x=1\n"):
    import scripts.merge as m
    dest = m.QUARANTINE_ROOT / asset_id
    raw  = dest / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "main.py").write_text(content)
    (dest / "metadata.json").write_text(json.dumps({"name": name, "asset_type": "manual"}))
    (dest / "review.json").write_text(json.dumps({"scan_score": 10, "recommendation": "approve"}))
    return dest


@patch("scripts.merge._git_commit", return_value=True)
@patch("scripts.merge._send_telegram")
def test_merge_copies_files(mock_tg, mock_git, tmp_path):
    from scripts.merge import merge_asset
    _make_quarantine(tmp_path, "abc123", "test-skill")
    result = merge_asset("abc123")
    assert result["status"] == "merged"
    target = Path(result["path"])
    assert (target / "main.py").exists()


@patch("scripts.merge._git_commit", return_value=True)
@patch("scripts.merge._send_telegram")
def test_merge_adds_to_approved(mock_tg, mock_git, tmp_path):
    import scripts.merge as m
    from scripts.merge import merge_asset
    _make_quarantine(tmp_path, "abc123", "test-skill")
    merge_asset("abc123")
    approved = json.loads(m.APPROVED_FILE.read_text())
    assert "abc123" in approved


@patch("scripts.merge._git_commit", return_value=True)
@patch("scripts.merge._send_telegram")
def test_merge_writes_changelog(mock_tg, mock_git, tmp_path):
    import scripts.merge as m
    from scripts.merge import merge_asset
    _make_quarantine(tmp_path, "abc123", "test-skill")
    result = merge_asset("abc123")
    changelog = (Path(result["path"]) / "CHANGELOG.md").read_text()
    assert "abc123" in changelog
    assert "test-skill" in changelog


@patch("scripts.merge._git_commit", return_value=True)
@patch("scripts.merge._send_telegram")
def test_merge_sends_telegram(mock_tg, mock_git, tmp_path):
    from scripts.merge import merge_asset
    _make_quarantine(tmp_path, "abc123", "test-skill")
    merge_asset("abc123")
    mock_tg.assert_called_once()
    assert "Merged" in mock_tg.call_args[0][0]


@patch("scripts.merge._send_telegram")
def test_reject_adds_to_blacklist(mock_tg, tmp_path):
    import scripts.merge as m
    from scripts.merge import reject_asset
    _make_quarantine(tmp_path, "abc123", "bad-skill")
    reject_asset("abc123", reason="contains eval")
    blacklist = json.loads(m.BLACKLIST_FILE.read_text())
    assert "abc123" in blacklist


@patch("scripts.merge._send_telegram")
def test_reject_updates_review_json(mock_tg, tmp_path):
    import scripts.merge as m
    from scripts.merge import reject_asset
    _make_quarantine(tmp_path, "abc123", "bad-skill")
    reject_asset("abc123", reason="malicious")
    review = json.loads((m.QUARANTINE_ROOT / "abc123" / "review.json").read_text())
    assert review["decision"] == "rejected"
    assert review["reason"] == "malicious"


@patch("scripts.merge._send_telegram")
def test_reject_sends_telegram(mock_tg, tmp_path):
    from scripts.merge import reject_asset
    _make_quarantine(tmp_path, "abc123", "bad-skill")
    reject_asset("abc123", reason="test")
    mock_tg.assert_called_once()
    assert "Rejected" in mock_tg.call_args[0][0]


@patch("scripts.merge._git_commit", return_value=True)
@patch("scripts.merge._send_telegram")
def test_merge_custom_install_dir(mock_tg, mock_git, tmp_path):
    from scripts.merge import merge_asset
    _make_quarantine(tmp_path, "abc123", "test-skill")
    custom = tmp_path / "custom_install"
    result = merge_asset("abc123", install_dir=custom)
    assert Path(result["path"]) == custom
    assert (custom / "main.py").exists()
