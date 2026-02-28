"""
MbD (面包多) CLI
Full command-line interface for interacting with mbd.pub.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from mbd_client import MbDClient, MbDError

console = Console()


def _client(token: Optional[str] = None) -> MbDClient:
    try:
        return MbDClient(token=token)
    except MbDError as e:
        console.print(f"[red]❌ {e.message}[/red]")
        raise SystemExit(1)


def _fmt_date(s: Optional[str]) -> str:
    if not s:
        return "-"
    try:
        dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(s)


def _fmt_price(v) -> str:
    if v is None:
        return "-"
    try:
        return f"¥{float(v):.2f}"
    except Exception:
        return str(v)


STATE_LABELS = {1: "上架", 4: "下架", 5: "未审核", 9: "草稿"}
TYPE_LABELS = {1: "单品", 3: "全家桶"}
NOTIFY_LABELS = {1: "点赞", 2: "评论", 3: "购买", 4: "关注", 5: "系统", 6: "新作品", 7: "回复", 8: "打赏", 9: "已购更新"}
PUSH_LABELS = {0: "不推", 1: "只推售出", 2: "都推"}


# ─────────────────────────────────────────────────────────────────────────────

@click.group()
@click.option("--token", envvar="MBD_TOKEN", default=None, help="MbD 开发者密钥")
@click.pass_context
def cli(ctx, token):
    """面包多 (mbd.pub) 命令行工具"""
    ctx.ensure_object(dict)
    ctx.obj["token"] = token


# ── 商品 ──────────────────────────────────────────────────────────────────────

@cli.group()
def products():
    """商品管理"""


@products.command("list")
@click.option("--state", default="全部",
              type=click.Choice(["上架", "下架", "草稿", "全部"]),
              help="筛选状态")
@click.option("--page", default=1, show_default=True, help="页码")
@click.option("--limit", default=20, show_default=True, help="每页数量")
@click.pass_context
def products_list(ctx, state, page, limit):
    """列出商品"""
    c = _client(ctx.obj["token"])
    state_map = {"上架": [1], "下架": [4], "草稿": [9], "全部": None}
    states = state_map[state]
    try:
        data = c.get_product_list(states=states, page=page, limit=limit)
    except MbDError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)

    items = data if isinstance(data, list) else data.get("products") or data.get("results") or []
    if not items:
        console.print("[yellow]暂无商品[/yellow]")
        return

    t = Table(title=f"商品列表（第{page}页）", show_lines=True)
    t.add_column("商品名称", style="cyan", no_wrap=False)
    t.add_column("urlkey", style="dim")
    t.add_column("类型")
    t.add_column("价格", justify="right")
    t.add_column("状态")
    t.add_column("发布时间")

    for p in items:
        t.add_row(
            str(p.get("productname", "-")),
            str(p.get("urlkey", "-")),
            TYPE_LABELS.get(p.get("producttype"), str(p.get("producttype", "-"))),
            _fmt_price(p.get("productprice")),
            STATE_LABELS.get(p.get("productstates"), str(p.get("productstates", "-"))),
            _fmt_date(p.get("publishtime")),
        )
    console.print(t)


@products.command("detail")
@click.argument("urlkey")
@click.pass_context
def products_detail(ctx, urlkey):
    """查看商品详情"""
    c = _client(ctx.obj["token"])
    try:
        p = c.get_product_detail(urlkey)
    except MbDError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)

    t = Table(title="商品详情", show_header=False, show_lines=True)
    t.add_column("字段", style="bold cyan")
    t.add_column("内容")
    rows = [
        ("商品名称", p.get("productname")),
        ("urlkey", p.get("urlkey")),
        ("类型", TYPE_LABELS.get(p.get("producttype"), str(p.get("producttype")))),
        ("价格", _fmt_price(p.get("productprice"))),
        ("状态", STATE_LABELS.get(p.get("productstates"), str(p.get("productstates")))),
        ("分类", str(p.get("category", "-"))),
        ("发布时间", _fmt_date(p.get("publishtime"))),
        ("封面图", str(p.get("productimage") or "-")),
        ("商品链接", str(p.get("producturl") or "-")),
        ("简介", str(p.get("productdetail") or "-")),
        ("付费内容", str(p.get("productcontent") or "-")),
        ("全家桶数量", str(p.get("contain_num") or "-")),
    ]
    for k, v in rows:
        t.add_row(k, str(v) if v is not None else "-")
    console.print(t)


@products.command("stats")
@click.argument("urlkey")
@click.pass_context
def products_stats(ctx, urlkey):
    """查看商品统计（近2个月）"""
    c = _client(ctx.obj["token"])
    try:
        data = c.get_product_stats(urlkey)
    except MbDError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)

    view_data = data.get("view_data") or {}
    sold_data = data.get("sold_data") or {}

    t = Table(title=f"商品统计 ({urlkey})", show_lines=True)
    t.add_column("日期", style="cyan")
    t.add_column("浏览量", justify="right")
    t.add_column("销量", justify="right")

    all_dates = sorted(set(list(view_data.keys()) + list(sold_data.keys())))
    for d in all_dates:
        t.add_row(d, str(view_data.get(d, 0)), str(sold_data.get(d, 0)))
    if not all_dates:
        console.print("[yellow]暂无统计数据[/yellow]")
        return
    console.print(t)


@products.command("create")
@click.option("--name", required=True, help="商品名称")
@click.option("--detail", "detail", required=True, help="商品简介（公开）")
@click.option("--price", required=True, type=float, help="价格（元）")
@click.option("--category", required=True,
              type=click.Choice(["未分类", "学习", "绘画", "素材", "科技", "生活",
                                  "播客", "资料", "写作", "其它", "私密", "受限制",
                                  "视频", "手账", "游戏"]),
              help="分类")
@click.option("--content", default="", help="付费内容")
@click.option("--image-url", default="", help="封面图 URL")
@click.pass_context
def products_create(ctx, name, detail, price, category, content, image_url):
    """创建商品草稿"""
    c = _client(ctx.obj["token"])
    cat_map = {k: v for v, k in enumerate(
        ["未分类", "学习", "绘画", "素材", "科技", "生活", "播客", "资料", "写作", "其它", "私密", "受限制", "视频", "手账", "游戏"]
    )}
    try:
        result = c.create_draft(
            productname=name,
            productdetail=detail,
            productprice=price,
            category=cat_map[category],
            productcontent=content,
            productimage=image_url,
        )
    except MbDError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)

    console.print(f"[green]✅ 草稿创建成功[/green]")
    console.print(f"  商品ID: [bold]{result.get('productid') or result.get('id')}[/bold]")
    console.print(f"  urlkey: [bold]{result.get('urlkey')}[/bold]")


@products.command("publish")
@click.argument("productid", type=int)
@click.pass_context
def products_publish(ctx, productid):
    """发布商品草稿"""
    c = _client(ctx.obj["token"])
    try:
        result = c.publish_draft(productid)
    except MbDError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)
    console.print(f"[green]✅ 商品发布成功[/green]")
    if isinstance(result, dict):
        url = result.get("url") or result.get("producturl") or result.get("product_url")
        if url:
            console.print(f"  商品链接: {url}")


@products.command("update")
@click.argument("productid", type=int)
@click.option("--name", default=None, help="商品名称")
@click.option("--price", default=None, type=float, help="价格")
@click.option("--detail", default=None, help="商品简介")
@click.option("--content", default=None, help="付费内容")
@click.option("--image-url", default=None, help="封面图 URL")
@click.option("--category", default=None,
              type=click.Choice(["未分类", "学习", "绘画", "素材", "科技", "生活",
                                  "播客", "资料", "写作", "其它", "私密", "受限制",
                                  "视频", "手账", "游戏"]),
              help="分类")
@click.pass_context
def products_update(ctx, productid, name, price, detail, content, image_url, category):
    """更新商品草稿"""
    c = _client(ctx.obj["token"])
    cat_map = {k: v for v, k in enumerate(
        ["未分类", "学习", "绘画", "素材", "科技", "生活", "播客", "资料", "写作", "其它", "私密", "受限制", "视频", "手账", "游戏"]
    )}
    kwargs = {}
    if name is not None:
        kwargs["productname"] = name
    if price is not None:
        kwargs["productprice"] = price
    if detail is not None:
        kwargs["productdetail"] = detail
    if content is not None:
        kwargs["productcontent"] = content
    if image_url is not None:
        kwargs["productimage"] = image_url
    if category is not None:
        kwargs["category"] = cat_map[category]

    if not kwargs:
        console.print("[yellow]⚠️  未提供任何更新字段[/yellow]")
        return

    try:
        c.update_draft(productid, **kwargs)
    except MbDError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)
    console.print(f"[green]✅ 商品 {productid} 更新成功[/green]")


# ── 订单 ──────────────────────────────────────────────────────────────────────

@cli.group()
def orders():
    """订单管理"""


@orders.command("list")
@click.option("--page", default=1, show_default=True, help="页码")
@click.option("--limit", default=20, show_default=True, help="每页数量")
@click.pass_context
def orders_list(ctx, page, limit):
    """列出订单"""
    c = _client(ctx.obj["token"])
    try:
        data = c.get_order_list(page=page, limit=limit)
    except MbDError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)

    items = data.get("orders") or (data if isinstance(data, list) else [])
    total = data.get("count", len(items)) if isinstance(data, dict) else len(items)

    if not items:
        console.print("[yellow]暂无订单[/yellow]")
        return

    t = Table(title=f"订单列表（共{total}笔，第{page}页）", show_lines=True)
    t.add_column("订单ID", style="dim")
    t.add_column("商品", style="cyan")
    t.add_column("金额", justify="right")
    t.add_column("支付方式")
    t.add_column("状态")
    t.add_column("下单时间")

    state_labels = {"success": "成功", "cancel": "取消", "invalid": "无效"}
    for o in items:
        t.add_row(
            str(o.get("order_id") or o.get("id") or "-"),
            str(o.get("urlkey") or o.get("product_url_key") or "-"),
            _fmt_price(o.get("orderamount") or o.get("amount")),
            str(o.get("payway") or "-"),
            state_labels.get(o.get("state"), str(o.get("state", "-"))),
            _fmt_date(o.get("ordertime")),
        )
    console.print(t)


@orders.command("detail")
@click.argument("order_id")
@click.pass_context
def orders_detail(ctx, order_id):
    """查看订单详情"""
    c = _client(ctx.obj["token"])
    try:
        o = c.get_order_detail(order_id=order_id)
    except MbDError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)

    state_labels = {"success": "成功", "cancel": "取消", "invalid": "无效"}
    t = Table(title="订单详情", show_header=False, show_lines=True)
    t.add_column("字段", style="bold cyan")
    t.add_column("内容")
    rows = [
        ("订单ID", o.get("order_id")),
        ("自定义ID", o.get("out_order_id")),
        ("商品urlkey", o.get("urlkey")),
        ("金额", _fmt_price(o.get("orderamount"))),
        ("支付方式", o.get("payway")),
        ("状态", state_labels.get(o.get("state"), str(o.get("state")))),
        ("下单时间", _fmt_date(o.get("ordertime"))),
        ("到期时间", _fmt_date(o.get("expire_at"))),
        ("续费轮次", str(o.get("rounds") or "-")),
    ]
    for k, v in rows:
        t.add_row(k, str(v) if v is not None else "-")
    console.print(t)


# ── 通知 ──────────────────────────────────────────────────────────────────────

@cli.command("notifications")
@click.option("--type", "notify_type", default="全部",
              type=click.Choice(["购买", "评论", "点赞", "全部"]),
              help="通知类型")
@click.pass_context
def notifications(ctx, notify_type):
    """查看未读通知"""
    c = _client(ctx.obj["token"])
    type_map = {"购买": [3], "评论": [2], "点赞": [1], "全部": None}
    types = type_map[notify_type]
    try:
        data = c.get_notifications(types=types)
    except MbDError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)

    items = data if isinstance(data, list) else data.get("mentions") or data.get("results") or []
    if not items:
        console.print("[green]✅ 暂无未读通知[/green]")
        return

    t = Table(title=f"未读通知（{notify_type}）", show_lines=True)
    t.add_column("类型")
    t.add_column("内容", style="cyan", no_wrap=False)
    t.add_column("来源")
    t.add_column("时间")

    for n in items:
        t.add_row(
            NOTIFY_LABELS.get(n.get("type"), str(n.get("type", "-"))),
            str(n.get("content") or n.get("message") or "-"),
            str(n.get("from_user") or n.get("source") or "-"),
            _fmt_date(n.get("created_at") or n.get("time")),
        )
    console.print(t)


# ── 优惠券 ────────────────────────────────────────────────────────────────────

@cli.group()
def coupon():
    """优惠券管理"""


@coupon.command("create")
@click.argument("urlkey")
@click.option("--rate", required=True, type=float, help="折扣率（0-1，如0.8表示八折）")
@click.pass_context
def coupon_create(ctx, urlkey, rate):
    """创建折扣优惠券"""
    if not 0 < rate <= 1:
        console.print("[red]❌ 折扣率必须在 0-1 之间[/red]")
        raise SystemExit(1)
    c = _client(ctx.obj["token"])
    try:
        result = c.create_coupon(urlkey=urlkey, rate=rate)
    except MbDError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)

    t = Table(title="优惠券创建成功", show_header=False, show_lines=True)
    t.add_column("字段", style="bold cyan")
    t.add_column("内容")
    t.add_row("urlkey", str(result.get("urlkey", "-")))
    t.add_row("折扣率", f"{result.get('rate', rate) * 100:.0f}折")
    t.add_row("优惠码", str(result.get("code", "-")))
    t.add_row("创建时间", _fmt_date(result.get("created_time")))
    console.print(t)


# ── 全家桶 ────────────────────────────────────────────────────────────────────

@cli.group()
def bundle():
    """全家桶管理"""


@bundle.command("list")
@click.pass_context
def bundle_list(ctx):
    """列出全家桶"""
    c = _client(ctx.obj["token"])
    try:
        data = c.get_bundle_list()
    except MbDError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)

    items = data if isinstance(data, list) else data.get("buckets") or data.get("results") or []
    if not items:
        console.print("[yellow]暂无全家桶[/yellow]")
        return

    t = Table(title="全家桶列表", show_lines=True)
    t.add_column("ID", style="dim")
    t.add_column("名称", style="cyan")
    t.add_column("价格", justify="right")
    t.add_column("商品数")
    t.add_column("创建时间")
    for b in items:
        t.add_row(
            str(b.get("id") or b.get("bucketid") or "-"),
            str(b.get("name") or b.get("productname") or "-"),
            _fmt_price(b.get("price") or b.get("buckcet_price")),
            str(b.get("contain_num") or "-"),
            _fmt_date(b.get("created_at") or b.get("publishtime")),
        )
    console.print(t)


@bundle.command("add")
@click.argument("product_id", type=int)
@click.option("--bucket", "bucket_id", required=True, type=int, help="全家桶 ID")
@click.pass_context
def bundle_add(ctx, product_id, bucket_id):
    """添加商品到全家桶"""
    c = _client(ctx.obj["token"])
    try:
        c.add_to_bundle(product_id=product_id, bucket_id=bucket_id)
    except MbDError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)
    console.print(f"[green]✅ 商品 {product_id} 已添加到全家桶 {bucket_id}[/green]")


@bundle.command("remove")
@click.argument("product_id", type=int)
@click.option("--bucket", "bucket_id", required=True, type=int, help="全家桶 ID")
@click.pass_context
def bundle_remove(ctx, product_id, bucket_id):
    """从全家桶移除商品"""
    c = _client(ctx.obj["token"])
    try:
        c.remove_from_bundle(product_id=product_id, bucket_id=bucket_id)
    except MbDError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)
    console.print(f"[green]✅ 商品 {product_id} 已从全家桶 {bucket_id} 移除[/green]")


# ── 用户资料 ──────────────────────────────────────────────────────────────────

@cli.group()
def profile():
    """个人资料管理"""


@profile.command("set-bio")
@click.argument("brief")
@click.pass_context
def profile_set_bio(ctx, brief):
    """设置个人简介（最多90字）"""
    c = _client(ctx.obj["token"])
    try:
        c.set_bio(brief)
    except MbDError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)
    console.print(f"[green]✅ 简介已更新（{len(brief)}字）[/green]")


@profile.command("set-name")
@click.argument("name")
@click.pass_context
def profile_set_name(ctx, name):
    """设置昵称（最多20字）"""
    c = _client(ctx.obj["token"])
    try:
        c.set_name(name)
    except MbDError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)
    console.print(f"[green]✅ 昵称已更新为：{name}[/green]")


@profile.command("push-settings")
@click.argument("setting", type=click.Choice(["不推", "售出", "全部"]))
@click.pass_context
def profile_push_settings(ctx, setting):
    """设置推送通知（不推/售出/全部）"""
    c = _client(ctx.obj["token"])
    setting_map = {"不推": 0, "售出": 1, "全部": 2}
    try:
        c.set_push_settings(setting_map[setting])
    except MbDError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)
    console.print(f"[green]✅ 推送设置已更新为：{setting}[/green]")


if __name__ == "__main__":
    cli()
