"""
MbD Client 单元测试
使用 responses 库模拟 HTTP 请求，覆盖率目标 ≥ 90%
"""

from __future__ import annotations

import json
import os
import sys
from unittest.mock import patch, MagicMock

import pytest
import responses as resp_lib
from responses import matchers

# 确保 skills/mbd 在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mbd_client import MbDClient, MbDError, _load_token_from_store

BASE = "https://x.mbd.pub/api"


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    return MbDClient(token="test-token-123")


# ─────────────────────────────────────────────────────────────────────────────
# Token loading
# ─────────────────────────────────────────────────────────────────────────────

def test_token_from_env():
    with patch.dict(os.environ, {"MBD_TOKEN": "env-token"}):
        c = MbDClient()
        assert c._token == "env-token"


def test_token_from_arg():
    c = MbDClient(token="explicit-token")
    assert c._token == "explicit-token"


def test_token_from_store():
    with patch("mbd_client._load_token_from_store", return_value="store-token"):
        with patch.dict(os.environ, {}, clear=True):
            # Remove MBD_TOKEN if present
            env = {k: v for k, v in os.environ.items() if k != "MBD_TOKEN"}
            with patch.dict(os.environ, env, clear=True):
                c = MbDClient()
                assert c._token == "store-token"


def test_load_token_from_store_success():
    mock_result = MagicMock()
    mock_result.stdout = "valid-token-abc\n"
    with patch("subprocess.run", return_value=mock_result):
        token = _load_token_from_store()
        assert token == "valid-token-abc"


def test_load_token_from_store_error():
    mock_result = MagicMock()
    mock_result.stdout = "DECRYPT_ERROR\n"
    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(MbDError) as exc_info:
            _load_token_from_store()
        assert exc_info.value.status_code == 0


def test_load_token_from_store_empty():
    mock_result = MagicMock()
    mock_result.stdout = "  \n"
    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(MbDError):
            _load_token_from_store()


# ─────────────────────────────────────────────────────────────────────────────
# MbDError
# ─────────────────────────────────────────────────────────────────────────────

def test_mbd_error_str():
    err = MbDError(404, "商品不存在")
    assert "404" in str(err)
    assert "商品不存在" in str(err)
    assert err.status_code == 404
    assert err.message == "商品不存在"


# ─────────────────────────────────────────────────────────────────────────────
# Products
# ─────────────────────────────────────────────────────────────────────────────

@resp_lib.activate
def test_get_product_list(client):
    payload = {"products": [{"productname": "测试商品", "urlkey": "abc123", "productprice": 9.9}]}
    resp_lib.add(resp_lib.GET, f"{BASE}/product-list", json=payload, status=200)
    result = client.get_product_list()
    assert "products" in result
    assert result["products"][0]["productname"] == "测试商品"


@resp_lib.activate
def test_get_product_list_with_states(client):
    payload = [{"productname": "上架商品", "productstates": 1}]
    resp_lib.add(resp_lib.GET, f"{BASE}/product-list", json=payload, status=200)
    result = client.get_product_list(states=[1], page=2, limit=10)
    assert isinstance(result, list)


@resp_lib.activate
def test_get_product_detail(client):
    payload = {"productname": "AI工具合集", "urlkey": "ai-tools", "productprice": 39.9}
    resp_lib.add(resp_lib.GET, f"{BASE}/product-detail", json=payload, status=200)
    result = client.get_product_detail("ai-tools")
    assert result["productname"] == "AI工具合集"


@resp_lib.activate
def test_get_product_stats(client):
    payload = {"view_data": {"2024-01-01": 100}, "sold_data": {"2024-01-01": 5}}
    resp_lib.add(resp_lib.GET, f"{BASE}/product-chart", json=payload, status=200)
    result = client.get_product_stats("ai-tools")
    assert "view_data" in result
    assert result["sold_data"]["2024-01-01"] == 5


@resp_lib.activate
def test_create_draft(client):
    payload = {"id": 42, "productid": 42, "urlkey": "new-product"}
    resp_lib.add(resp_lib.POST, f"{BASE}/drafts/", json=payload, status=200)
    result = client.create_draft(
        productname="新商品",
        productdetail="这是描述",
        productprice=19.9,
        category=1,
        productimage="https://example.com/img.jpg",
        productcontent="付费内容",
    )
    assert result["productid"] == 42
    assert result["urlkey"] == "new-product"


