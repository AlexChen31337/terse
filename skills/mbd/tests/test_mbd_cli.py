"""
面包多 CLI 测试
"""

from __future__ import annotations

import os
import sys

import pytest
import responses
from click.testing import CliRunner

os.environ["MBD_TOKEN"] = "test-token-12345"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mbd_cli import cli

BASE = "https://x.mbd.pub/api"


@pytest.fixture
def runner():
    return CliRunner()


class TestProductsCLI:
    @responses.activate
    def test_products_list(self, runner):
        responses.add(responses.GET, f"{BASE}/product-list",
            json={"count": 1, "products": [
                {"urlkey": "abc", "productname": "Test", "producttype": 1, "productprice": 9.9, "productstates": 1, "publishtime": "2026-02-28T10:00:00"}
            ]})
        r = runner.invoke(cli, ["products", "list"])
        assert r.exit_code == 0
        assert "Test" in r.output
        assert "\u00a59.90" in r.output

    @responses.activate
    def test_products_list_empty(self, runner):
        responses.add(responses.GET, f"{BASE}/product-list", json={"count": 0, "products": []})
        r = runner.invoke(cli, ["products", "list"])
        assert r.exit_code == 0
        assert "\u6682\u65e0" in r.output

    @responses.activate
    def test_products_list_with_state(self, runner):
        responses.add(responses.GET, f"{BASE}/product-list", json={"count": 0, "products": []})
        r = runner.invoke(cli, ["products", "list", "--state", "\u4e0a\u67b6"])
        assert r.exit_code == 0

    @responses.activate
    def test_products_detail(self, runner):
        responses.add(responses.GET, f"{BASE}/product-detail",
            json={"urlkey": "abc", "productname": "Detail", "producttype": 1, "productprice": 19.9,
                  "productstates": 1, "productdetail": "Desc", "producturl": "https://mbd.pub/o/abc",
                  "publishtime": "2026-02-28T10:00:00", "category": 4, "productimage": "https://img.png"})
        r = runner.invoke(cli, ["products", "detail", "abc"])
        assert r.exit_code == 0
        assert "Detail" in r.output

    @responses.activate
    def test_products_detail_bundle(self, runner):
        responses.add(responses.GET, f"{BASE}/product-detail",
            json={"urlkey": "bun", "productname": "Bundle", "producttype": 3, "productprice": 49.9,
                  "productstates": 1, "productdetail": "D", "producturl": "u", "publishtime": "2026-02-28T10:00:00",
                  "category": 4, "productimage": "i", "contain_num": 5, "buckcet_price": 49.9})
        r = runner.invoke(cli, ["products", "detail", "bun"])
        assert r.exit_code == 0
        assert "\u5305\u542b\u6570\u91cf" in r.output

    @responses.activate
    def test_products_stats(self, runner):
        responses.add(responses.GET, f"{BASE}/product-chart",
            json={"view_data": {"2026-02-01": 10, "2026-02-02": 25}, "sold_data": {"2026-02-01": 1}})
        r = runner.invoke(cli, ["products", "stats", "abc"])
        assert r.exit_code == 0
        assert "2026-02-01" in r.output
        assert "\u603b\u6d4f\u89c8" in r.output

    @responses.activate
    def test_products_stats_empty(self, runner):
        responses.add(responses.GET, f"{BASE}/product-chart", json={"view_data": {}, "sold_data": {}})
        r = runner.invoke(cli, ["products", "stats", "abc"])
        assert r.exit_code == 0
        assert "\u6682\u65e0\u7edf\u8ba1" in r.output

    @responses.activate
    def test_products_create(self, runner):
        responses.add(responses.POST, f"{BASE}/drafts/", json={"id": 42, "productid": 42, "urlkey": "new"})
        r = runner.invoke(cli, ["products", "create", "--name", "Test", "--detail", "Desc", "--price", "9.9", "--category", "\u79d1\u6280"])
        assert r.exit_code == 0
        assert "\u8349\u7a3f\u5df2\u521b\u5efa" in r.output

    def test_products_create_invalid_category(self, runner):
        r = runner.invoke(cli, ["products", "create", "--name", "T", "--detail", "D", "--price", "9.9", "--category", "INVALID"])
        assert r.exit_code != 0 or "\u672a\u77e5\u5206\u7c7b" in r.output

    @responses.activate
    def test_products_publish(self, runner):
        responses.add(responses.POST, f"{BASE}/drafts/publish/", json={"producturl": "https://mbd.pub/o/new"})
        r = runner.invoke(cli, ["products", "publish", "42"])
        assert r.exit_code == 0
        assert "\u53d1\u5e03" in r.output

    @responses.activate
    def test_products_update(self, runner):
        responses.add(responses.PATCH, f"{BASE}/drafts/", json={"productid": 42, "productname": "New"})
        r = runner.invoke(cli, ["products", "update", "42", "--name", "New", "--price", "19.9"])
        assert r.exit_code == 0
        assert "\u66f4\u65b0" in r.output

    def test_products_update_no_fields(self, runner):
        r = runner.invoke(cli, ["products", "update", "42"])
        assert r.exit_code != 0 or "\u81f3\u5c11" in r.output


