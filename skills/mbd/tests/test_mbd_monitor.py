"""
面包多监控测试
"""

from __future__ import annotations

import json
import os
import sys
from unittest.mock import patch

import pytest
import responses

os.environ["MBD_TOKEN"] = "test-token-12345"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mbd_monitor import _load_state, _save_state, check_new_orders, check_notifications, report, run_once
from mbd_client import MbDClient

BASE = "https://x.mbd.pub/api"


@pytest.fixture
def client():
    return MbDClient(token="test-token-12345")


@pytest.fixture
def temp_state_file(tmp_path):
    state_file = str(tmp_path / "mbd-monitor-state.json")
    with patch("mbd_monitor.STATE_FILE", state_file):
        yield state_file


class TestStateManagement:
    def test_load_state_no_file(self, temp_state_file):
        state = _load_state()
        assert state["last_order_time"] is None
        assert state["seen_order_ids"] == []

    def test_save_and_load_state(self, temp_state_file):
        state = {"last_order_time": "2026-02-28T16:00:00", "last_order_count": 5,
                 "last_notification_check": "2026-02-28T16:00:00", "seen_order_ids": ["abc", "def"]}
        _save_state(state)
        loaded = _load_state()
        assert loaded["last_order_count"] == 5
        assert "abc" in loaded["seen_order_ids"]


class TestOrderChecks:
    @responses.activate
    def test_check_new_orders_first_run(self, client):
        responses.add(responses.GET, f"{BASE}/order-list",
            json={"count": 2, "orders": [
                {"order_id": "o1", "orderamount": 9.9, "ordertime": "2026-02-28T15:00:00"},
                {"order_id": "o2", "orderamount": 19.9, "ordertime": "2026-02-28T16:00:00"},
            ]})
        state = {"seen_order_ids": [], "last_order_time": None, "last_order_count": 0}
        new = check_new_orders(client, state)
        assert len(new) == 2
        assert "o1" in state["seen_order_ids"]

    @responses.activate
    def test_check_new_orders_seen(self, client):
        responses.add(responses.GET, f"{BASE}/order-list",
            json={"count": 2, "orders": [{"order_id": "o1"}, {"order_id": "o2"}]})
        state = {"seen_order_ids": ["o1", "o2"], "last_order_time": None, "last_order_count": 0}
        new = check_new_orders(client, state)
        assert len(new) == 0

    @responses.activate
    def test_check_new_orders_partial(self, client):
        responses.add(responses.GET, f"{BASE}/order-list",
            json={"count": 2, "orders": [{"order_id": "o1"}, {"order_id": "o3", "orderamount": 29.9}]})
        state = {"seen_order_ids": ["o1"], "last_order_time": None, "last_order_count": 0}
        new = check_new_orders(client, state)
        assert len(new) == 1
        assert new[0]["order_id"] == "o3"

    @responses.activate
    def test_check_orders_api_error(self, client):
        responses.add(responses.GET, f"{BASE}/order-list", json={"error": "fail"}, status=500)
        state = {"seen_order_ids": [], "last_order_time": None, "last_order_count": 0}
        new = check_new_orders(client, state)
        assert len(new) == 0

    @responses.activate
    def test_seen_ids_cap(self, client):
        orders = [{"order_id": f"o{i}", "orderamount": 1.0} for i in range(250)]
        responses.add(responses.GET, f"{BASE}/order-list", json={"count": 250, "orders": orders})
        state = {"seen_order_ids": [], "last_order_time": None, "last_order_count": 0}
        check_new_orders(client, state)
        assert len(state["seen_order_ids"]) == 200


class TestNotificationChecks:
    @responses.activate
    def test_check_notifications(self, client):
        responses.add(responses.GET, f"{BASE}/unread-mentions", json={"mentions": [{"type": 3, "content": "Buy"}]})
        state = {"last_notification_check": None}
        notifs = check_notifications(client, state)
        assert len(notifs) == 1
        assert state["last_notification_check"] is not None

    @responses.activate
    def test_check_notifications_empty(self, client):
        responses.add(responses.GET, f"{BASE}/unread-mentions", json={"mentions": []})
        state = {"last_notification_check": None}
        notifs = check_notifications(client, state)
        assert len(notifs) == 0

    @responses.activate
    def test_check_notifications_error(self, client):
        responses.add(responses.GET, f"{BASE}/unread-mentions", json={"error": "fail"}, status=500)
        state = {"last_notification_check": None}
        notifs = check_notifications(client, state)
        assert len(notifs) == 0


class TestReport:
    def test_with_orders(self):
        orders = [{"order_id": "o1", "orderamount": 9.9, "ordertime": "2026-02-28T15:00:00"},
                  {"order_id": "o2", "orderamount": 19.9, "ordertime": "2026-02-28T16:00:00"}]
        r = report(orders, [])
        assert "2 \u7b14\u65b0\u8ba2\u5355" in r
        assert "\u00a59.90" in r

    def test_with_many_orders(self):
        orders = [{"order_id": f"o{i}", "orderamount": 1.0, "ordertime": "2026-02-28T15:00:00"} for i in range(8)]
        r = report(orders, [])
        assert "8 \u7b14\u65b0\u8ba2\u5355" in r
        assert "\u8fd8\u6709 3 \u7b14" in r

    def test_with_notifications(self):
        r = report([], [{"type": 3, "content": "Buy"}])
        assert "1 \u6761\u65b0\u8d2d\u4e70\u901a\u77e5" in r

    def test_empty(self):
        assert report([], []) == ""

    def test_both(self):
        r = report([{"order_id": "o1", "orderamount": 9.9, "ordertime": "2026-02-28T15:00:00"}],
                   [{"type": 3, "content": "Buy"}])
        assert "\u65b0\u8ba2\u5355" in r
        assert "\u8d2d\u4e70\u901a\u77e5" in r


class TestRunOnce:
    @responses.activate
    def test_with_new_orders(self, temp_state_file):
        responses.add(responses.GET, f"{BASE}/order-list",
            json={"count": 1, "orders": [{"order_id": "o1", "orderamount": 9.9, "ordertime": "2026-02-28T15:00:00"}]})
        responses.add(responses.GET, f"{BASE}/unread-mentions", json={"mentions": []})
        r = run_once()
        assert "\u65b0\u8ba2\u5355" in r

    @responses.activate
    def test_no_news(self, temp_state_file):
        state = {"last_order_time": None, "last_order_count": 0, "last_notification_check": None, "seen_order_ids": ["o1"]}
        _save_state(state)
        responses.add(responses.GET, f"{BASE}/order-list", json={"count": 1, "orders": [{"order_id": "o1"}]})
        responses.add(responses.GET, f"{BASE}/unread-mentions", json={"mentions": []})
        r = run_once()
        assert r == ""

    def test_init_failure(self, temp_state_file):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("MBD_TOKEN", None)
            with patch("mbd_client._load_token_from_store", return_value=None):
                r = run_once()
                assert "\u5931\u8d25" in r or "token" in r.lower()