@resp_lib.activate
def test_publish_draft(client):
    payload = {"url": "https://mbd.pub/p/new-product"}
    resp_lib.add(resp_lib.POST, f"{BASE}/drafts/publish/", json=payload, status=200)
    result = client.publish_draft(42)
    assert "url" in result


@resp_lib.activate
def test_update_draft(client):
    payload = {"success": True}
    resp_lib.add(resp_lib.PATCH, f"{BASE}/drafts/", json=payload, status=200)
    result = client.update_draft(42, productname="新名称", productprice=29.9)
    assert result.get("success") is True


# ─────────────────────────────────────────────────────────────────────────────
# Orders
# ─────────────────────────────────────────────────────────────────────────────

@resp_lib.activate
def test_get_order_list(client):
    payload = {
        "count": 2,
        "orders": [
            {"order_id": "abc", "orderamount": 9.9, "state": "success"},
            {"order_id": "def", "orderamount": 19.9, "state": "cancel"},
        ]
    }
    resp_lib.add(resp_lib.GET, f"{BASE}/order-list", json=payload, status=200)
    result = client.get_order_list()
    assert result["count"] == 2
    assert len(result["orders"]) == 2


@resp_lib.activate
def test_get_order_detail_by_id(client):
    payload = {"order_id": "abc123", "orderamount": 9.9, "state": "success", "urlkey": "test"}
    resp_lib.add(resp_lib.GET, f"{BASE}/order-detail", json=payload, status=200)
    result = client.get_order_detail(order_id="abc123")
    assert result["order_id"] == "abc123"


@resp_lib.activate
def test_get_order_detail_by_out_id(client):
    payload = {"order_id": "abc123", "out_order_id": "custom-001"}
    resp_lib.add(resp_lib.GET, f"{BASE}/order-detail", json=payload, status=200)
    result = client.get_order_detail(out_order_id="custom-001")
    assert result["out_order_id"] == "custom-001"


def test_get_order_detail_no_params(client):
    with pytest.raises(MbDError) as exc_info:
        client.get_order_detail()
    assert exc_info.value.status_code == 0
    assert "order_id" in exc_info.value.message


# ─────────────────────────────────────────────────────────────────────────────
# Notifications
# ─────────────────────────────────────────────────────────────────────────────

@resp_lib.activate
def test_get_notifications_all(client):
    payload = [{"type": 3, "content": "有人购买了你的商品"}]
    resp_lib.add(resp_lib.GET, f"{BASE}/unread-mentions", json=payload, status=200)
    result = client.get_notifications()
    assert len(result) == 1
    assert result[0]["type"] == 3


