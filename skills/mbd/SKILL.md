# MbD (面包多) Skill

Interact with the 面包多 (mbd.pub) content monetization platform API.

## Overview

**面包多** is a Chinese content creator monetization platform (like Gumroad/Patreon).
- **Base URL:** `https://x.mbd.pub/api/`
- **Auth:** All requests require header `x-token: <developer_key>`
- **Rate limit:** 10,000 requests/day
- **Docs:** https://mbd.pub/open_doc/ (Docsify, raw markdown at https://mbd.pub/open_doc/<page>.md)

## Credentials

Developer key stored at: `~/.openclaw/workspace/memory/encrypted/mbd-token.enc`

To load key (after Bowen stores it):
```bash
KEY=$(bash ~/.openclaw/workspace/memory/decrypt.sh mbd-token)
```

Or set directly in env:
```bash
export MBD_TOKEN="<developer_key>"
```

**⚠️ Note:** The key leaked on 2026-02-28 via Telegram. Bowen must rotate it at https://mbd.pub/o/config/developer before use.

## API Reference

### Authentication
All endpoints: `x-token: <developer_key>` in request header.

---

### READ Endpoints

#### Get Order by ID
```
GET https://x.mbd.pub/api/order-detail?order_id=<id>
GET https://x.mbd.pub/api/order-detail?out_order_id=<custom_id>
```
Returns: ordertime, orderamount, payway, state (success/cancel/invalid), urlkey, expire_at, rounds, re (latest renewal)

#### Get All Orders
```
GET https://x.mbd.pub/api/order-list?page=1&limit=20
```
Returns: count, previous_page, next_page, orders[]

#### Get Product List
```
GET https://x.mbd.pub/api/product-list?page=1&limit=20
Body (optional JSON): {"states": [1,4,5,9]}
```
States: 1=上架, 4=下架, 5=未审核, 9=草稿

#### Get Product Detail
```
GET https://x.mbd.pub/api/product-detail?urlkey=<urlkey>
```
Returns: producttype (1=单品, 3=全家桶), productname, productimage, productprice, publishtime, productstates, productdetail, productcontent, urlkey, contains, contain_num, buckcet_price, producturl

#### Get Product Stats (2 months)
```
GET https://x.mbd.pub/api/product-chart?urlkey=<urlkey>
```
Returns: view_data{date: count}, sold_data{date: count}

#### Get Unread Notifications
```
GET https://x.mbd.pub/api/unread-mentions
Body (optional JSON): {"types": [1,2,3]}
```
Types: 1=点赞, 2=评论, 3=购买, 4=关注, 5=系统, 6=新作品, 7=回复, 8=打赏, 9=已购更新

#### Get Push Settings
```
GET https://x.mbd.pub/api/message-settings
```
Returns: type {2: "都推"} — 0=不推, 1=只推售出, 2=都推

---

### WRITE Endpoints

#### Create Draft
```
POST https://x.mbd.pub/api/drafts/
Content-Type: application/json
Body: {
  "productname": "string",     // required
  "producttype": 1,            // required: 1=单品, 3=全家桶
  "productdetail": "string",   // required: public description
  "productimage": "url",       // required: cover image URL
  "productprice": 1.0,         // optional, default 1
  "productcontent": "string",  // optional: paid content (图文)
  "category": 0,               // required: see categories below
  "opendata": 0,               // optional: 1=public sales data
  "sale_limit": -1,            // optional: -1=unlimited
  "buyer_comment": 0           // optional: 1=buyers only
}
```
Returns: draft object with id, urlkey, productid

Categories: 0=未分类, 1=学习, 2=绘画, 3=素材, 4=科技, 5=生活, 6=播客, 7=资料, 8=写作, 9=其它, 10=私密, 11=受限制, 12=视频, 13=手账, 14=游戏

#### Publish Draft
```
POST https://x.mbd.pub/api/drafts/publish/
Content-Type: application/json
Body: {"productid": <int>}
```
Returns: product URL

