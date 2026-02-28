#!/usr/bin/env python3
"""
MbD 每日书稿发布器
每天自动生成一篇新书稿，保存为面包多草稿，并发送邮件通知。
"""

import os
import sys
import json
import smtplib
import subprocess
import requests
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

try:
    import markdown as _md_lib
    def md_to_html(text: str) -> str:
        """Convert Markdown to HTML with common extensions."""
        return _md_lib.markdown(
            text,
            extensions=["extra", "nl2br", "sane_lists"],
        )
except ImportError:
    import re
    def md_to_html(text: str) -> str:
        """Minimal Markdown→HTML fallback (no library needed)."""
        # Headers
        text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.M)
        text = re.sub(r'^## (.+)$',  r'<h2>\1</h2>', text, flags=re.M)
        text = re.sub(r'^# (.+)$',   r'<h1>\1</h1>', text, flags=re.M)
        # Bold / italic
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*',     r'<em>\1</em>', text)
        # Blockquote
        text = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', text, flags=re.M)
        # Line breaks → <br> for blank lines
        text = re.sub(r'\n\n', '</p><p>', text)
        return f'<p>{text}</p>'

WORKSPACE = Path.home() / ".openclaw/workspace"
STATE_FILE = WORKSPACE / "memory/mbd-publisher-state.json"
SKILLS_DIR = WORKSPACE / "skills/mbd"

MBD_BASE = "https://x.mbd.pub/api"

# ── 书稿主题池（每天轮转，可扩展）──────────────────────────────────────────
BOOK_TOPICS = [
    {
        "title": "AI副业指南：躺着月入五位数的真实路径",
        "category": 4,  # 科技
        "outline": "如何利用AI工具建立被动收入，包括：AI写作变现、AI图片销售、AI脚本创作、自动化内容矩阵搭建。",
    },
    {
        "title": "提示词炼金术：让AI为你创造价值的100个咒语",
        "category": 4,
        "outline": "精选100个高效Prompt模板，覆盖创作、营销、数据分析、职场沟通等场景，附使用案例和变体技巧。",
    },
    {
        "title": "AI时代的职场生存手册：不被淘汰的核心技能",
        "category": 1,  # 学习
        "outline": "分析AI对各职业的冲击程度，给出每种职业的转型路径，以及如何将AI变成你最强的职场武器。",
    },
    {
        "title": "赛博朋克副业：用AI+区块链构建你的数字帝国",
        "category": 4,
        "outline": "从零搭建AI+Web3副业体系：AI生成NFT、链上版权确权、智能合约自动分润，技术门槛为零。",
    },
    {
        "title": "AI恋爱教练：用算法理解人心的完整指南",
        "category": 5,  # 生活
        "outline": "用AI分析社交信号、优化沟通策略、设计约会方案——不是让AI替你恋爱，是让AI帮你更懂对方。",
    },
    {
        "title": "懒人理财经：AI帮你选股、择时、管仓的实战记录",
        "category": 4,
        "outline": "真实案例：用AI做技术分析、宏观判断、风险控制。附：AI投资的边界在哪里（重要）。",
    },
    {
        "title": "AI写作工厂：从一个想法到一本书的完整流水线",
        "category": 8,  # 写作
        "outline": "手把手教你搭建AI辅助写作系统：选题→大纲→初稿→润色→封面→发布，全流程工具链和提示词。",
    },
]


def load_token(token_override: str | None = None) -> str:
    if token_override:
        return token_override
    try:
        result = subprocess.run(
            ["bash", str(WORKSPACE / "memory/decrypt.sh"), "mbd-token"],
            capture_output=True, text=True, timeout=10
        )
        token = result.stdout.strip()
        if not token or "ERROR" in token.upper():
            raise ValueError("Token decrypt failed")
        return token
    except Exception as e:
        print(f"❌ 无法加载MbD Token: {e}", file=sys.stderr)
        sys.exit(1)


def load_smtp_env() -> dict:
    try:
        result = subprocess.run(
            ["bash", str(WORKSPACE / "memory/decrypt.sh"), "imap-smtp-env"],
            capture_output=True, text=True, timeout=10
        )
        env = {}
        for line in result.stdout.strip().splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
        return env
    except Exception as e:
        print(f"⚠️ 无法加载SMTP配置: {e}", file=sys.stderr)
        return {}


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_published": None, "published_count": 0, "topic_index": 0, "drafts": []}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def get_today_topic(state: dict) -> dict:
    idx = state.get("topic_index", 0) % len(BOOK_TOPICS)
    return BOOK_TOPICS[idx], idx