@resp_lib.activate
def test_get_notifications_filtered(client):
    payload = [{"type": 1, "content": "有人点赞了你的商品"}]
    resp_lib.add(resp_lib.GET, f"{BASE}/unread-mentions", json=payload, status=200)
    result = client.get_notifications(types=[1])
    assert result[0]["type"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# Coupon
# ─────────────────────────────────────────────────────────────────────────────

@resp_lib.activate
def test_create_coupon(client):
    payload = {"urlkey": "ai-tools", "rate": 0.8, "code": "DISC20", "created_time": "2024-01-01T10:00:00"}
    resp_lib.add(resp_lib.POST, f"{BASE}/create-discount", json=payload, status=200)
    result = client.create_coupon("ai-tools", 0.8)
    assert result["code"] == "DISC20"
    assert result["rate"] == 0.8


# ─────────────────────────────────────────────────────────────────────────────
# Bundle
# ─────────────────────────────────────────────────────────────────────────────

@resp_lib.activate
def test_get_bundle_list(client):
    payload = [{"id": 1, "name": "全家桶A", "price": 99.9}]
    resp_lib.add(resp_lib.GET, f"{BASE}/users/buckets_list/", json=payload, status=200)
    result = client.get_bundle_list()
    assert result[0]["name"] == "全家桶A"


@resp_lib.activate
def test_add_to_bundle(client):
    payload = {"success": True}
    resp_lib.add(resp_lib.POST, f"{BASE}/products/123/add_in_bucket/", json=payload, status=200)
    result = client.add_to_bundle(product_id=123, bucket_id=1)
    assert result.get("success") is True


@resp_lib.activate
def test_remove_from_bundle(client):
    payload = {"success": True}
    resp_lib.add(resp_lib.DELETE, f"{BASE}/products/123/rm_out_bucket/", json=payload, status=200)
    result = client.remove_from_bundle(product_id=123, bucket_id=1)
    assert result.get("success") is True


# ─────────────────────────────────────────────────────────────────────────────
# Profile
# ─────────────────────────────────────────────────────────────────────────────

@resp_lib.activate
def test_set_bio(client):
    payload = {"success": True}
    resp_lib.add(resp_lib.PATCH, f"{BASE}/set-user-info", json=payload, status=200)
    result = client.set_bio("这是我的简介")
    assert result.get("success") is True


def test_set_bio_too_long(client):
    long_bio = "字" * 91
    with pytest.raises(MbDError) as exc_info:
        client.set_bio(long_bio)
    assert "90" in exc_info.value.message


@resp_lib.activate
def test_set_name(client):
    payload = {"success": True}
    resp_lib.add(resp_lib.PATCH, f"{BASE}/set-user-info", json=payload, status=200)
    result = client.set_name("Alex陈")
    assert result.get("success") is True


def test_set_name_too_long(client):
    long_name = "字" * 21
    with pytest.raises(MbDError) as exc_info:
        client.set_name(long_name)
    assert "20" in exc_info.value.message


@resp_lib.activate
def test_set_push_settings_valid(client):
    payload = {"success": True}
    resp_lib.add(resp_lib.PATCH, f"{BASE}/set-user-info", json=payload, status=200)
    for setting in (0, 1, 2):
        resp_lib.add(resp_lib.PATCH, f"{BASE}/set-user-info", json=payload, status=200)
        result = client.set_push_settings(setting)
        assert result.get("success") is True


def test_set_push_settings_invalid(client):
    with pytest.raises(MbDError) as exc_info:
        client.set_push_settings(3)
    assert exc_info.value.status_code == 0


@resp_lib.activate
def test_get_push_settings(client):
    payload = {"type": {2: "都推"}}
    resp_lib.add(resp_lib.GET, f"{BASE}/message-settings", json=payload, status=200)
    result = client.get_push_settings()
    assert "type" in result


# ─────────────────────────────────────────────────────────────────────────────
# Error handling
# ─────────────────────────────────────────────────────────────────────────────

@resp_lib.activate
def test_http_404_raises_mbd_error(client):
    resp_lib.add(resp_lib.GET, f"{BASE}/product-detail",
                 json={"detail": "商品不存在"}, status=404)
    with pytest.raises(MbDError) as exc_info:
        client.get_product_detail("not-exist")
    assert exc_info.value.status_code == 404
    assert "商品不存在" in exc_info.value.message


@resp_lib.activate
def test_http_500_raises_mbd_error(client):
    resp_lib.add(resp_lib.GET, f"{BASE}/product-list",
                 body="Internal Server Error", status=500)
    with pytest.raises(MbDError) as exc_info:
        client.get_product_list()
    assert exc_info.value.status_code == 500


@resp_lib.activate
def test_http_401_raises_mbd_error(client):
    resp_lib.add(resp_lib.GET, f"{BASE}/order-list",
                 json={"message": "Token无效"}, status=401)
    with pytest.raises(MbDError) as exc_info:
        client.get_order_list()
    assert exc_info.value.status_code == 401


@resp_lib.activate
def test_response_non_json(client):
    """非 JSON 响应应返回 raw 字段"""
    resp_lib.add(resp_lib.GET, f"{BASE}/product-list",
                 body="OK", status=200,
                 content_type="text/plain")
    result = client.get_product_list()
    assert "raw" in result


@resp_lib.activate
def test_post_returns_dict(client):
    resp_lib.add(resp_lib.POST, f"{BASE}/drafts/", json={"productid": 99}, status=201)
    result = client.create_draft("商品", "描述", 9.9, 0)
    assert result["productid"] == 99


# ─────────────────────────────────────────────────────────────────────────────
# Class constants
# ─────────────────────────────────────────────────────────────────────────────

def test_state_map_coverage():
    assert MbDClient.STATE_MAP["上架"] == 1
    assert MbDClient.STATE_MAP["草稿"] == 9


def test_category_map_coverage():
    assert MbDClient.CATEGORY_MAP["学习"] == 1
    assert MbDClient.CATEGORY_MAP["游戏"] == 14
    assert len(MbDClient.CATEGORY_MAP) == 15


def test_notify_type_map():
    assert MbDClient.NOTIFY_TYPE_MAP["购买"] == 3
    assert MbDClient.NOTIFY_TYPE_MAP["已购更新"] == 9
