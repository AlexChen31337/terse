"""Tests for review_notifier.py"""
import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, call


@pytest.fixture(autouse=True)
def patch_quarantine(tmp_path):
    import scripts.review_notifier as rn
    rn.QUARANTINE_ROOT = tmp_path / "quarantine"
    rn.POLL_INTERVAL   = 0   # no sleep in tests
    rn.QUARANTINE_ROOT.mkdir(parents=True)
    yield tmp_path


def _make_asset(tmp_path, asset_id="abc123", score=20, rec="approve", decision=None):
    import scripts.review_notifier as rn
    dest = rn.QUARANTINE_ROOT / asset_id
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "metadata.json").write_text(json.dumps({
        "name": "test-skill", "asset_type": "ClawHub skill"
    }))
    review = {"scan_score": score, "recommendation": rec, "findings": []}
    if decision:
        review["decision"] = decision
    (dest / "review.json").write_text(json.dumps(review))
    return dest


@patch("scripts.review_notifier._send_telegram")
def test_notify_review_sends_telegram(mock_tg, tmp_path):
    from scripts.review_notifier import notify_review
    _make_asset(tmp_path)
    notify_review("abc123")
    mock_tg.assert_called_once()
    msg = mock_tg.call_args[0][0]
    assert "abc123" in msg or "abc123"[:16] in msg


@patch("scripts.review_notifier._send_telegram")
def test_notify_review_includes_score(mock_tg, tmp_path):
    from scripts.review_notifier import notify_review
    _make_asset(tmp_path, score=55, rec="review")
    notify_review("abc123")
    msg = mock_tg.call_args[0][0]
    assert "55" in msg


@patch("scripts.review_notifier._send_telegram")
def test_notify_with_findings(mock_tg, tmp_path):
    import scripts.review_notifier as rn
    _make_asset(tmp_path, score=45, rec="review")
    dest = rn.QUARANTINE_ROOT / "abc123"
    review = json.loads((dest / "review.json").read_text())
    review["findings"] = [
        {"rule_id": "eval_exec", "description": "eval/exec", "score": 25, "file": "skill.py"},
        {"rule_id": "env_read",  "description": "env read",  "score": 15, "file": "skill.py"},
    ]
    (dest / "review.json").write_text(json.dumps(review))
    from scripts.review_notifier import notify_review
    notify_review("abc123")
    msg = mock_tg.call_args[0][0]
    assert "eval/exec" in msg or "eval" in msg


def test_record_decision_approved(tmp_path):
    from scripts.review_notifier import record_decision
    import scripts.review_notifier as rn
    _make_asset(tmp_path)
    record_decision("abc123", "approved", "looks clean")
    review = json.loads((rn.QUARANTINE_ROOT / "abc123" / "review.json").read_text())
    assert review["decision"] == "approved"
    assert review["reason"] == "looks clean"
    assert "decided_at" in review


def test_record_decision_rejected(tmp_path):
    from scripts.review_notifier import record_decision
    import scripts.review_notifier as rn
    _make_asset(tmp_path)
    record_decision("abc123", "rejected", "uses eval")
    review = json.loads((rn.QUARANTINE_ROOT / "abc123" / "review.json").read_text())
    assert review["decision"] == "rejected"


def test_wait_for_decision_already_decided(tmp_path):
    from scripts.review_notifier import wait_for_decision
    _make_asset(tmp_path, decision="approved")
    result = wait_for_decision("abc123", timeout_hours=0)
    assert result == "approved"


def test_wait_for_decision_timeout(tmp_path):
    from scripts.review_notifier import wait_for_decision
    _make_asset(tmp_path)  # no decision yet
    result = wait_for_decision("abc123", timeout_hours=0)
    assert result == "timeout"


@patch("subprocess.run")
def test_send_telegram_calls_openclaw(mock_run, tmp_path):
    from scripts.review_notifier import _send_telegram
    _send_telegram("hello world")
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "openclaw" in args
    assert "telegram" in args