class TestOrdersCLI:
    @responses.activate
    def test_orders_list(self, runner):
        responses.add(responses.GET, f"{BASE}/order-list",
            json={"count": 1, "orders": [{"order_id": "abc-def-123-456", "orderamount": 9.9, "payway": "alipay", "state": "success", "ordertime": "2026-02-28T15:30:00"}]})
        r = runner.invoke(cli, ["orders", "list"])
        assert r.exit_code == 0
        assert "\u00a59.90" in r.output

    @responses.activate
    def test_orders_list_empty(self, runner):
        responses.add(responses.GET, f"{BASE}/order-list", json={"count": 0, "orders": []})
        r = runner.invoke(cli, ["orders", "list"])
        assert r.exit_code == 0
        assert "\u6682\u65e0\u8ba2\u5355" in r.output

    @responses.activate
    def test_orders_detail(self, runner):
        responses.add(responses.GET, f"{BASE}/order-detail",
            json={"order_id": "abc-123", "orderamount": 9.9, "payway": "wechat", "state": "success",
                  "ordertime": "2026-02-28T15:30:00", "urlkey": "prod", "expire_at": None})
        r = runner.invoke(cli, ["orders", "detail", "abc-123"])
        assert r.exit_code == 0
        assert "\u5fae\u4fe1\u652f\u4ed8" in r.output


class TestNotificationsCLI:
    @responses.activate
    def test_notifications_all(self, runner):
        responses.add(responses.GET, f"{BASE}/unread-mentions",
            json={"mentions": [{"type": 3, "content": "Purchase", "created_time": "2026-02-28T14:00:00"}]})
        r = runner.invoke(cli, ["notifications"])
        assert r.exit_code == 0
        assert "\u8d2d\u4e70" in r.output

    @responses.activate
    def test_notifications_empty(self, runner):
        responses.add(responses.GET, f"{BASE}/unread-mentions", json={"mentions": []})
        r = runner.invoke(cli, ["notifications"])
        assert r.exit_code == 0
        assert "\u6682\u65e0\u672a\u8bfb" in r.output

    @responses.activate
    def test_notifications_with_type(self, runner):
        responses.add(responses.GET, f"{BASE}/unread-mentions", json={"mentions": []})
        r = runner.invoke(cli, ["notifications", "--type", "\u8d2d\u4e70"])
        assert r.exit_code == 0


class TestCouponCLI:
    @responses.activate
    def test_coupon_create(self, runner):
        responses.add(responses.POST, f"{BASE}/create-discount",
            json={"urlkey": "abc", "rate": 0.8, "code": "SALE20", "created_time": "2026-02-28T16:00:00"})
        r = runner.invoke(cli, ["coupon", "create", "abc", "--rate", "0.8"])
        assert r.exit_code == 0
        assert "SALE20" in r.output


class TestBundleCLI:
    @responses.activate
    def test_bundle_list(self, runner):
        responses.add(responses.GET, f"{BASE}/users/buckets_list/",
            json={"buckets": [{"id": 1, "name": "AI Bundle", "contain_num": 5, "price": 99.0}]})
        r = runner.invoke(cli, ["bundle", "list"])
        assert r.exit_code == 0
        assert "AI Bundle" in r.output

    @responses.activate
    def test_bundle_list_empty(self, runner):
        responses.add(responses.GET, f"{BASE}/users/buckets_list/", json={"buckets": []})
        r = runner.invoke(cli, ["bundle", "list"])
        assert r.exit_code == 0
        assert "\u6682\u65e0" in r.output

    @responses.activate
    def test_bundle_add(self, runner):
        responses.add(responses.POST, f"{BASE}/products/42/add_in_bucket/", json={"success": True})
        r = runner.invoke(cli, ["bundle", "add", "42", "--bucket", "1"])
        assert r.exit_code == 0
        assert "\u52a0\u5165" in r.output

    @responses.activate
    def test_bundle_remove(self, runner):
        responses.add(responses.DELETE, f"{BASE}/products/42/rm_out_bucket/", json={"success": True})
        r = runner.invoke(cli, ["bundle", "remove", "42", "--bucket", "1"])
        assert r.exit_code == 0
        assert "\u79fb\u9664" in r.output