def generate_book_content(topic: dict) -> tuple[str, str]:
    """
    使用OpenAI兼容API生成书稿内容。
    返回 (detail, content) — detail是公开描述，content是付费正文。
    """
    today = date.today().strftime("%Y年%m月%d日")
    
    prompt = f"""你是一位幽默、犀利、接地气的中文科技作家，风格类似韩寒+罗永浩+互联网段子手。

请为以下主题写一篇完整的中文电子书章节（简体中文）：

标题：《{topic['title']}》
核心内容：{topic['outline']}
写作日期：{today}

要求：
1. 公开简介（300字以内）：吸引人购买的预览，揭示痛点，吊足胃口，末尾有购买号召
2. 付费正文（2000-3000字）：有实质内容，有具体方法，有真实案例（可以是虚构但合理的），语气轻松不说教
   - 至少3个小节，每节有标题
   - 每章结尾有一句金句
   - 适当加入对话/场景描写增加可读性
   - 不要水字数，每段都要有信息量

请严格按以下JSON格式输出（不要有其他内容）：
{{
  "detail": "公开简介内容",
  "content": "付费正文内容（Markdown格式）"
}}"""

    # 尝试调用本地或远程AI
    # 优先用OpenAI兼容API（如有配置），否则用简单模板
    api_endpoints = [
        ("http://localhost:11434/api/generate", "ollama"),
    ]
    
    for endpoint, api_type in api_endpoints:
        try:
            if api_type == "ollama":
                resp = requests.post(
                    endpoint,
                    json={"model": "qwen2.5:32b", "prompt": prompt, "stream": False},
                    timeout=120
                )
                if resp.ok:
                    raw = resp.json().get("response", "")
                    # 提取JSON
                    start = raw.find("{")
                    end = raw.rfind("}") + 1
                    if start >= 0 and end > start:
                        data = json.loads(raw[start:end])
                        return data["detail"], data["content"]
        except Exception:
            continue
    
    # 兜底：生成简单模板内容
    detail = (
        f"📚 今日新书：《{topic['title']}》\n\n"
        f"{topic['outline']}\n\n"
        f"本书以幽默直白的风格，拆解AI时代最实用的生存技巧。"
        f"不讲废话，全是干货。购买后即可阅读完整版。"
    )
    content = (
        f"# {topic['title']}\n\n"
        f"> 生成日期：{today}\n\n"
        f"## 前言\n\n{topic['outline']}\n\n"
        f"## 第一节：为什么你需要这份指南\n\n"
        f"2026年，AI不再是新鲜事。它已经渗透进每个人的生活——"
        f"无论你意识到没有。区别只在于：有人用AI当铲子挖金矿，有人用AI当娱乐消遣。\n\n"
        f"这本书属于前者。\n\n"
        f"## 第二节：核心方法论\n\n"
        f"（完整内容见付费版本）\n\n"
        f"## 第三节：行动清单\n\n"
        f"从今天开始，每天花30分钟，按照本书的路径执行。\n\n"
        f"> **金句：** 信息时代，懒得有方法的人才能赢。\n"
    )
    return detail, content


def save_draft_to_mbd(token: str, topic: dict, detail: str, content: str) -> dict:
    """将书稿保存为面包多草稿（Markdown自动转HTML）"""
    # MbD WYSIWYG editor expects HTML, not Markdown
    detail_html = md_to_html(detail)
    content_html = md_to_html(content)

    headers = {
        "x-token": token,
        "Content-Type": "application/json",
    }
    payload = {
        "productname": topic["title"],
        "producttype": 1,  # 单品
        "productprice": 9.9,
        "productdetail": detail_html,
        "productcontent": content_html,
        "productimage": "https://cdn.2zimu.com/mianbaoduo/img/logoPC.png",  # 默认封面
        "category": topic["category"],
        "opendata": 0,
        "sale_limit": -1,
        "buyer_comment": 0,
    }
    resp = requests.post(f"{MBD_BASE}/drafts/", headers=headers, json=payload, timeout=30)
    data = resp.json()
    if data.get("code") != 200:
        raise RuntimeError(f"MbD API错误: {data.get('error_info', '未知错误')} (code={data.get('code')})")
    return data["result"]


