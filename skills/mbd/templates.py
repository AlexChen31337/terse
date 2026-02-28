"""
MbD (面包多) 内容模板
提供3个简体中文内容创作模板，用于快速创建商品草稿。
"""

from __future__ import annotations

# ── 模板定义 ──────────────────────────────────────────────────────────────────

# 模板1：学习资料包
TEMPLATE_STUDY_PACK = {
    "name": "name_placeholder",           # 替换为实际商品名，如：《Python进阶实战》资料包
    "productname": "name_placeholder",
    "producttype": 1,                       # 单品
    "category": 1,                          # 学习
    "productprice": 19.9,
    "productimage": "",                     # 替换为封面图 URL
    "productdetail": (
        "📚 本资料包包含系统化学习资料，适合有一定基础的同学深入提升。\n\n"
        "✅ 内容亮点：\n"
        "- 精心整理的知识体系\n"
        "- 实战案例与练习题\n"
        "- 配套学习笔记\n\n"
        "💡 适合人群：希望系统提升技能的学习者\n\n"
        "📦 资料格式：PDF + 示例代码"
    ),
    "productcontent": (
        "感谢购买！以下是您的专属资料下载链接：\n\n"
        "[资料下载链接] https://example.com/download\n\n"
        "如有问题欢迎在评论区留言，我会尽快回复 😊"
    ),
    "opendata": 0,
    "sale_limit": -1,
    "buyer_comment": 1,    # 仅买家可评论
    # --- 使用说明 ---
    "_description": "学习资料包模板 - 适用于知识类PDF、学习笔记、教程合集等",
    "_usage": (
        "from templates import TEMPLATE_STUDY_PACK\n"
        "from mbd_client import MbDClient\n"
        "c = MbDClient()\n"
        "t = dict(TEMPLATE_STUDY_PACK)\n"
        "t['productname'] = '《Python进阶实战》资料包'\n"
        "t['productprice'] = 29.9\n"
        "result = c.create_draft(**{k: v for k, v in t.items() if not k.startswith('_') and k != 'name'})\n"
    ),
}

# 模板2：数字绘画/素材包
TEMPLATE_DIGITAL_ART = {
    "name": "name_placeholder",
    "productname": "name_placeholder",
    "producttype": 1,                       # 单品
    "category": 2,                          # 绘画
    "productprice": 9.9,
    "productimage": "",
    "productdetail": (
        "🎨 精心制作的数字素材包，可商用！\n\n"
        "✅ 包含内容：\n"
        "- 高质量矢量素材\n"
        "- 多种格式（PNG / SVG / PSD）\n"
        "- 完整商用授权\n\n"
        "🖌️ 适合设计师、插画师、自媒体创作者使用\n\n"
        "📐 分辨率：最高 4K，无损质量"
    ),
    "productcontent": (
        "感谢支持！您的专属下载链接：\n\n"
        "🔗 [素材包下载] https://example.com/art-pack\n\n"
        "📋 使用须知：\n"
        "1. 可用于商业项目\n"
        "2. 不可二次销售原始文件\n"
        "3. 注明来源更好哦～\n\n"
        "喜欢的话欢迎五星好评 ⭐⭐⭐⭐⭐"
    ),
    "opendata": 1,     # 公开销量数据，增加信任感
    "sale_limit": -1,
    "buyer_comment": 0,
    "_description": "数字艺术/素材包模板 - 适用于设计素材、图标、插画、字体等",
    "_usage": (
        "from templates import TEMPLATE_DIGITAL_ART\n"
        "from mbd_client import MbDClient\n"
        "c = MbDClient()\n"
        "t = dict(TEMPLATE_DIGITAL_ART)\n"
        "t['productname'] = '手绘风商业插画素材包 Vol.1'\n"
        "t['productprice'] = 14.9\n"
        "t['productimage'] = 'https://your-cdn.com/cover.jpg'\n"
        "result = c.create_draft(**{k: v for k, v in t.items() if not k.startswith('_') and k != 'name'})\n"
    ),
}

# 模板3：科技工具/资源合集
TEMPLATE_TECH_TOOLKIT = {
    "name": "name_placeholder",
    "productname": "name_placeholder",
    "producttype": 1,                       # 单品
    "category": 4,                          # 科技
    "productprice": 39.9,
    "productimage": "",
    "productdetail": (
        "🚀 精选科技工具资源合集，帮你效率翻倍！\n\n"
        "✅ 包含内容：\n"
        "- 精选工具清单（附下载/获取方法）\n"
        "- 使用技巧与最佳实践\n"
        "- 定期更新，永久有效\n\n"
        "⚡ 适合人群：开发者、研究者、效率达人\n\n"
        "🔄 购买后可免费获取后续更新版本"
    ),
    "productcontent": (
        "欢迎加入！以下是专属内容：\n\n"
        "🛠️ 工具合集文档：https://example.com/toolkit\n\n"
        "📌 使用指南：\n"
        "1. 点击链接查看完整工具列表\n"
        "2. 每个工具都附有简短介绍和获取方式\n"
        "3. 建议收藏，随时查阅\n\n"
        "💬 有问题？欢迎评论区交流，我每天都会回复！\n\n"
        "🎁 福利：关注我获取更多免费内容~"
    ),
    "opendata": 1,
    "sale_limit": -1,
    "buyer_comment": 1,
    "_description": "科技工具/资源合集模板 - 适用于软件推荐、AI工具、开发资源等",
    "_usage": (
        "from templates import TEMPLATE_TECH_TOOLKIT\n"
        "from mbd_client import MbDClient\n"
        "c = MbDClient()\n"
        "t = dict(TEMPLATE_TECH_TOOLKIT)\n"
        "t['productname'] = '2024最强AI工具合集（持续更新）'\n"
        "t['productprice'] = 49.9\n"
        "result = c.create_draft(**{k: v for k, v in t.items() if not k.startswith('_') and k != 'name'})\n"
    ),
}

# 所有模板列表
ALL_TEMPLATES = [
    TEMPLATE_STUDY_PACK,
    TEMPLATE_DIGITAL_ART,
    TEMPLATE_TECH_TOOLKIT,
]


def get_template(name: str) -> dict:
    """
    按名称获取模板。
    可用名称: 'study_pack', 'digital_art', 'tech_toolkit'
    """
    mapping = {
        "study_pack": TEMPLATE_STUDY_PACK,
        "digital_art": TEMPLATE_DIGITAL_ART,
        "tech_toolkit": TEMPLATE_TECH_TOOLKIT,
    }
    if name not in mapping:
        raise ValueError(f"未知模板：{name}。可用：{list(mapping.keys())}")
    return dict(mapping[name])


def apply_template(template: dict, **overrides) -> dict:
    """
    应用模板并覆盖指定字段，过滤掉元数据字段（以 _ 开头）。
    返回可直接传入 MbDClient.create_draft() 的参数字典。
    """
    result = {k: v for k, v in template.items() if not k.startswith("_") and k != "name"}
    result.update(overrides)
    return result


if __name__ == "__main__":
    # 打印模板概要
    for tmpl in ALL_TEMPLATES:
        print(f"📦 {tmpl['_description']}")
        print(f"   名称: {tmpl.get('productname', '(待设置)')}")
        print(f"   分类: {tmpl.get('category')}  价格: ¥{tmpl.get('productprice')}")
        print()