#### Update Draft
```
PATCH https://x.mbd.pub/api/drafts/
Content-Type: application/json
Body: {"productid": <int>, "productname": "...", ...}
```
Updatable fields: productname, productprice, productimage, productsize, publishtime, productdetail, productcontent, noshow, category, opendata, sale_limit, buyer_comment

#### Create Discount Coupon
```
POST https://x.mbd.pub/api/create-discount?urlkey=<urlkey>
Body: {"rate": 0.8}   // 0-1, one decimal place
```
Returns: urlkey, rate, code (coupon code), created_time

#### Bundle Management
```
GET  https://x.mbd.pub/api/users/buckets_list/          # list all bundles
POST https://x.mbd.pub/api/products/{id}/add_in_bucket/ # add to bundle
     Body: {"bucketid": <int>}
DELETE https://x.mbd.pub/api/products/{id}/rm_out_bucket/ # remove from bundle
     Body: {"bucketid": <int>}
```

#### Update User Profile
```
PATCH https://x.mbd.pub/api/set-user-info
Body: {"brief": "intro text"}  // max 90 chars
Body: {"name": "nickname"}     // max 20 chars
Body: {"post_setting": 2}      // 0=off, 1=sales only, 2=all
```

---

### Webhook / Callback

Set callback URL at: https://mbd.pub/o/config/developer
Requires: 闪电结算 (Lightning Settlement) enabled

POST payload on purchase:
```json
{
  "order_id": "3faa1cfd...",
  "out_order_id": "12345678",   // null if not set
  "product_name": "作品名",
  "product_url_key": "urlkey",
  "amount": 9.9,
  "state": 1                    // 1=success
}
```

Custom order ID: append `?out_order_id=<your_id>` to product purchase URL.

---

## Usage Examples

```bash
MBD_TOKEN="your-developer-key"

# List all products
curl -s -H "x-token: $MBD_TOKEN" "https://x.mbd.pub/api/product-list" | python3 -m json.tool

# Get recent orders
curl -s -H "x-token: $MBD_TOKEN" "https://x.mbd.pub/api/order-list?limit=10&page=1" | python3 -m json.tool

# Get unread notifications (purchases only)
curl -s -H "x-token: $MBD_TOKEN" -X GET \
  -H "Content-Type: application/json" \
  -d '{"types":[3]}' \
  "https://x.mbd.pub/api/unread-mentions" | python3 -m json.tool

# Check product stats
curl -s -H "x-token: $MBD_TOKEN" "https://x.mbd.pub/api/product-chart?urlkey=Z5mamQ==" | python3 -m json.tool
```

## Python Helper

```python
import requests

class MbDClient:
    BASE = "https://x.mbd.pub/api"
    
    def __init__(self, token: str):
        self.headers = {"x-token": token, "Content-Type": "application/json"}
    
    def get(self, path: str, params: dict = None):
        r = requests.get(f"{self.BASE}{path}", headers=self.headers, params=params)
        return r.json()
    
    def post(self, path: str, data: dict = None, params: dict = None):
        r = requests.post(f"{self.BASE}{path}", headers=self.headers, json=data, params=params)
        return r.json()
    
    # Convenience methods
    def products(self, states=None, page=1, limit=20):
        body = {"states": states} if states else None
        return self.get("/product-list", params={"page": page, "limit": limit})
    
    def orders(self, page=1, limit=20):
        return self.get("/order-list", params={"page": page, "limit": limit})
    
    def order(self, order_id=None, out_order_id=None):
        params = {}
        if order_id: params["order_id"] = order_id
        if out_order_id: params["out_order_id"] = out_order_id
        return self.get("/order-detail", params=params)
    
    def notifications(self, types=None):
        data = {"types": types} if types else None
        r = requests.get(f"{self.BASE}/unread-mentions", headers=self.headers, json=data)
        return r.json()
    
    def stats(self, urlkey: str):
        return self.get("/product-chart", params={"urlkey": urlkey})
    
    def create_coupon(self, urlkey: str, rate: float):
        return self.post("/create-discount", data={"rate": rate}, params={"urlkey": urlkey})
```