def backup_to_github(topic: dict, detail: str, content: str, cover_local_path: str | None = None):
    """Push markdown + cover image to bowen31337/mbd-book-ideas repo."""
    try:
        import tempfile, shutil
        today = date.today().strftime("%Y-%m-%d")
        safe_title = topic["title"].replace("/", "、").replace(" ", "_")[:40]

        # Decrypt GitHub token
        result = subprocess.run(
            ["bash", str(WORKSPACE / "memory/decrypt.sh"), "github-token-bowen31337"],
            capture_output=True, text=True, timeout=10
        )
        gh_token = result.stdout.strip()
        if not gh_token or "ERROR" in gh_token.upper():
            print("⚠️ GitHub token unavailable, skipping backup")
            return

        repo_url = f"https://{gh_token}@github.com/bowen31337/mbd-book-ideas.git"
        clone_dir = Path(tempfile.mkdtemp()) / "mbd-book-ideas"

        print("📦 Backing up to GitHub...")
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(clone_dir)],
            capture_output=True, timeout=60
        )

        # Single shared folder for both md and cover
        drafts_dir = clone_dir / "drafts"
        drafts_dir.mkdir(exist_ok=True)

        # Write markdown
        md_filename = f"{today}_{safe_title}.md"
        md_content = f"# 《{topic['title']}》\n\n> 发布日期：{today}\n\n## 公开简介\n\n{detail}\n\n---\n\n## 正文\n\n{content}\n"
        (drafts_dir / md_filename).write_text(md_content, encoding="utf-8")
        print(f"   📝 drafts/{md_filename}")

        # Copy cover image if available
        cover_filename = None
        if cover_local_path and Path(cover_local_path).exists():
            cover_filename = f"{today}_{safe_title}.png"
            shutil.copy2(cover_local_path, drafts_dir / cover_filename)
            print(f"   🖼  drafts/{cover_filename}")

        # Git commit & push
        subprocess.run(["git", "config", "user.email", "alex.chen31337@gmail.com"], cwd=clone_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Alex Chen"], cwd=clone_dir, capture_output=True)
        subprocess.run(["git", "add", "drafts/"], cwd=clone_dir, capture_output=True)

        commit_msg = f"feat: add {today} — 《{topic['title']}》"
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=clone_dir, capture_output=True, text=True
        )
        if "nothing to commit" in result.stdout:
            print("   ℹ️  Nothing new to commit")
            return

        push = subprocess.run(
            ["git", "push", repo_url, "main"],
            cwd=clone_dir, capture_output=True, text=True, timeout=60
        )
        if push.returncode == 0:
            print(f"✅ GitHub backup pushed: books/{md_filename}" + (f" + covers/{cover_filename}" if cover_filename else ""))
        else:
            print(f"⚠️ Push failed: {push.stderr[:200]}")

        # Cleanup
        shutil.rmtree(clone_dir.parent, ignore_errors=True)

    except Exception as e:
        print(f"⚠️ GitHub backup failed (non-fatal): {e}")


