#!/usr/bin/env python3
"""
All-Platform Article Digest Emailer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Aggregates published articles from all platforms and sends a nightly digest.

Platforms covered:
  - MbD (面包多) — paid Chinese content
  - Dev.to — English tech articles
  - Substack — English newsletter (scraped from backup repo)
  - HackerNews — submitted posts by AlexChen_31337

Usage:
    uv run python scripts/article_digest.py

Env:
    MBD_TOKEN       MbD API token (or auto-decrypted)
    SMTP_USER       Gmail address (default: alex.chen31337@gmail.com)
    SMTP_PASS       Gmail app password
    DIGEST_TO       Recipient email (default: bowen31337@outlook.com)
    DEVTO_API_KEY   Dev.to API key (or auto-decrypted)
"""

from __future__ import annotations

import json
import os
import smtplib
import subprocess
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import requests

# Add skill root to path
SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

from mbd_client import MbDClient, MbDError, format_datetime  # noqa: E402

# ── Config ──────────────────────────────────────────────
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER", "alex.chen31337@gmail.com")
SMTP_PASS = os.environ.get("SMTP_PASS", "itmkayyivszmbpaw")
DIGEST_TO = os.environ.get("DIGEST_TO", "bowen31337@outlook.com")

DEVTO_USER = "alexchen31337"
HN_USER = "AlexChen_31337"
SUBSTACK_BACKUP_REPO = Path.home() / ".openclaw/workspace/memory/substack-backup"

MBD_BASE_URL = "https://mbd.pub/o/book/"
DEVTO_API = "https://dev.to/api"
HN_API = "https://hacker-news.firebaseio.com/v0"
ALGOLIA_HN = "https://hn.algolia.com/api/v1"

MBD_CATEGORY_NAMES = {
    0: "未分类", 1: "文学", 2: "小说", 3: "漫画",
    4: "科技", 5: "财经", 6: "情感", 7: "历史",
    8: "写作", 9: "教育", 10: "生活",
}


# ── Helpers ─────────────────────────────────────────────

def _decrypt(key: str) -> str:
    res = subprocess.run(
        ["bash", str(Path.home() / ".openclaw/workspace/memory/decrypt.sh"), key],
        capture_output=True, text=True
    )
    val = res.stdout.strip()
    if not val or "ERROR" in val:
        return ""
    return val


