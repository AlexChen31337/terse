"""
MbD (面包多) API Client
Core client for interacting with the mbd.pub content monetization platform.
"""

from __future__ import annotations

import os
import subprocess
from typing import Optional

import requests


class MbDError(Exception):
    """面包多 API 错误"""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API错误 [{status_code}]: {message}")


def _load_token_from_store() -> str:
    """从加密存储中加载 MbD token"""
    decrypt_script = os.path.expanduser(
        "~/.openclaw/workspace/memory/decrypt.sh"
    )
    result = subprocess.run(
        ["bash", decrypt_script, "mbd-token"],
        capture_output=True,
        text=True,
    )
    token = result.stdout.strip()
    if not token or "ERROR" in token or "DECRYPT" in token.upper():
        raise MbDError(0, "无法从加密存储加载 token，请设置环境变量 MBD_TOKEN 或使用 --token 参数")
    return token


class MbDClient:
    """面包多 API 客户端"""

    BASE = "https://x.mbd.pub/api"

    # 商品状态映射
    STATE_MAP = {
        "上架": 1,
        "下架": 4,
        "未审核": 5,
        "草稿": 9,
    }

    # 通知类型映射
    NOTIFY_TYPE_MAP = {
        "点赞": 1,
        "评论": 2,
        "购买": 3,
        "关注": 4,
        "系统": 5,
        "新作品": 6,
        "回复": 7,
        "打赏": 8,
        "已购更新": 9,
    }

    # 分类映射
    CATEGORY_MAP = {
        "未分类": 0,
        "学习": 1,
        "绘画": 2,
        "素材": 3,
        "科技": 4,
        "生活": 5,
        "播客": 6,
        "资料": 7,
        "写作": 8,
        "其它": 9,
        "私密": 10,
        "受限制": 11,
        "视频": 12,
        "手账": 13,
        "游戏": 14,
    }

    def __init__(self, token: Optional[str] = None):
        if token is None:
            token = os.environ.get("MBD_TOKEN")
        if token is None:
            token = _load_token_from_store()
        self._token = token
        self._session = requests.Session()
        self._session.headers.update({
            "x-token": token,
            "Content-Type": "application/json",
        })

    def _get(self, path: str, params: Optional[dict] = None, json: Optional[dict] = None) -> dict:
        url = f"{self.BASE}{path}"
        resp = self._session.get(url, params=params, json=json)
        return self._handle(resp)

    def _post(self, path: str, json: Optional[dict] = None, params: Optional[dict] = None) -> dict:
        url = f"{self.BASE}{path}"
        resp = self._session.post(url, json=json, params=params)
        return self._handle(resp)

    def _patch(self, path: str, json: Optional[dict] = None) -> dict:
        url = f"{self.BASE}{path}"
        resp = self._session.patch(url, json=json)
        return self._handle(resp)

    def _delete(self, path: str, json: Optional[dict] = None) -> dict:
        url = f"{self.BASE}{path}"
        resp = self._session.delete(url, json=json)
        return self._handle(resp)

    def _handle(self, resp: requests.Response) -> dict:
        if not resp.ok:
            try:
                detail = resp.json()
                msg = detail.get("detail") or detail.get("message") or resp.text
            except Exception:
                msg = resp.text or "未知错误"
            raise MbDError(resp.status_code, str(msg))
        try:
            return resp.json()
        except Exception:
            return {"raw": resp.text}

    # ── 商品 ──────────────────────────────────────────────

    def get_product_list(
        self,
        states: Optional[list[int]] = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """获取商品列表"""
        body = {"states": states} if states else None
        return self._get("/product-list", params={"page": page, "limit": limit}, json=body)

    def get_product_detail(self, urlkey: str) -> dict:
        """获取商品详情"""
        return self._get("/product-detail", params={"urlkey": urlkey})

    def get_product_stats(self, urlkey: str) -> dict:
        """获取商品统计（近2个月）"""
        return self._get("/product-chart", params={"urlkey": urlkey})

    def create_draft(
        self,
        productname: str,
        productdetail: str,
        productprice: float,
        category: int,
        productimage: str = "",
        productcontent: str = "",
        producttype: int = 1,
        opendata: int = 0,
        sale_limit: int = -1,
        buyer_comment: int = 0,
    ) -> dict:
        """创建草稿"""
        body = {
            "productname": productname,
            "producttype": producttype,
            "productdetail": productdetail,
            "productimage": productimage,
            "productprice": productprice,
            "productcontent": productcontent,
            "category": category,
            "opendata": opendata,
            "sale_limit": sale_limit,
            "buyer_comment": buyer_comment,
        }
        return self._post("/drafts/", json=body)

    def publish_draft(self, productid: int) -> dict:
        """发布草稿"""
        return self._post("/drafts/publish/", json={"productid": productid})

    def update_draft(self, productid: int, **kwargs) -> dict:
        """更新草稿"""
        body = {"productid": productid, **kwargs}
        return self._patch("/drafts/", json=body)

    # ── 订单 ──────────────────────────────────────────────

    def get_order_list(self, page: int = 1, limit: int = 20) -> dict:
        """获取订单列表"""
        return self._get("/order-list", params={"page": page, "limit": limit})

    def get_order_detail(
        self,
        order_id: Optional[str] = None,
        out_order_id: Optional[str] = None,
    ) -> dict:
        """获取订单详情"""
        params: dict = {}
        if order_id:
            params["order_id"] = order_id
        if out_order_id:
            params["out_order_id"] = out_order_id
        if not params:
            raise MbDError(0, "必须提供 order_id 或 out_order_id")
        return self._get("/order-detail", params=params)

    # ── 通知 ──────────────────────────────────────────────

    def get_notifications(self, types: Optional[list[int]] = None) -> dict:
        """获取未读通知"""
        body = {"types": types} if types else None
        return self._get("/unread-mentions", json=body)

    # ── 优惠券 ────────────────────────────────────────────

    def create_coupon(self, urlkey: str, rate: float) -> dict:
        """创建折扣优惠券"""
        return self._post("/create-discount", json={"rate": rate}, params={"urlkey": urlkey})

    # ── 全家桶 ────────────────────────────────────────────

    def get_bundle_list(self) -> dict:
        """获取全家桶列表"""
        return self._get("/users/buckets_list/")

    def add_to_bundle(self, product_id: int, bucket_id: int) -> dict:
        """添加商品到全家桶"""
        return self._post(f"/products/{product_id}/add_in_bucket/", json={"bucketid": bucket_id})

    def remove_from_bundle(self, product_id: int, bucket_id: int) -> dict:
        """从全家桶移除商品"""
        return self._delete(f"/products/{product_id}/rm_out_bucket/", json={"bucketid": bucket_id})

    # ── 用户资料 ──────────────────────────────────────────

    def set_bio(self, brief: str) -> dict:
        """设置个人简介（最多90字）"""
        if len(brief) > 90:
            raise MbDError(0, f"简介不能超过90个字符，当前 {len(brief)} 个字符")
        return self._patch("/set-user-info", json={"brief": brief})

    def set_name(self, name: str) -> dict:
        """设置昵称（最多20字）"""
        if len(name) > 20:
            raise MbDError(0, f"昵称不能超过20个字符，当前 {len(name)} 个字符")
        return self._patch("/set-user-info", json={"name": name})

    def set_push_settings(self, post_setting: int) -> dict:
        """设置推送设置 (0=不推, 1=售出, 2=全部)"""
        if post_setting not in (0, 1, 2):
            raise MbDError(0, "推送设置必须为 0（不推）、1（售出）或 2（全部）")
        return self._patch("/set-user-info", json={"post_setting": post_setting})

    def get_push_settings(self) -> dict:
        """获取推送设置"""
        return self._get("/message-settings")
