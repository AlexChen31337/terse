"""
面包多销售监控
~~~~~~~~~~~~~

轮询新订单和通知，适合从 HEARTBEAT.md 调用。

用法:
    uv run python mbd_monitor.py [--interval 30]
    uv run python mbd_monitor.py --once    # 单次检查
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from mbd_client import MbDClient, MbDError, format_datetime

STATE_FILE = os.path.expanduser(
    "~/.openclaw/workspace/memory/mbd-monitor-state.json"
)


def _load_state() -> dict:
    """加载上次检查状态。"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "last_order_time": None,
        "last_order_count": 0,
        "last_notification_check": None,
        "seen_order_ids": [],
    }


def _save_state(state: dict) -> None:
    """保存状态到文件。"""
    Path(os.path.dirname(STATE_FILE)).mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def check_new_orders(client: MbDClient, state: dict) -> list[dict]:
    """检查新订单，返回新订单列表。"""
    try:
        data = client.order_list(page=1, limit=50)
    except MbDError as exc:
        print(f"⚠️ 获取订单失败: {exc}", file=sys.stderr)
        return []

    orders = data.get("orders", data.get("results", []))
    seen_ids: set[str] = set(state.get("seen_order_ids", []))
    new_orders = []

    for order in orders:
        oid = order.get("order_id", "")
        if oid and oid not in seen_ids:
            new_orders.append(order)
            seen_ids.add(oid)

    # Keep only last 200 IDs to prevent unbounded growth
    state["seen_order_ids"] = list(seen_ids)[-200:]
    state["last_order_count"] = data.get("count", len(orders))
    state["last_order_time"] = datetime.now().isoformat()

    return new_orders


def check_notifications(client: MbDClient, state: dict) -> list[dict]:
    """检查新通知，返回新通知列表。"""
    try:
        data = client.notifications(types=[3])  # 购买通知
    except MbDError as exc:
        print(f"⚠️ 获取通知失败: {exc}", file=sys.stderr)
        return []

    items = data if isinstance(data, list) else data.get("mentions", data.get("results", []))
    state["last_notification_check"] = datetime.now().isoformat()
    return items if items else []


def report(new_orders: list[dict], notifications: list[dict]) -> str:
    """生成报告字符串。"""
    lines: list[str] = []

    if new_orders:
        lines.append(f"🍞 面包多: {len(new_orders)} 笔新订单!")
        for o in new_orders[:5]:  # Show max 5
            amount = o.get("orderamount", 0)
            time_str = format_datetime(o.get("ordertime"))
            lines.append(f"  💰 ¥{amount:.2f} — {time_str}")
        if len(new_orders) > 5:
            lines.append(f"  ... 还有 {len(new_orders) - 5} 笔")

    if notifications:
        lines.append(f"🔔 {len(notifications)} 条新购买通知")

    if not lines:
        return ""

    return "\n".join(lines)


def run_once(client: MbDClient | None = None) -> str:
    """单次检查，返回报告字符串。无新内容返回空字符串。"""
    if client is None:
        try:
            client = MbDClient()
        except MbDError as exc:
            return f"⚠️ 面包多监控初始化失败: {exc}"

    state = _load_state()
    new_orders = check_new_orders(client, state)
    notifications = check_notifications(client, state)
    _save_state(state)

    return report(new_orders, notifications)


def run_loop(interval_minutes: int = 30) -> None:  # pragma: no cover
    """持续监控循环。"""
    try:
        client = MbDClient()
    except MbDError as exc:
        print(f"❌ 初始化失败: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"🍞 面包多销售监控已启动 (每 {interval_minutes} 分钟检查一次)")
    print(f"📁 状态文件: {STATE_FILE}")

    while True:
        result = run_once(client)
        if result:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}]")
            print(result)
        else:
            print(f"[{datetime.now().strftime('%H:%M')}] ✅ 无新动态", end="\r")

        time.sleep(interval_minutes * 60)


def main() -> None:  # pragma: no cover
    """CLI 入口。"""
    import argparse

    parser = argparse.ArgumentParser(description="面包多销售监控")
    parser.add_argument("--interval", type=int, default=30, help="检查间隔 (分钟)")
    parser.add_argument("--once", action="store_true", help="只检查一次")
    parser.add_argument("--token", default=None, help="API token")
    args = parser.parse_args()

    if args.token:
        os.environ["MBD_TOKEN"] = args.token

    if args.once:
        result = run_once()
        if result:
            print(result)
        else:
            print("✅ 面包多: 无新动态")
    else:
        run_loop(args.interval)


if __name__ == "__main__":
    main()
