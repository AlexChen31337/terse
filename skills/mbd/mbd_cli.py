"""
面包多 CLI — 命令行管理工具
~~~~~~~~~~~~~~~~~~~~~~~~~

用法: uv run python mbd_cli.py [命令] [子命令] [选项]
"""

from __future__ import annotations

import sys

import click
from tabulate import tabulate

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
)


def _get_client(ctx: click.Context) -> MbDClient:
    return ctx.obj["client"]


def _print_table(rows: list[list], headers: list[str]) -> None:
    click.echo(tabulate(rows, headers=headers, tablefmt="simple"))


def _error(msg: str) -> None:
    click.echo(f"❌ 错误: {msg}", err=True)
    sys.exit(1)


@click.group()
@click.option("--token", envvar="MBD_TOKEN", default=None, help="面包多 API token")
@click.pass_context
def cli(ctx: click.Context, token: str | None) -> None:
    """面包多 (mbd.pub) 命令行管理工具 🍞"""
    ctx.ensure_object(dict)
    try:
        ctx.obj["client"] = MbDClient(token=token)
    except MbDError as exc:
        _error(str(exc))


# ── 产品命令组 ────────────────────────────────────────────

@cli.group()
def products() -> None:
    """产品管理 📦"""


@products.command("list")
@click.option("--state", type=click.Choice(["上架", "下架", "草稿", "全部"]), default="全部", help="产品状态过滤")
@click.option("--page", default=1, type=int, help="页码")
@click.option("--limit", default=20, type=int, help="每页数量")
@click.pass_context
def products_list(ctx: click.Context, state: str, page: int, limit: int) -> None:
    """列出产品"""
    client = _get_client(ctx)
    states = STATE_NAME_TO_ID.get(state)
    try:
        data = client.product_list(states=states, page=page, limit=limit)
    except MbDError as exc:
        _error(str(exc))
    products_data = data.get("products", data.get("results", []))
    if not products_data:
        click.echo("📭 暂无产品")
        return
    rows = []
    for p in products_data:
        rows.append([
            p.get("urlkey", "—"),
            p.get("productname", "—"),
            PRODUCT_TYPES.get(p.get("producttype"), "—"),
            f"¥{p.get('productprice', 0):.2f}",
            PRODUCT_STATES.get(p.get("productstates", 0), "—"),
            format_datetime(p.get("publishtime")),
        ])
    _print_table(rows, ["URL Key", "名称", "类型", "价格", "状态", "发布时间"])
    count = data.get("count", len(products_data))
    click.echo(f"\n共 {count} 件产品")


@products.command("detail")
@click.argument("urlkey")
@click.pass_context
def products_detail(ctx: click.Context, urlkey: str) -> None:
    """查看产品详情"""
    client = _get_client(ctx)
    try:
        p = client.product_detail(urlkey)
    except MbDError as exc:
        _error(str(exc))
    rows = [
        ["名称", p.get("productname", "—")],
        ["类型", PRODUCT_TYPES.get(p.get("producttype"), "—")],
        ["价格", f"¥{p.get('productprice', 0):.2f}"],
        ["状态", PRODUCT_STATES.get(p.get("productstates", 0), "—")],
        ["分类", CATEGORIES.get(p.get("category", 0), "—")],
        ["URL Key", p.get("urlkey", "—")],
        ["产品链接", p.get("producturl", "—")],
        ["发布时间", format_datetime(p.get("publishtime"))],
        ["封面图", p.get("productimage", "—")],
        ["描述", (p.get("productdetail", "—") or "—")[:100]],
    ]
    if p.get("producttype") == 3:
        rows.append(["包含数量", p.get("contain_num", "—")])
        bp = p.get("buckcet_price", 0)
        rows.append(["全家桶价格", f"¥{bp:.2f}"])
    _print_table(rows, ["字段", "值"])


