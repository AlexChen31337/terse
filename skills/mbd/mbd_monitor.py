"""
MbD (面包多) 销售监控
检查新订单和通知，将新销售输出到 stdout。
可从 heartbeat 调用。
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from typing import Optional

from mbd_client import MbDClient, MbDError

STATE_FILE = os.path.expanduser(
    "~/.openclaw/workspace/memory/mbd-monitor-state.json"
)


def _load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_order_id": None, "last_check": None, "known_order_ids": []}


def _save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def check_new_sales(token: Optional[str] = None, verbose: bool = False) -> list[dict]:
    """
    检查新订单。返回新订单列表。
    有新订单时打印到 stdout。
    """
    state = _load_state()
    known_ids = set(state.get("known_order_ids") or [])

    try:
        client = MbDClient(token=token)
    except MbDError as e:
        print(f"[MbD监控] ❌ 无法连接：{e.message}", file=sys.stderr)
        return []

    # 获取最新订单（第1页）
    try:
        data = client.get_order_list(page=1, limit=50)
    except MbDError as e:
        print(f"[MbD监控] ❌ 获取订单失败：{e}", file=sys.stderr)
        return []

    orders = data.get("orders") or (data if isinstance(data, list) else [])

    new_orders = []
    for order in orders:
        oid = str(order.get("order_id") or order.get("id") or "")
        if not oid:
            continue
        if oid not in known_ids:
            new_orders.append(order)
            known_ids.add(oid)

    # 检查购买通知
    new_notifications = []
    try:
        notif_data = client.get_notifications(types=[3])  # 3=购买
        items = notif_data if isinstance(notif_data, list) else notif_data.get("mentions") or []
        new_notifications = items
    except MbDError:
        pass

    # 输出新销售
    if new_orders:
        print(f"\n🎉 面包多新销售提醒（{datetime.now().strftime('%Y-%m-%d %H:%M')}）")
        print("=" * 50)
        for o in new_orders:
            state_map = {"success": "✅ 成功", "cancel": "❌ 取消", "invalid": "⚠️ 无效"}
            state_label = state_map.get(o.get("state"), str(o.get("state", "-")))
            amount = o.get("orderamount") or o.get("amount") or 0
            urlkey = o.get("urlkey") or o.get("product_url_key") or "-"
            oid_display = o.get("order_id") or o.get("id") or "-"
            print(f"  订单: {oid_display}")
            print(f"  商品: {urlkey}")
            print(f"  金额: ¥{float(amount):.2f}")
            print(f"  状态: {state_label}")
            print("-" * 30)
    elif verbose:
        print(f"[MbD监控] ✅ 暂无新订单（{datetime.now().strftime('%Y-%m-%d %H:%M')}）")

    if new_notifications and verbose:
        print(f"[MbD监控] 📬 {len(new_notifications)} 条购买通知")

    # 更新状态
    state["known_order_ids"] = list(known_ids)
    state["last_check"] = datetime.now().isoformat()
    _save_state(state)

    return new_orders


def main():
    import argparse
    parser = argparse.ArgumentParser(description="MbD 销售监控")
    parser.add_argument("--token", default=None, help="MbD 开发者密钥")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    args = parser.parse_args()

    new_orders = check_new_sales(token=args.token, verbose=args.verbose)
    sys.exit(0 if not new_orders else 0)


if __name__ == "__main__":
    main()
