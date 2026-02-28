# MbD (面包多) Skill

Interact with the 面包多 (mbd.pub) content monetization platform API.

## Overview

**面包多** is a Chinese content creator monetization platform (like Gumroad/Patreon).
- **Base URL:** `https://x.mbd.pub/api/`
- **Auth:** All requests require header `x-token: <developer_key>`
- **Rate limit:** 10,000 requests/day
- **Docs:** https://mbd.pub/open_doc/

## Credentials

Developer key stored at: `~/.openclaw/workspace/memory/encrypted/mbd-token.enc`

Load key:
```bash
KEY=$(bash ~/.openclaw/workspace/memory/decrypt.sh mbd-token)
```

Or set directly:
```bash
export MBD_TOKEN="<developer_key>"
```

The CLI auto-loads from encrypted store if no `--token` or `MBD_TOKEN` is set.

⚠️ **Note:** The key leaked on 2026-02-28 via Telegram. Bowen must rotate it at https://mbd.pub/o/config/developer before use.

## CLI Tool

### Installation

```bash
cd ~/.openclaw/workspace/skills/mbd
uv pip install -e .  # or just use: uv run python mbd_cli.py
```

### Usage

```bash
# Products
uv run python mbd_cli.py products list                          # 列出所有产品
uv run python mbd_cli.py products list --state 上架              # 只看上架产品
uv run python mbd_cli.py products detail <urlkey>               # 产品详情
uv run python mbd_cli.py products stats <urlkey>                # 近两月浏览/销量统计
uv run python mbd_cli.py products create --name "标题" --detail "描述" --price 9.9 --category 科技
uv run python mbd_cli.py products create --name "教程" --detail "描述" --price 19.9 --category 学习 --content "付费内容"
uv run python mbd_cli.py products publish <productid>           # 发布草稿
uv run python mbd_cli.py products update <productid> --name "新标题" --price 29.9

# Orders
uv run python mbd_cli.py orders list                            # 列出订单
uv run python mbd_cli.py orders list --page 2 --limit 10        # 分页
uv run python mbd_cli.py orders detail <order_id>               # 订单详情

# Notifications
uv run python mbd_cli.py notifications                          # 全部未读通知
uv run python mbd_cli.py notifications --type 购买              # 只看购买通知

# Coupons
uv run python mbd_cli.py coupon create <urlkey> --rate 0.8      # 八折优惠券

# Bundles (全家桶)
uv run python mbd_cli.py bundle list                            # 列出全家桶
uv run python mbd_cli.py bundle add <product_id> --bucket <id>  # 加入全家桶
uv run python mbd_cli.py bundle remove <product_id> --bucket <id>

# Profile
uv run python mbd_cli.py profile set-bio "AI开发者"              # 设置简介 (≤90字)
uv run python mbd_cli.py profile set-name "Alex"                 # 设置昵称 (≤20字)
uv run python mbd_cli.py profile push-settings                   # 查看推送设置
uv run python mbd_cli.py profile push-settings 售出              # 设为仅推售出通知

# Global options
uv run python mbd_cli.py --token <token> products list           # 指定token
```

### Categories

未分类(0), 学习(1), 绘画(2), 素材(3), 科技(4), 生活(5), 播客(6), 资料(7), 写作(8), 其它(9), 私密(10), 受限制(11), 视频(12), 手账(13), 游戏(14)

## Sales Monitor

Poll for new orders and notifications. Designed for HEARTBEAT.md integration.

### Single check
```bash
uv run python mbd_monitor.py --once
```

### Continuous loop (every 30 min)
```bash
uv run python mbd_monitor.py --interval 30
```

### From Python (heartbeat integration)
```python
from mbd_monitor import run_once
result = run_once()
if result:
    print(result)  # New sales found
```

State file: `~/.openclaw/workspace/memory/mbd-monitor-state.json`

## Python API Client

```python
from mbd_client import MbDClient

client = MbDClient()  # Auto-loads token from encrypted store

# Products
products = client.product_list(states=[1], page=1, limit=20)
detail = client.product_detail("urlkey")
stats = client.product_stats("urlkey")

# Create & publish
draft = client.create_draft(
    productname="新产品",
    productdetail="公开描述",
    productimage="https://img.png",
    productprice=9.9,
    category=4,  # 科技
    productcontent="付费内容",
)
client.publish_draft(draft["productid"])

# Orders
orders = client.order_list(page=1, limit=20)
order = client.order_detail(order_id="abc123")

# Notifications
notifs = client.notifications(types=[3])  # 购买通知

# Coupons
coupon = client.create_coupon("urlkey", rate=0.8)

# Bundles
bundles = client.bundle_list()
client.bundle_add(product_id=42, bucket_id=1)
client.bundle_remove(product_id=42, bucket_id=1)

# Profile
client.set_bio("AI开发者")
client.set_name("Alex")
client.set_push_settings(2)  # 0=不推, 1=售出, 2=全部
```

## Templates

Three pre-built product templates available as Python dicts:

```python
from templates import get_template, list_templates

# List available templates
templates = list_templates()
# [{"key": "article", "name": "图文内容模板", ...}, ...]

# Get a template
t = get_template("article")   # 图文内容
t = get_template("file")      # 文件商品
t = get_template("bundle")    # 全家桶

# Use template fields to create a product
client.create_draft(**t["fields"])
```

## API Reference

### Authentication
All endpoints: `x-token: <developer_key>` in request header.

### READ Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/product-list?page=1&limit=20` | GET | 产品列表 (body: `{"states": [1,4,5,9]}`) |
| `/product-detail?urlkey=<key>` | GET | 产品详情 |
| `/product-chart?urlkey=<key>` | GET | 产品统计 (近两月) |
| `/order-list?page=1&limit=20` | GET | 订单列表 |
| `/order-detail?order_id=<id>` | GET | 订单详情 |
| `/unread-mentions` | GET | 未读通知 (body: `{"types": [1,2,3]}`) |
| `/message-settings` | GET | 推送设置 |
| `/users/buckets_list/` | GET | 全家桶列表 |

### WRITE Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/drafts/` | POST | 创建草稿 |
| `/drafts/publish/` | POST | 发布草稿 |
| `/drafts/` | PATCH | 更新草稿 |
| `/create-discount?urlkey=<key>` | POST | 创建优惠券 |
| `/products/{id}/add_in_bucket/` | POST | 加入全家桶 |
| `/products/{id}/rm_out_bucket/` | DELETE | 移出全家桶 |
| `/set-user-info` | PATCH | 更新个人资料 |

### States
- Product: 1=上架, 4=下架, 5=未审核, 9=草稿
- Notification: 1=点赞, 2=评论, 3=购买, 4=关注, 5=系统, 6=新作品, 7=回复, 8=打赏, 9=已购更新
- Push: 0=不推, 1=只推售出, 2=都推

### Webhook

Set callback URL at: https://mbd.pub/o/config/developer
Requires: 闪电结算 (Lightning Settlement) enabled

POST payload on purchase:
```json
{
  "order_id": "3faa1cfd...",
  "out_order_id": "12345678",
  "product_name": "作品名",
  "product_url_key": "urlkey",
  "amount": 9.9,
  "state": 1
}
```
