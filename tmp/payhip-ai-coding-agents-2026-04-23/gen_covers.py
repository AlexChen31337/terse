#!/usr/bin/env python3
"""Generate MbD (768x1024) and Payhip (1600x2400) covers via PIL."""
from PIL import Image, ImageDraw, ImageFont
import os, sys

CJK_FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
]
LATIN_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

def find_font(cands):
    for p in cands:
        if os.path.exists(p):
            return p
    return None

def gradient_bg(w, h):
    img = Image.new("RGB", (w, h), (15, 23, 42))
    px = img.load()
    c1 = (15, 23, 42)   # #0f172a
    c2 = (30, 41, 59)   # #1e293b
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        for x in range(w):
            px[x, y] = (r, g, b)
    return img

def draw_accents(draw, w, h, cyan=(34, 211, 238)):
    # outlined triangles + hex dots scattered
    import random
    random.seed(42)
    for _ in range(12):
        cx = random.randint(40, w - 40)
        cy = random.randint(40, h - 40)
        s = random.randint(6, 16)
        if random.random() < 0.5:
            # triangle outline
            pts = [(cx, cy - s), (cx - s, cy + s), (cx + s, cy + s)]
            draw.polygon(pts, outline=cyan, width=2)
        else:
            # hex dot
            draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=cyan)
    # border accents
    draw.rectangle([20, 20, w - 20, h - 20], outline=cyan, width=2)

def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def wrap_cjk(text, max_chars):
    out = []
    cur = ""
    for c in text:
        cur += c
        if len(cur) >= max_chars:
            out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    return out

def make_mbd_cover(out_path):
    w, h = 768, 1024
    img = gradient_bg(w, h)
    draw = ImageDraw.Draw(img)
    cyan = (34, 211, 238)
    white = (240, 245, 250)
    cjk_font_path = find_font(CJK_FONT_CANDIDATES)
    latin_font_path = find_font(LATIN_FONT_CANDIDATES)

    title_zh = "别再让 AI\n写玩具代码"
    subtitle_zh = "生产级软件的智能体工作流"
    author = "Alex Chen · 2026-04-23"
    tag = "PBR · VBR · 护栏 · 复核"

    if cjk_font_path:
        title_font = ImageFont.truetype(cjk_font_path, 78)
        sub_font = ImageFont.truetype(cjk_font_path, 36)
        small_font = ImageFont.truetype(cjk_font_path, 24)
    else:
        # fallback: english title
        title_zh = "Production-Grade\nAI Agents"
        subtitle_zh = "A Practitioner's Workflow"
        tag = "Plan · Build · Review"
        title_font = ImageFont.truetype(latin_font_path, 64)
        sub_font = ImageFont.truetype(latin_font_path, 32)
        small_font = ImageFont.truetype(latin_font_path, 22)

    draw_accents(draw, w, h, cyan)

    # title
    y = 240
    for line in title_zh.split("\n"):
        tw, th = text_size(draw, line, title_font)
        draw.text(((w - tw) / 2, y), line, fill=white, font=title_font)
        y += th + 20

    # subtitle
    y += 20
    tw, th = text_size(draw, subtitle_zh, sub_font)
    draw.text(((w - tw) / 2, y), subtitle_zh, fill=cyan, font=sub_font)
    y += th + 60

    # tag
    tw, th = text_size(draw, tag, small_font)
    draw.text(((w - tw) / 2, y), tag, fill=white, font=small_font)

    # author at bottom
    tw, th = text_size(draw, author, small_font)
    draw.text(((w - tw) / 2, h - 80), author, fill=cyan, font=small_font)

    img.save(out_path, "PNG", optimize=True)
    print(f"MbD cover: {out_path} {img.size}")

def make_payhip_cover(out_path):
    w, h = 1600, 2400
    img = gradient_bg(w, h)
    draw = ImageDraw.Draw(img)
    cyan = (34, 211, 238)
    white = (240, 245, 250)
    latin_font_path = find_font(LATIN_FONT_CANDIDATES)

    title = "How to Utilize\nAI Coding Agents\nfor Production-Grade\nSoftware"
    subtitle = "A Practitioner's Guide — 2026"
    author = "Alex Chen"
    tag = "Plan · Build · Review · Verify"

    title_font = ImageFont.truetype(latin_font_path, 110)
    sub_font = ImageFont.truetype(latin_font_path, 56)
    small_font = ImageFont.truetype(latin_font_path, 44)

    draw_accents(draw, w, h, cyan)

    y = 380
    for line in title.split("\n"):
        tw, th = text_size(draw, line, title_font)
        draw.text(((w - tw) / 2, y), line, fill=white, font=title_font)
        y += th + 18

    y += 60
    tw, th = text_size(draw, subtitle, sub_font)
    draw.text(((w - tw) / 2, y), subtitle, fill=cyan, font=sub_font)
    y += th + 80

    tw, th = text_size(draw, tag, small_font)
    draw.text(((w - tw) / 2, y), tag, fill=white, font=small_font)

    tw, th = text_size(draw, author, sub_font)
    draw.text(((w - tw) / 2, h - 200), author, fill=cyan, font=sub_font)

    img.save(out_path, "PNG", optimize=True)
    print(f"Payhip cover: {out_path} {img.size}")

if __name__ == "__main__":
    mbd_out = "/media/DATA/.openclaw/workspace/bowen31337/mbd-book-ideas/2026-04-23_AI_Coding_Agents_Production_Grade_Workflow/cover.png"
    payhip_out = "/media/DATA/.openclaw/workspace/tmp/payhip-ai-coding-agents-2026-04-23/cover.png"
    os.makedirs(os.path.dirname(payhip_out), exist_ok=True)
    make_mbd_cover(mbd_out)
    make_payhip_cover(payhip_out)