@products.command("stats")
@click.argument("urlkey")
@click.pass_context
def products_stats(ctx: click.Context, urlkey: str) -> None:
    """查看产品统计 (近两月浏览/销量)"""
    client = _get_client(ctx)
    try:
        data = client.product_stats(urlkey)
    except MbDError as exc:
        _error(str(exc))
    view_data = data.get("view_data", {})
    sold_data = data.get("sold_data", {})
    if not view_data and not sold_data:
        click.echo("📊 暂无统计数据")
        return
    all_dates = sorted(set(list(view_data.keys()) + list(sold_data.keys())))
    rows = []
    for date in all_dates:
        views = view_data.get(date, 0)
        sales = sold_data.get(date, 0)
        bar = "█" * min(views, 50)
        rows.append([date, views, sales, bar])
    _print_table(rows, ["日期", "浏览", "销量", "浏览趋势"])
    total_views = sum(view_data.values())
    total_sales = sum(sold_data.values())
    click.echo(f"\n📈 总浏览: {total_views}  |  💰 总销量: {total_sales}")


@products.command("create")
@click.option("--name", required=True, help="产品名称")
@click.option("--detail", required=True, help="公开描述")
@click.option("--price", required=True, type=float, help="价格 (元)")
@click.option("--category", required=True, help="分类名称 (科技/学习/写作/...)")
@click.option("--content", default=None, help="付费内容 (图文)")
@click.option("--image-url", default="https://mbd.pub/default-cover.png", help="封面图 URL")
@click.option("--type", "ptype", type=click.Choice(["单品", "全家桶"]), default="单品", help="产品类型")
@click.pass_context
def products_create(ctx: click.Context, name: str, detail: str, price: float,
                    category: str, content: str | None, image_url: str, ptype: str) -> None:
    """创建新产品 (草稿)"""
    client = _get_client(ctx)
    cat_id = CATEGORY_NAME_TO_ID.get(category)
    if cat_id is None:
        cats = ", ".join(CATEGORY_NAME_TO_ID.keys())
        _error(f"未知分类: {category}。可选: {cats}")
    product_type = 1 if ptype == "单品" else 3
    try:
        result = client.create_draft(
            productname=name, productdetail=detail, productimage=image_url,
            producttype=product_type, productprice=price, productcontent=content, category=cat_id,
        )
    except MbDError as exc:
        _error(str(exc))
    pid = result.get("productid", result.get("id", "—"))
    uk = result.get("urlkey", "—")
    click.echo("✅ 草稿已创建:")
    click.echo(f"  产品 ID: {pid}")
    click.echo(f"  URL Key: {uk}")
    click.echo("  ⚠️  草稿需要发布后才能访问。")


@products.command("publish")
@click.argument("productid", type=int)
@click.pass_context
def products_publish(ctx: click.Context, productid: int) -> None:
    """发布草稿"""
    client = _get_client(ctx)
    try:
        result = client.publish_draft(productid)
    except MbDError as exc:
        _error(str(exc))
    url = result.get("producturl", result)
    click.echo(f"🚀 产品已发布! URL: {url}")


@products.command("update")
@click.argument("productid", type=int)
@click.option("--name", default=None, help="新名称")
@click.option("--price", default=None, type=float, help="新价格")
@click.option("--detail", default=None, help="新描述")
@click.option("--content", default=None, help="新付费内容")
@click.option("--category", default=None, help="新分类名称")
@click.option("--image-url", default=None, help="新封面图 URL")
@click.pass_context
def products_update(ctx: click.Context, productid: int, name: str | None, price: float | None,
                    detail: str | None, content: str | None, category: str | None, image_url: str | None) -> None:
    """更新产品信息"""
    client = _get_client(ctx)
    fields: dict = {}
    if name is not None:
        fields["productname"] = name
    if price is not None:
        fields["productprice"] = price
    if detail is not None:
        fields["productdetail"] = detail
    if content is not None:
        fields["productcontent"] = content
    if image_url is not None:
        fields["productimage"] = image_url
    if category is not None:
        cat_id = CATEGORY_NAME_TO_ID.get(category)
        if cat_id is None:
            _error(f"未知分类: {category}")
        fields["category"] = cat_id
    if not fields:
        _error("请至少指定一个要更新的字段")
    try:
        client.update_draft(productid, **fields)
    except MbDError as exc:
        _error(str(exc))
    click.echo(f"✅ 产品 {productid} 已更新")