def send_email_notification(smtp_env: dict, topic: dict, draft: dict, bowen_email: str):
    """发送邮件通知"""
    if not smtp_env:
        print("⚠️ SMTP未配置，跳过邮件通知")
        return

    today = date.today().strftime("%Y年%m月%d日")
    urlkey = draft.get("urlkey", "N/A")
    productid = draft.get("productid") or draft.get("id", "N/A")
    
    subject = f"📚 MbD每日新书草稿已就绪 — {today}"
    
    body_html = f"""
<html><body style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
<h2 style="color: #333;">📚 今日书稿已保存为草稿</h2>
<table style="width:100%; border-collapse:collapse;">
  <tr><td style="padding:8px; color:#666; width:100px;">书名</td>
      <td style="padding:8px; font-weight:bold;">《{topic['title']}》</td></tr>
  <tr style="background:#f9f9f9;"><td style="padding:8px; color:#666;">日期</td>
      <td style="padding:8px;">{today}</td></tr>
  <tr><td style="padding:8px; color:#666;">草稿ID</td>
      <td style="padding:8px; font-family:monospace;">{productid}</td></tr>
  <tr style="background:#f9f9f9;"><td style="padding:8px; color:#666;">URLKey</td>
      <td style="padding:8px; font-family:monospace;">{urlkey}</td></tr>
</table>
<br>
<p style="margin:16px 0;"><strong>下一步：</strong></p>
<ul>
  <li>前往 <a href="https://mbd.pub/o/config/developer">面包多草稿箱</a> 查看并编辑</li>
  <li>满意后发布，或让 Alex 帮你自动发布</li>
</ul>
<hr style="border:none; border-top:1px solid #eee; margin:20px 0;">
<p style="color:#999; font-size:12px;">由 Alex Chen 自动生成 · MbD每日发布系统</p>
</body></html>
"""
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_env.get("SMTP_FROM", smtp_env.get("SMTP_USER", "alex.chen31337@gmail.com"))
    msg["To"] = bowen_email
    msg.attach(MIMEText(body_html, "html", "utf-8"))
    
    try:
        host = smtp_env.get("SMTP_HOST", "smtp.gmail.com")
        port = int(smtp_env.get("SMTP_PORT", 587))
        user = smtp_env.get("SMTP_USER", "")
        passwd = smtp_env.get("SMTP_PASS", "")
        
        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            server.starttls()
            server.login(user, passwd)
            server.sendmail(msg["From"], [bowen_email], msg.as_string())
        print(f"✅ 邮件通知已发送至 {bowen_email}")
    except Exception as e:
        print(f"⚠️ 邮件发送失败: {e}", file=sys.stderr)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="MbD每日书稿自动发布器")
    parser.add_argument("--token", help="MbD开发者Key（可选，默认从加密存储加载）")
    parser.add_argument("--notify-email", default="bowen31337@outlook.com", help="通知邮件地址")
    parser.add_argument("--cover-image", help="本地封面图路径，用于GitHub备份（可选）")
    parser.add_argument("--dry-run", action="store_true", help="仅生成内容，不提交到MbD")
    args = parser.parse_args()

    print(f"🚀 MbD每日书稿发布器启动 — {date.today()}")

    # 检查今天是否已发布
    state = load_state()
    if state.get("last_published") == str(date.today()):
        print("✅ 今日已发布，跳过。")
        sys.exit(0)

    # 加载Token
    token = load_token(args.token)
    smtp_env = load_smtp_env()

    # 选定今日主题
    topic, topic_idx = get_today_topic(state)
    print(f"📖 今日主题：《{topic['title']}》")

    # 生成内容
    print("✍️  正在生成书稿内容...")
    detail, content = generate_book_content(topic)
    print(f"   简介：{len(detail)} 字 | 正文：{len(content)} 字")

    if args.dry_run:
        print("\n── DRY RUN ──")
        print(f"[简介]\n{detail[:200]}...\n")
        print(f"[正文预览]\n{content[:300]}...")
        sys.exit(0)

    # 保存为草稿
    print("💾 正在保存到面包多草稿...")
    try:
        draft = save_draft_to_mbd(token, topic, detail, content)
        print(f"✅ 草稿已保存 — ID: {draft.get('productid') or draft.get('id')} | URLKey: {draft.get('urlkey')}")
    except Exception as e:
        print(f"❌ 草稿保存失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 更新状态
    state["last_published"] = str(date.today())
    state["published_count"] = state.get("published_count", 0) + 1
    state["topic_index"] = (topic_idx + 1) % len(BOOK_TOPICS)
    state.setdefault("drafts", []).append({
        "date": str(date.today()),
        "title": topic["title"],
        "productid": draft.get("productid") or draft.get("id"),
        "urlkey": draft.get("urlkey"),
    })
    save_state(state)

    # GitHub备份
    cover_path = args.cover_image if hasattr(args, 'cover_image') and args.cover_image else None
    backup_to_github(topic, detail, content, cover_local_path=cover_path)

    # 发送邮件通知
    print(f"📧 发送邮件通知至 {args.notify_email}...")
    send_email_notification(smtp_env, topic, draft, args.notify_email)

    print(f"\n🎉 完成！第 {state['published_count']} 本书稿已就绪。")


if __name__ == "__main__":
    main()
