"""
面包多 (mbd.pub) API 客户端
~~~~~~~~~~~~~~~~~~~~~~~~~

核心 API 封装，支持所有面包多开放接口。
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from typing import Any, Optional

import requests


class MbDError(Exception):
    """面包多 API 错误"""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.response = response or {}
        super().__init__(self.message)


# ── 状态 / 类型映射 ──────────────────────────────────────────

PRODUCT_STATES: dict[int, str] = {
    1: "上架",
    4: "下架",
    5: "未审核",
    9: "草稿",
}

STATE_NAME_TO_ID: dict[str, list[int]] = {
    "上架": [1],
    "下架": [4],
    "草稿": [9],
    "全部": [1, 4, 5, 9],
}

PRODUCT_TYPES: dict[int, str] = {
    1: "单品",
    3: "全家桶",
}

NOTIFICATION_TYPES: dict[int, str] = {
    1: "点赞",
    2: "评论",
    3: "购买",
    4: "关注",
    5: "系统",
    6: "新作品",
    7: "回复",
    8: "打赏",
    9: "已购更新",
}

NOTIFICATION_NAME_TO_ID: dict[str, list[int]] = {
    "购买": [3],
    "评论": [2],
    "点赞": [1],
    "全部": [1, 2, 3, 4, 5, 6, 7, 8, 9],
}

CATEGORIES: dict[int, str] = {
    0: "未分类",
    1: "学习",
    2: "绘画",
    3: "素材",
    4: "科技",
    5: "生活",
    6: "播客",
    7: "资料",
    8: "写作",
    9: "其它",
    10: "私密",
    11: "受限制",
    12: "视频",
    13: "手账",
    14: "游戏",
}

CATEGORY_NAME_TO_ID: dict[str, int] = {v: k for k, v in CATEGORIES.items()}

PUSH_SETTINGS: dict[str, int] = {
    "不推": 0,
    "售出": 1,
    "全部": 2,
}

PUSH_ID_TO_NAME: dict[int, str] = {v: k for k, v in PUSH_SETTINGS.items()}

ORDER_STATES: dict[str, str] = {
    "success": "成功",
    "cancel": "已取消",
    "invalid": "无效",
}

PAY_WAYS: dict[str, str] = {
    "alipay": "支付宝",
    "wechat": "微信支付",
    "paypal": "PayPal",
}


def format_datetime(dt_str: str | None) -> str:
    """将 ISO / 各种日期字符串格式化为人类可读的中文格式。"""
    if not dt_str:
        return "—"
    try:
        dt = datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return str(dt_str)


def _load_token_from_store() -> str | None:
    """从加密存储加载 token。"""
    decrypt_script = os.path.expanduser(
        "~/.openclaw/workspace/memory/decrypt.sh"
    )
    if not os.path.exists(decrypt_script):
        return None
    try:
        result = subprocess.run(
            ["bash", decrypt_script, "mbd-token"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            token = result.stdout.strip()
            if "ERROR" in token or "DECRYPT_ERROR" in token:
                return None
            return token
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


class MbDClient:
    """面包多 API 客户端"""

    BASE = "https://x.mbd.pub/api"

    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("MBD_TOKEN") or _load_token_from_store()
        if not self.token:
            raise MbDError("未找到 token。请设置 MBD_TOKEN 环境变量或使用 --token 参数。")
        self._session = requests.Session()
        self._session.headers.update({
            "x-token": self.token,
            "Content-Type": "application/json",
        })

    def _request(self, method: str, path: str, params: dict | None = None, json_body: dict | None = None) -> Any:
        url = f"{self.BASE}{path}"
        try:
            resp = self._session.request(method, url, params=params, json=json_body, timeout=30)
        except requests.RequestException as exc:
            raise MbDError(f"请求失败: {exc}") from exc
        if resp.status_code != 200:
            raise MbDError(
                f"API 返回错误 (HTTP {resp.status_code})",
                status_code=resp.status_code,
                response=resp.json() if resp.text else {},
            )
        try:
            data = resp.json()
        except ValueError as exc:
            raise MbDError("API 返回了非 JSON 数据") from exc
        return data

    def _get(self, path: str, params: dict | None = None, json_body: dict | None = None) -> Any:
        return self._request("GET", path, params=params, json_body=json_body)

    def _post(self, path: str, params: dict | None = None, json_body: dict | None = None) -> Any:
        return self._request("POST", path, params=params, json_body=json_body)

    def _patch(self, path: str, json_body: dict | None = None) -> Any:
        return self._request("PATCH", path, json_body=json_body)

    def _delete(self, path: str, json_body: dict | None = None) -> Any:
        return self._request("DELETE", path, json_body=json_body)

    # ── 产品 ──────────────────────────────────────

    def product_list(self, states: list[int] | None = None, page: int = 1, limit: int = 20) -> dict:
        params = {"page": page, "limit": limit}
        body = {"states": states} if states else None
        return self._get("/product-list", params=params, json_body=body)

    def product_detail(self, urlkey: str) -> dict:
        return self._get("/product-detail", params={"urlkey": urlkey})

    def product_stats(self, urlkey: str) -> dict:
        return self._get("/product-chart", params={"urlkey": urlkey})

    # ── 草稿 / 创建 / 发布 ───────────────────────

    def create_draft(self, productname: str, productdetail: str, productimage: str,
                     producttype: int = 1, productprice: float = 1.0,
                     productcontent: str | None = None, category: int = 0,
                     opendata: int = 0, sale_limit: int = -1, buyer_comment: int = 0) -> dict:
        body: dict[str, Any] = {
            "productname": productname, "producttype": producttype,
            "productdetail": productdetail, "productimage": productimage,
            "productprice": productprice, "category": category,
            "opendata": opendata, "sale_limit": sale_limit, "buyer_comment": buyer_comment,
        }
        if productcontent is not None:
            body["productcontent"] = productcontent
        return self._post("/drafts/", json_body=body)

    def publish_draft(self, productid: int) -> dict:
        return self._post("/drafts/publish/", json_body={"productid": productid})

    def update_draft(self, productid: int, **fields: Any) -> dict:
        body = {"productid": productid, **fields}
        return self._patch("/drafts/", json_body=body)

    # ── 订单 ──────────────────────────────────────

    def order_list(self, page: int = 1, limit: int = 20) -> dict:
        return self._get("/order-list", params={"page": page, "limit": limit})

    def order_detail(self, order_id: str | None = None, out_order_id: str | None = None) -> dict:
        params: dict[str, str] = {}
        if order_id:
            params["order_id"] = order_id
        if out_order_id:
            params["out_order_id"] = out_order_id
        if not params:
            raise MbDError("必须提供 order_id 或 out_order_id")
        return self._get("/order-detail", params=params)

    # ── 通知 ──────────────────────────────────────

    def notifications(self, types: list[int] | None = None) -> dict:
        body = {"types": types} if types else None
        return self._get("/unread-mentions", json_body=body)

    # ── 优惠券 ────────────────────────────────────

    def create_coupon(self, urlkey: str, rate: float) -> dict:
        if not 0 < rate < 1:
            raise MbDError("折扣率必须在 0 到 1 之间（不含边界），例如 0.8 表示八折")
        return self._post("/create-discount", params={"urlkey": urlkey}, json_body={"rate": rate})

    # ── 全家桶 ────────────────────────────────────

    def bundle_list(self) -> dict:
        return self._get("/users/buckets_list/")

    def bundle_add(self, product_id: int, bucket_id: int) -> dict:
        return self._post(f"/products/{product_id}/add_in_bucket/", json_body={"bucketid": bucket_id})

    def bundle_remove(self, product_id: int, bucket_id: int) -> dict:
        return self._delete(f"/products/{product_id}/rm_out_bucket/", json_body={"bucketid": bucket_id})

    # ── 用户资料 ──────────────────────────────────

    def set_bio(self, brief: str) -> dict:
        if len(brief) > 90:
            raise MbDError(f"简介长度 ({len(brief)}) 超过90字限制")
        return self._patch("/set-user-info", json_body={"brief": brief})

    def set_name(self, name: str) -> dict:
        if len(name) > 20:
            raise MbDError(f"昵称长度 ({len(name)}) 超过20字限制")
        return self._patch("/set-user-info", json_body={"name": name})

    def push_settings(self) -> dict:
        return self._get("/message-settings")

    def set_push_settings(self, setting: int) -> dict:
        if setting not in (0, 1, 2):
            raise MbDError("推送设置值必须为 0(不推), 1(只推售出), 2(都推)")
        return self._patch("/set-user-info", json_body={"post_setting": setting})