# ── 订单命令组 ────────────────────────────────────────────

@cli.group()
def orders() -> None:
    """订单管理 🧾"""


@orders.command("list")
@click.option("--page", default=1, type=int, help="页码")
@click.option("--limit", default=20, type=int, help="每页数量")
@click.pass_context
def orders_list(ctx: click.Context, page: int, limit: int) -> None:
    """列出订单"""
    client = _get_client(ctx)
    try:
        data = client.order_list(page=page, limit=limit)
    except MbDError as exc:
        _error(str(exc))
    order_list_data = data.get("orders", data.get("results", []))
    if not order_list_data:
        click.echo("📭 暂无订单")
        return
    rows = []
    for o in order_list_data:
        oid = o.get("order_id", "—")
        truncated_oid = oid[:12] + "…" if len(oid) > 12 else oid
        rows.append([
            truncated_oid,
            f"¥{o.get('orderamount', 0):.2f}",
            PAY_WAYS.get(o.get("payway", ""), o.get("payway", "—")),
            ORDER_STATES.get(o.get("state", ""), o.get("state", "—")),
            format_datetime(o.get("ordertime")),
        ])
    _print_table(rows, ["订单 ID", "金额", "支付方式", "状态", "下单时间"])
    count = data.get("count", len(order_list_data))
    click.echo(f"\n共 {count} 笔订单")


@orders.command("detail")
@click.argument("order_id")
@click.pass_context
def orders_detail(ctx: click.Context, order_id: str) -> None:
    """查看订单详情"""
    client = _get_client(ctx)
    try:
        o = client.order_detail(order_id=order_id)
    except MbDError as exc:
        _error(str(exc))
    rows = [
        ["订单 ID", o.get("order_id", "—")],
        ["金额", f"¥{o.get('orderamount', 0):.2f}"],
        ["支付方式", PAY_WAYS.get(o.get("payway", ""), o.get("payway", "—"))],
        ["状态", ORDER_STATES.get(o.get("state", ""), o.get("state", "—"))],
        ["下单时间", format_datetime(o.get("ordertime"))],
        ["产品 Key", o.get("urlkey", "—")],
        ["过期时间", format_datetime(o.get("expire_at"))],
    ]
    _print_table(rows, ["字段", "值"])


# ── 通知 ──────────────────────────────────────────────

@cli.command("notifications")
@click.option("--type", "ntype", type=click.Choice(["购买", "评论", "点赞", "全部"]), default="全部", help="通知类型")
@click.pass_context
def notifications_cmd(ctx: click.Context, ntype: str) -> None:
    """查看未读通知 🔔"""
    client = _get_client(ctx)
    types = NOTIFICATION_NAME_TO_ID.get(ntype)
    try:
        data = client.notifications(types=types)
    except MbDError as exc:
        _error(str(exc))
    items = data if isinstance(data, list) else data.get("mentions", data.get("results", []))
    if not items:
        click.echo("🔕 暂无未读通知")
        return
    rows = []
    for n in items:
        ntype_id = n.get("type", 0)
        type_label = NOTIFICATION_TYPES.get(ntype_id, f"类型{ntype_id}")
        content_text = n.get("content", n.get("message", "—"))[:50]
        time_str = format_datetime(n.get("created_time", n.get("time")))
        rows.append([type_label, content_text, time_str])
    _print_table(rows, ["类型", "内容", "时间"])


# ── 优惠券 ────────────────────────────────────────────

@cli.group()
def coupon() -> None:
    """优惠券管理 🎫"""


@coupon.command("create")
@click.argument("urlkey")
@click.option("--rate", required=True, type=float, help="折扣率 (0-1)，如 0.8 表示八折")
@click.pass_context
def coupon_create(ctx: click.Context, urlkey: str, rate: float) -> None:
    """创建优惠券"""
    client = _get_client(ctx)
    try:
        result = client.create_coupon(urlkey, rate)
    except MbDError as exc:
        _error(str(exc))
    r_val = result.get("rate", rate)
    code = result.get("code", "—")
    ctime = format_datetime(result.get("created_time"))
    discount = int(rate * 10)
    click.echo("🎫 优惠券已创建:")
    click.echo(f"  折扣率: {r_val} ({discount}折)")
    click.echo(f"  优惠码: {code}")
    click.echo(f"  创建时间: {ctime}")


