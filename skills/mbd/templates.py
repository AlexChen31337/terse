"""
面包多产品模板
~~~~~~~~~~~~~

预设产品模板，用于快速创建常见类型的产品。
"""

from __future__ import annotations

# ── 图文内容模板 ──────────────────────────────────────────

template_article: dict = {
    "name": "图文内容模板",
    "description": "适用于付费文章、教程、指南等",
    "fields": {
        "productname": "【标题】如何用 AI 提升效率",
        "producttype": 1,  # 单品
        "productdetail": (
            "本文将详细介绍如何利用 AI 工具提升日常工作效率。"
            "涵盖 ChatGPT、Claude 等主流工具的实战技巧。\n\n"
            "📌 你将获得：\n"
            "• 10+ 实用 AI 工作流\n"
            "• 提示词模板合集\n"
            "• 效率提升案例分析"
        ),
        "productcontent": (
            "【付费内容】\n\n"
            "## 第一章：AI 工具选择\n"
            "在这里放置你的付费图文内容...\n\n"
            "## 第二章：提示词工程\n"
            "详细的提示词技巧...\n\n"
            "## 第三章：实战案例\n"
            "真实的效率提升案例..."
        ),
        "productimage": "https://mbd.pub/default-cover.png",
        "productprice": 9.9,
        "category": 4,  # 科技
        "opendata": 0,
        "sale_limit": -1,
        "buyer_comment": 0,
    },
}

# ── 文件商品模板 ──────────────────────────────────────────

template_file_product: dict = {
    "name": "文件商品模板",
    "description": "适用于 PDF、源码包、素材包等文件类产品",
    "fields": {
        "productname": "【资源包】Python 学习路线图 + 项目源码",
        "producttype": 1,  # 单品
        "productdetail": (
            "精心整理的 Python 学习资源包，适合初学者到进阶开发者。\n\n"
            "📦 包含内容：\n"
            "• Python 学习路线图 (高清 PDF)\n"
            "• 10 个实战项目源码\n"
            "• 配套视频教程链接\n"
            "• 常见面试题汇总\n\n"
            "💡 购买后自动获取下载链接"
        ),
        "productcontent": (
            "【下载链接】\n\n"
            "🔗 百度网盘: https://pan.baidu.com/s/xxx\n"
            "   提取码: xxxx\n\n"
            "🔗 Google Drive: https://drive.google.com/xxx\n\n"
            "⚠️ 请勿分享，仅供个人学习使用"
        ),
        "productimage": "https://mbd.pub/default-cover.png",
        "productprice": 19.9,
        "category": 1,  # 学习
        "opendata": 0,
        "sale_limit": -1,
        "buyer_comment": 1,  # 仅购买者可评论
    },
}

# ── 全家桶模板 ────────────────────────────────────────────

template_bundle: dict = {
    "name": "全家桶模板",
    "description": "适用于打包多个产品为套餐",
    "fields": {
        "productname": "【全家桶】AI 开发者工具箱 — 全套课程合集",
        "producttype": 3,  # 全家桶
        "productdetail": (
            "🎁 AI 开发者必备全家桶！\n\n"
            "包含所有 AI 相关课程和资源，一次购买永久访问。\n\n"
            "📚 包含课程：\n"
            "• ChatGPT 进阶指南 (价值 ¥29.9)\n"
            "• Prompt Engineering 实战 (价值 ¥39.9)\n"
            "• AI 绘画从入门到精通 (价值 ¥19.9)\n"
            "• LLM 应用开发教程 (价值 ¥49.9)\n\n"
            "💰 单独购买总价: ¥139.6\n"
            "🔥 全家桶特价: ¥69.9 (省 50%!)"
        ),
        "productimage": "https://mbd.pub/default-cover.png",
        "productprice": 69.9,
        "category": 4,  # 科技
        "opendata": 1,  # 公开销售数据
        "sale_limit": -1,
        "buyer_comment": 0,
    },
}

# ── 所有模板 ──────────────────────────────────────────────

ALL_TEMPLATES: dict[str, dict] = {
    "article": template_article,
    "file": template_file_product,
    "bundle": template_bundle,
}


def get_template(name: str) -> dict | None:
    """获取模板。名称: article, file, bundle"""
    return ALL_TEMPLATES.get(name)


def list_templates() -> list[dict[str, str]]:
    """列出所有可用模板。"""
    return [
        {"key": k, "name": v["name"], "description": v["description"]}
        for k, v in ALL_TEMPLATES.items()
    ]