def _get(url: str, headers: dict | None = None, params: dict | None = None,
         timeout: int = 15) -> Any:
    try:
        r = requests.get(url, headers=headers or {}, params=params, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[warn] GET {url}: {e}", file=sys.stderr)
    return None


# ── Platform fetchers ────────────────────────────────────

def fetch_mbd(token: str) -> list[dict]:
    articles = []
    try:
        client = MbDClient(token=token)
        page = 1
        while True:
            data = client.product_list(page=page, limit=20)
            items = data.get("results", data.get("products", []))
            if not items:
                break
            for item in items:
                urlkey = item.get("urlkey", "")
                articles.append({
                    "platform": "面包多",
                    "title": item.get("productname", "（无标题）"),
                    "url": f"{MBD_BASE_URL}{urlkey}" if urlkey else "—",
                    "published": format_datetime(item.get("publishtime")) if item.get("publishtime") else "—",
                    "tags": MBD_CATEGORY_NAMES.get(item.get("category", 0), "其他"),
                    "price": f"¥{item.get('productprice', 0)}",
                })
            if len(items) < 20:
                break
            page += 1
    except MbDError as e:
        print(f"[warn] MbD fetch error: {e}", file=sys.stderr)
    return articles


def fetch_devto(api_key: str) -> list[dict]:
    articles = []
    headers = {"api-key": api_key} if api_key else {}
    # Public articles by username (no auth needed)
    data = _get(f"{DEVTO_API}/articles", params={"username": DEVTO_USER, "per_page": 50})
    if not data:
        return articles
    for item in data:
        articles.append({
            "platform": "Dev.to",
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "published": item.get("published_at", "—")[:10] if item.get("published_at") else "—",
            "tags": ", ".join(item.get("tag_list", [])),
            "price": "Free",
        })
    return articles


def fetch_hn() -> list[dict]:
    articles = []
    # Use Algolia HN search API — fast and reliable
    data = _get(f"{ALGOLIA_HN}/search_by_date",
                params={"tags": f"author_{HN_USER},story", "hitsPerPage": 50})
    if not data:
        return articles
    for hit in data.get("hits", []):
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        articles.append({
            "platform": "HackerNews",
            "title": hit.get("title", ""),
            "url": url,
            "published": (hit.get("created_at") or "—")[:10],
            "tags": "Ask HN" if hit.get("title", "").startswith("Ask HN") else
                    "Show HN" if hit.get("title", "").startswith("Show HN") else "Post",
            "price": "Free",
        })
    return articles


def fetch_substack_from_backup() -> list[dict]:
    """Read articles from local substack backup git repo."""
    articles = []
    backup_dir = SUBSTACK_BACKUP_REPO
    if not backup_dir.exists():
        return articles
    for folder in sorted(backup_dir.iterdir(), reverse=True):
        meta_file = folder / "metadata.json"
        if not meta_file.exists():
            continue
        try:
            meta = json.loads(meta_file.read_text())
            articles.append({
                "platform": "Substack",
                "title": meta.get("title", folder.name),
                "url": meta.get("url", "—"),
                "published": meta.get("published_at", "—")[:10] if meta.get("published_at") else "—",
                "tags": ", ".join(meta.get("tags", [])),
                "price": "Free",
            })
        except Exception:
            pass
    return articles


# ── Email builder ────────────────────────────────────────

PLATFORM_COLORS = {
    "面包多": "#f59e0b",
    "Dev.to": "#3b49df",
    "HackerNews": "#ff6600",
    "Substack": "#ff681a",
}


def build_html(all_articles: list[dict]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(all_articles)

    # Group by platform for summary
    by_platform: dict[str, list] = {}
    for a in all_articles:
        by_platform.setdefault(a["platform"], []).append(a)

    summary_pills = " ".join(
        f'<span style="background:{PLATFORM_COLORS.get(p,"#6b7280")};color:#fff;'
        f'padding:3px 10px;border-radius:12px;font-size:12px;margin-right:6px">'
        f'{p} {len(arts)}</span>'
        for p, arts in by_platform.items()
    )

    rows = ""
    for i, a in enumerate(all_articles, 1):
        color = PLATFORM_COLORS.get(a["platform"], "#6b7280")
        badge = (f'<span style="background:{color};color:#fff;padding:2px 8px;'
                 f'border-radius:8px;font-size:11px">{a["platform"]}</span>')
        rows += f"""
        <tr style="background:{'#f9fafb' if i % 2 == 0 else '#ffffff'}">
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;color:#9ca3af">{i}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb">{badge}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb">
                <a href="{a['url']}" style="color:#2563eb;text-decoration:none;font-weight:500">{a['title']}</a>
                <div style="color:#9ca3af;font-size:11px;margin-top:2px">{a['tags']}</div>
            </td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;color:#059669;white-space:nowrap">{a['price']}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;color:#6b7280;font-size:12px;white-space:nowrap">{a['published']}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="zh">
<head><meta charset="utf-8"><title>文章日报</title></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f3f4f6;margin:0;padding:20px">
<div style="max-width:760px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.1)">
  <div style="background:#111827;padding:24px 32px">
    <h1 style="color:#fff;margin:0;font-size:20px">📰 内容发布日报</h1>
    <p style="color:#9ca3af;margin:8px 0 12px;font-size:14px">{now} | 共 {total} 篇已发布</p>
    <div>{summary_pills}</div>
  </div>
  <div style="padding:24px 32px">
    {"<p style='color:#6b7280'>暂无已发布文章。</p>" if not all_articles else f'''
    <table style="width:100%;border-collapse:collapse;font-size:14px">
      <thead>
        <tr style="background:#f9fafb">
          <th style="padding:8px 12px;text-align:left;color:#374151;border-bottom:2px solid #e5e7eb">#</th>
          <th style="padding:8px 12px;text-align:left;color:#374151;border-bottom:2px solid #e5e7eb">平台</th>
          <th style="padding:8px 12px;text-align:left;color:#374151;border-bottom:2px solid #e5e7eb">文章</th>
          <th style="padding:8px 12px;text-align:left;color:#374151;border-bottom:2px solid #e5e7eb">价格</th>
          <th style="padding:8px 12px;text-align:left;color:#374151;border-bottom:2px solid #e5e7eb">发布时间</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>'''}
  </div>
  <div style="padding:16px 32px;background:#f9fafb;border-top:1px solid #e5e7eb">
    <p style="color:#9ca3af;font-size:12px;margin:0">
      由 Alex Agent 自动聚合 · 平台：面包多 · Dev.to · HackerNews · Substack
    </p>
  </div>
</div>
</body>
</html>"""


def build_plain(all_articles: list[dict]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"内容发布日报 ({now})", f"共 {len(all_articles)} 篇已发布\n", "=" * 60]
    cur_platform = ""
    for a in all_articles:
        if a["platform"] != cur_platform:
            cur_platform = a["platform"]
            lines.append(f"\n[{cur_platform}]")
        lines.append(f"  • {a['title']}")
        lines.append(f"    {a['url']}")
        lines.append(f"    {a['price']} | {a['tags']} | {a['published']}")
    if not all_articles:
        lines.append("暂无已发布文章。")
    return "\n".join(lines)


def send_email(subject: str, html: str, plain: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Alex Agent <{SMTP_USER}>"
    msg["To"] = DIGEST_TO
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(SMTP_USER, [DIGEST_TO], msg.as_bytes())
    print(f"[ok] Email sent to {DIGEST_TO}")


def main() -> None:
    # Get tokens
    mbd_token = os.environ.get("MBD_TOKEN") or _decrypt("mbd-token")
    devto_api_key = os.environ.get("DEVTO_API_KEY") or _decrypt("devto-api-key")

    print("[*] Fetching MbD articles...")
    mbd = fetch_mbd(mbd_token) if mbd_token else []
    print(f"    {len(mbd)} articles")

    print("[*] Fetching Dev.to articles...")
    devto = fetch_devto(devto_api_key)
    print(f"    {len(devto)} articles")

    print("[*] Fetching HackerNews posts...")
    hn = fetch_hn()
    print(f"    {len(hn)} posts")

    print("[*] Fetching Substack backups...")
    substack = fetch_substack_from_backup()
    print(f"    {len(substack)} articles")

    # Combine: MbD first, then Dev.to, HN, Substack
    all_articles = mbd + devto + hn + substack
    total = len(all_articles)
    print(f"[*] Total: {total} items across {len(set(a['platform'] for a in all_articles))} platforms")

    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"📰 内容发布日报 {today} ({total} 篇)"
    html = build_html(all_articles)
    plain = build_plain(all_articles)

    send_email(subject, html, plain)


if __name__ == "__main__":
    main()