# ── 全家桶 ────────────────────────────────────────────

@cli.group()
def bundle() -> None:
    """全家桶管理 🪣"""


@bundle.command("list")
@click.pass_context
def bundle_list(ctx: click.Context) -> None:
    """列出全家桶"""
    client = _get_client(ctx)
    try:
        data = client.bundle_list()
    except MbDError as exc:
        _error(str(exc))
    buckets = data if isinstance(data, list) else data.get("buckets", data.get("results", []))
    if not buckets:
        click.echo("📭 暂无全家桶")
        return
    rows = []
    for b in buckets:
        bp = b.get("price", b.get("buckcet_price", 0))
        rows.append([
            b.get("id", "—"),
            b.get("name", b.get("productname", "—")),
            b.get("contain_num", b.get("count", "—")),
            f"¥{bp:.2f}",
        ])
    _print_table(rows, ["ID", "名称", "包含数量", "价格"])


@bundle.command("add")
@click.argument("product_id", type=int)
@click.option("--bucket", required=True, type=int, help="全家桶 ID")
@click.pass_context
def bundle_add(ctx: click.Context, product_id: int, bucket: int) -> None:
    """将产品加入全家桶"""
    client = _get_client(ctx)
    try:
        client.bundle_add(product_id, bucket)
    except MbDError as exc:
        _error(str(exc))
    click.echo(f"✅ 产品 {product_id} 已加入全家桶 {bucket}")


@bundle.command("remove")
@click.argument("product_id", type=int)
@click.option("--bucket", required=True, type=int, help="全家桶 ID")
@click.pass_context
def bundle_remove(ctx: click.Context, product_id: int, bucket: int) -> None:
    """将产品从全家桶移除"""
    client = _get_client(ctx)
    try:
        client.bundle_remove(product_id, bucket)
    except MbDError as exc:
        _error(str(exc))
    click.echo(f"✅ 产品 {product_id} 已从全家桶 {bucket} 移除")


# ── 个人资料 ──────────────────────────────────────────

@cli.group()
def profile() -> None:
    """个人资料管理 👤"""


@profile.command("set-bio")
@click.argument("bio")
@click.pass_context
def profile_set_bio(ctx: click.Context, bio: str) -> None:
    """设置个人简介 (最多90字)"""
    client = _get_client(ctx)
    try:
        client.set_bio(bio)
    except MbDError as exc:
        _error(str(exc))
    click.echo(f"✅ 简介已更新: {bio}")


@profile.command("set-name")
@click.argument("name")
@click.pass_context
def profile_set_name(ctx: click.Context, name: str) -> None:
    """设置昵称 (最多20字)"""
    client = _get_client(ctx)
    try:
        client.set_name(name)
    except MbDError as exc:
        _error(str(exc))
    click.echo(f"✅ 昵称已更新: {name}")


@profile.command("push-settings")
@click.argument("setting", type=click.Choice(["不推", "售出", "全部"]), required=False)
@click.pass_context
def profile_push_settings(ctx: click.Context, setting: str | None) -> None:
    """查看或设置推送偏好"""
    client = _get_client(ctx)
    if setting is None:
        try:
            data = client.push_settings()
        except MbDError as exc:
            _error(str(exc))
        type_data = data.get("type", data)
        if isinstance(type_data, dict):
            for k, v in type_data.items():
                click.echo(f"📢 当前推送设置: {v} (ID: {k})")
        else:
            pname = PUSH_ID_TO_NAME.get(type_data, str(type_data))
            click.echo(f"📢 当前推送设置: {pname}")
    else:
        value = PUSH_SETTINGS[setting]
        try:
            client.set_push_settings(value)
        except MbDError as exc:
            _error(str(exc))
        click.echo(f"✅ 推送设置已更新为: {setting}")


if __name__ == "__main__":
    cli()
