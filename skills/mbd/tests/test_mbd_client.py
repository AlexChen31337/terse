"""
面包多 API 客户端测试
~~~~~~~~~~~~~~~~~~~

使用 responses 库模拟所有 HTTP 请求。
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

from mbd_client import (
    CATEGORIES,
    CATEGORY_NAME_TO_ID,
    NOTIFICATION_NAME_TO_ID,
    NOTIFICATION_TYPES,
    ORDER_STATES,
    PAY_WAYS,
    PRODUCT_STATES,
    PRODUCT_TYPES,
    PUSH_ID_TO_NAME,
    PUSH_SETTINGS,
    STATE_NAME_TO_ID,
    MbDClient,
    MbDError,
    format_datetime,
    _load_token_from_store,
)

BASE = "https://x.mbd.pub/api"


@pytest.fixture
def client():
    return MbDClient(token="test-token-12345")


class TestTokenLoading:
    def test_token_from_param(self):
        c = MbDClient(token="direct-token")
        assert c.token == "direct-token"

    def test_token_from_env(self):
        with patch.dict(os.environ, {"MBD_TOKEN": "env-token"}):
            c = MbDClient()
            assert c.token == "env-token"

    def test_no_token_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("MBD_TOKEN", None)
            with patch("mbd_client._load_token_from_store", return_value=None):
                with pytest.raises(MbDError, match="token"):
                    MbDClient()

    def test_load_token_no_script(self):
        with patch("os.path.exists", return_value=False):
            assert _load_token_from_store() is None

    def test_load_token_error_string(self):
        with patch("os.path.exists", return_value=True):
            with patch("subprocess.run") as m:
                m.return_value.returncode = 0
                m.return_value.stdout = "some-DECRYPT_ERROR-token"
                assert _load_token_from_store() is None

    def test_load_token_success(self):
        with patch("os.path.exists", return_value=True):
            with patch("subprocess.run") as m:
                m.return_value.returncode = 0
                m.return_value.stdout = "valid-token-123\n"
                assert _load_token_from_store() == "valid-token-123"

    def test_load_token_failure(self):
        with patch("os.path.exists", return_value=True):
            with patch("subprocess.run") as m:
                m.return_value.returncode = 1
                m.return_value.stdout = ""
                assert _load_token_from_store() is None

    def test_load_token_timeout(self):
        import subprocess as sp
        with patch("os.path.exists", return_value=True):
            with patch("subprocess.run", side_effect=sp.TimeoutExpired("cmd", 10)):
                assert _load_token_from_store() is None


class TestProducts:
    @responses.activate
    def test_product_list(self, client):
        responses.add(responses.GET, f"{BASE}/product-list",
            json={"count": 2, "products": [
                {"urlkey": "abc", "productname": "Test", "producttype": 1, "productprice": 9.9, "productstates": 1, "publishtime": "2026-02-28T10:00:00"},
                {"urlkey": "def", "productname": "Bundle", "producttype": 3, "productprice": 49.9, "productstates": 4, "publishtime": "2026-01-15T08:30:00"},
            ]})
        r = client.product_list(states=[1, 4], page=1, limit=20)
        assert r["count"] == 2
        assert len(r["products"]) == 2

    @responses.activate
    def test_product_list_no_states(self, client):
        responses.add(responses.GET, f"{BASE}/product-list", json={"count": 0, "products": []})
        r = client.product_list()
        assert r["count"] == 0

    @responses.activate
    def test_product_detail(self, client):
        responses.add(responses.GET, f"{BASE}/product-detail",
            json={"urlkey": "abc", "productname": "Detail", "producttype": 1, "productprice": 19.9, "productstates": 1, "category": 4})
        r = client.product_detail("abc")
        assert r["productname"] == "Detail"

    @responses.activate
    def test_product_stats(self, client):
        responses.add(responses.GET, f"{BASE}/product-chart",
            json={"view_data": {"2026-02-01": 10}, "sold_data": {"2026-02-01": 1}})
        r = client.product_stats("abc")
        assert r["view_data"]["2026-02-01"] == 10


class TestDrafts:
    @responses.activate
    def test_create_draft(self, client):
        responses.add(responses.POST, f"{BASE}/drafts/", json={"id": 42, "productid": 42, "urlkey": "new"})
        r = client.create_draft(productname="New", productdetail="Desc", productimage="https://img.png",
                                producttype=1, productprice=9.9, category=4)
        assert r["productid"] == 42

    @responses.activate
    def test_create_draft_with_content(self, client):
        responses.add(responses.POST, f"{BASE}/drafts/", json={"productid": 43, "urlkey": "new2"})
        r = client.create_draft(productname="Paid", productdetail="Public", productimage="https://img.png",
                                productcontent="Premium content")
        assert r["productid"] == 43
        req_body = json.loads(responses.calls[0].request.body)
        assert req_body["productcontent"] == "Premium content"

    @responses.activate
    def test_publish_draft(self, client):
        responses.add(responses.POST, f"{BASE}/drafts/publish/", json={"producturl": "https://mbd.pub/o/new"})
        r = client.publish_draft(42)
        assert "producturl" in r

    @responses.activate
    def test_update_draft(self, client):
        responses.add(responses.PATCH, f"{BASE}/drafts/", json={"productid": 42, "productname": "Updated"})
        r = client.update_draft(42, productname="Updated", productprice=19.9)
        req_body = json.loads(responses.calls[0].request.body)
        assert req_body["productid"] == 42
        assert req_body["productprice"] == 19.9


class TestOrders:
    @responses.activate
    def test_order_list(self, client):
        responses.add(responses.GET, f"{BASE}/order-list",
            json={"count": 1, "orders": [{"order_id": "abc-123", "orderamount": 9.9, "payway": "alipay", "state": "success", "ordertime": "2026-02-28T15:30:00"}]})
        r = client.order_list(page=1, limit=10)
        assert r["count"] == 1

    @responses.activate
    def test_order_detail_by_id(self, client):
        responses.add(responses.GET, f"{BASE}/order-detail",
            json={"order_id": "abc-123", "orderamount": 9.9, "payway": "wechat", "state": "success"})
        r = client.order_detail(order_id="abc-123")
        assert r["order_id"] == "abc-123"

    @responses.activate
    def test_order_detail_by_out_id(self, client):
        responses.add(responses.GET, f"{BASE}/order-detail", json={"order_id": "abc-123", "orderamount": 9.9})
        r = client.order_detail(out_order_id="custom-123")
        assert r["order_id"] == "abc-123"

    def test_order_detail_no_id(self, client):
        with pytest.raises(MbDError, match="order_id"):
            client.order_detail()


class TestNotifications:
    @responses.activate
    def test_notifications_all(self, client):
        responses.add(responses.GET, f"{BASE}/unread-mentions",
            json={"mentions": [{"type": 3, "content": "Purchase"}, {"type": 1, "content": "Like"}]})
        r = client.notifications()
        assert len(r["mentions"]) == 2

    @responses.activate
    def test_notifications_filtered(self, client):
        responses.add(responses.GET, f"{BASE}/unread-mentions",
            json={"mentions": [{"type": 3, "content": "Purchase"}]})
        r = client.notifications(types=[3])
        assert len(r["mentions"]) == 1


class TestCoupons:
    @responses.activate
    def test_create_coupon(self, client):
        responses.add(responses.POST, f"{BASE}/create-discount",
            json={"urlkey": "abc", "rate": 0.8, "code": "SALE20", "created_time": "2026-02-28T16:00:00"})
        r = client.create_coupon("abc", 0.8)
        assert r["code"] == "SALE20"

    def test_coupon_invalid_rate_zero(self, client):
        with pytest.raises(MbDError): client.create_coupon("abc", 0)

    def test_coupon_invalid_rate_one(self, client):
        with pytest.raises(MbDError): client.create_coupon("abc", 1)

    def test_coupon_invalid_rate_neg(self, client):
        with pytest.raises(MbDError): client.create_coupon("abc", -0.5)

    def test_coupon_invalid_rate_over(self, client):
        with pytest.raises(MbDError): client.create_coupon("abc", 1.5)


class TestBundles:
    @responses.activate
    def test_bundle_list(self, client):
        responses.add(responses.GET, f"{BASE}/users/buckets_list/",
            json={"buckets": [{"id": 1, "name": "AI Bundle", "contain_num": 5, "price": 99.0}]})
        r = client.bundle_list()
        assert len(r["buckets"]) == 1

    @responses.activate
    def test_bundle_add(self, client):
        responses.add(responses.POST, f"{BASE}/products/42/add_in_bucket/", json={"success": True})
        r = client.bundle_add(42, 1)
        assert r["success"]

    @responses.activate
    def test_bundle_remove(self, client):
        responses.add(responses.DELETE, f"{BASE}/products/42/rm_out_bucket/", json={"success": True})
        r = client.bundle_remove(42, 1)
        assert r["success"]


class TestProfile:
    @responses.activate
    def test_set_bio(self, client):
        responses.add(responses.PATCH, f"{BASE}/set-user-info", json={"success": True})
        r = client.set_bio("AI Developer")
        assert r["success"]

    def test_set_bio_too_long(self, client):
        with pytest.raises(MbDError, match="90"):
            client.set_bio("x" * 91)

    @responses.activate
    def test_set_name(self, client):
        responses.add(responses.PATCH, f"{BASE}/set-user-info", json={"success": True})
        r = client.set_name("Alex")
        assert r["success"]

    def test_set_name_too_long(self, client):
        with pytest.raises(MbDError, match="20"):
            client.set_name("x" * 21)

    @responses.activate
    def test_push_settings(self, client):
        responses.add(responses.GET, f"{BASE}/message-settings", json={"type": {2: "All"}})
        r = client.push_settings()
        assert "type" in r

    @responses.activate
    def test_set_push_settings(self, client):
        responses.add(responses.PATCH, f"{BASE}/set-user-info", json={"success": True})
        r = client.set_push_settings(1)
        assert r["success"]

    def test_set_push_settings_invalid(self, client):
        with pytest.raises(MbDError):
            client.set_push_settings(5)


class TestErrorHandling:
    @responses.activate
    def test_http_error(self, client):
        responses.add(responses.GET, f"{BASE}/product-list", json={"error": "unauthorized"}, status=401)
        with pytest.raises(MbDError, match="HTTP 401"):
            client.product_list()

    @responses.activate
    def test_non_json_response(self, client):
        responses.add(responses.GET, f"{BASE}/product-list", body="<html>Error</html>", status=200, content_type="text/html")
        with pytest.raises(MbDError, match="JSON"):
            client.product_list()

    @responses.activate
    def test_connection_error(self, client):
        import requests as req_lib
        responses.add(responses.GET, f"{BASE}/product-list", body=req_lib.ConnectionError("Connection refused"))
        with pytest.raises(MbDError, match="失败"):
            client.product_list()

    def test_mbd_error_attributes(self):
        err = MbDError("test", status_code=500, response={"detail": "bad"})
        assert err.message == "test"
        assert err.status_code == 500
        assert err.response == {"detail": "bad"}
        assert str(err) == "test"

    def test_mbd_error_defaults(self):
        err = MbDError("simple")
        assert err.status_code is None
        assert err.response == {}


class TestUtilities:
    def test_format_datetime_iso(self):
        assert format_datetime("2026-02-28T16:30:00") == "2026-02-28 16:30"

    def test_format_datetime_with_z(self):
        assert "2026-02-28" in format_datetime("2026-02-28T16:30:00Z")

    def test_format_datetime_none(self):
        assert format_datetime(None) == "\u2014"

    def test_format_datetime_empty(self):
        assert format_datetime("") == "\u2014"

    def test_format_datetime_invalid(self):
        assert format_datetime("not-a-date") == "not-a-date"

    def test_state_mappings(self):
        assert PRODUCT_STATES[1] == "\u4e0a\u67b6"
        assert STATE_NAME_TO_ID["\u4e0a\u67b6"] == [1]
        assert STATE_NAME_TO_ID["\u5168\u90e8"] == [1, 4, 5, 9]

    def test_product_types(self):
        assert PRODUCT_TYPES[1] == "\u5355\u54c1"
        assert PRODUCT_TYPES[3] == "\u5168\u5bb6\u6876"

    def test_notification_types(self):
        assert NOTIFICATION_TYPES[3] == "\u8d2d\u4e70"
        assert NOTIFICATION_NAME_TO_ID["\u8d2d\u4e70"] == [3]

    def test_categories(self):
        assert CATEGORIES[4] == "\u79d1\u6280"
        assert CATEGORY_NAME_TO_ID["\u79d1\u6280"] == 4
        assert len(CATEGORIES) == 15

    def test_push_settings(self):
        assert PUSH_SETTINGS["\u4e0d\u63a8"] == 0
        assert PUSH_ID_TO_NAME[0] == "\u4e0d\u63a8"

    def test_order_states(self):
        assert ORDER_STATES["success"] == "\u6210\u529f"

    def test_pay_ways(self):
        assert PAY_WAYS["alipay"] == "\u652f\u4ed8\u5b9d"

    def test_headers_set(self, client):
        assert client._session.headers["x-token"] == "test-token-12345"