class TestProfileCLI:
    @responses.activate
    def test_set_bio(self, runner):
        responses.add(responses.PATCH, f"{BASE}/set-user-info", json={"success": True})
        r = runner.invoke(cli, ["profile", "set-bio", "AI Dev"])
        assert r.exit_code == 0
        assert "\u7b80\u4ecb\u5df2\u66f4\u65b0" in r.output

    @responses.activate
    def test_set_name(self, runner):
        responses.add(responses.PATCH, f"{BASE}/set-user-info", json={"success": True})
        r = runner.invoke(cli, ["profile", "set-name", "Alex"])
        assert r.exit_code == 0
        assert "\u6635\u79f0\u5df2\u66f4\u65b0" in r.output

    @responses.activate
    def test_push_settings_view(self, runner):
        responses.add(responses.GET, f"{BASE}/message-settings", json={"type": {2: "All"}})
        r = runner.invoke(cli, ["profile", "push-settings"])
        assert r.exit_code == 0
        assert "\u63a8\u9001\u8bbe\u7f6e" in r.output

    @responses.activate
    def test_push_settings_set(self, runner):
        responses.add(responses.PATCH, f"{BASE}/set-user-info", json={"success": True})
        r = runner.invoke(cli, ["profile", "push-settings", "\u552e\u51fa"])
        assert r.exit_code == 0
        assert "\u552e\u51fa" in r.output


class TestCLIErrors:
    @responses.activate
    def test_api_error(self, runner):
        responses.add(responses.GET, f"{BASE}/product-list", json={"error": "unauthorized"}, status=401)
        r = runner.invoke(cli, ["products", "list"])
        assert r.exit_code != 0

    def test_help(self, runner):
        r = runner.invoke(cli, ["--help"])
        assert r.exit_code == 0
        assert "mbd.pub" in r.output

    def test_products_help(self, runner):
        r = runner.invoke(cli, ["products", "--help"])
        assert r.exit_code == 0


class TestCLIEdgeCases:
    @responses.activate
    def test_products_create_with_content(self, runner):
        responses.add(responses.POST, f"{BASE}/drafts/", json={"id": 1, "productid": 1, "urlkey": "c1"})
        r = runner.invoke(cli, ["products", "create", "--name", "T", "--detail", "D", "--price", "9.9",
                                "--category", "科技", "--content", "paid stuff"])
        assert r.exit_code == 0
        assert "草稿已创建" in r.output

    @responses.activate
    def test_products_update_with_category(self, runner):
        responses.add(responses.PATCH, f"{BASE}/drafts/", json={"productid": 42})
        r = runner.invoke(cli, ["products", "update", "42", "--category", "学习"])
        assert r.exit_code == 0
        assert "更新" in r.output

    def test_products_update_invalid_category(self, runner):
        r = runner.invoke(cli, ["products", "update", "42", "--category", "INVALID"])
        assert r.exit_code != 0 or "未知分类" in r.output

    @responses.activate
    def test_push_settings_view_non_dict(self, runner):
        responses.add(responses.GET, f"{BASE}/message-settings", json={"type": 2})
        r = runner.invoke(cli, ["profile", "push-settings"])
        assert r.exit_code == 0
        assert "推送设置" in r.output

    @responses.activate
    def test_products_create_bundle(self, runner):
        responses.add(responses.POST, f"{BASE}/drafts/", json={"id": 2, "productid": 2, "urlkey": "b1"})
        r = runner.invoke(cli, ["products", "create", "--name", "Bundle", "--detail", "D", "--price", "99.9",
                                "--category", "科技", "--type", "全家桶"])
        assert r.exit_code == 0

    @responses.activate
    def test_products_update_with_all_fields(self, runner):
        responses.add(responses.PATCH, f"{BASE}/drafts/", json={"productid": 42})
        r = runner.invoke(cli, ["products", "update", "42", "--name", "N", "--price", "9.9",
                                "--detail", "D", "--content", "C", "--image-url", "http://x"])
        assert r.exit_code == 0

    @responses.activate
    def test_notifications_list_type(self, runner):
        responses.add(responses.GET, f"{BASE}/unread-mentions",
            json=[{"type": 3, "content": "Buy", "created_time": "2026-02-28T14:00:00"}])
        r = runner.invoke(cli, ["notifications"])
        assert r.exit_code == 0
        assert "购买" in r.output

    @responses.activate
    def test_bundle_list_as_list(self, runner):
        responses.add(responses.GET, f"{BASE}/users/buckets_list/",
            json=[{"id": 1, "name": "B", "contain_num": 2, "price": 19.9}])
        r = runner.invoke(cli, ["bundle", "list"])
        assert r.exit_code == 0
