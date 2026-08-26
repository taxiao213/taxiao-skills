#!/usr/bin/env python3
"""
微信公众号封面图生成器（Pillow）—— 他晓 v4 暖色极简版

为「他晓」公众号生成 900×383 Banner 风格封面图。
封面图仅用于微信公众号推送链接的缩略图（thumb_media_id），不嵌入正文 HTML。

设计风格：暖色极简 + 编辑卡片式布局，与 taxiao-wechat-v4 技能配色系统完全一致。
- 纯色暖米白背景 #fdfdf8
- 左侧橙色竖条强调 #ed7b2f
- 暗色顶部条 #1e1f23
- 左对齐文字，层次清晰

用法:
    python3 generate_cover.py \
        --title "Manus重获自由" \
        --subtitle "林俊旸押注Agent" \
        --tags "Manus · Pragmatik Labs · Agent" \
        --output "Manus_LinJunyang_v4_公众号推文_assets/cover.png" \
        --theme warm

主题选项:
    warm    暖色极简（默认，与 v4 技能配色一致）
    blue    科技蓝（适合AI/技术/开发类文章）
    orange  活力橙（适合产品/创业/增长类文章）
    purple  深空紫（适合深度分析/行业报告类文章）
    green   清新绿（适合生态/开源/教育类文章）
"""

import argparse
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# 主题配色方案（与 SKILL.md 配色系统一致）
# ============================================================
THEMES = {
    "warm": {
        "bg": (253, 253, 248),            # #fdfdf8 暖米白
        "card_bg": (238, 239, 233),       # #eeefe9 浅暖灰
        "primary": (237, 123, 47),        # #ed7b2f 橙色强调
        "dark": (30, 31, 35),             # #1e1f23 暗色
        "text_dark": (35, 37, 29),        # #23251d
        "text_mid": (101, 103, 94),       # #65675e
        "text_light": (158, 160, 150),    # #9ea096
        "border": (191, 193, 183),        # #bfc1b7
    },
    "blue": {
        "bg": (245, 249, 255),
        "card_bg": (225, 238, 250),
        "primary": (25, 118, 210),
        "dark": (26, 35, 50),
        "text_dark": (26, 35, 50),
        "text_mid": (74, 85, 104),
        "text_light": (113, 128, 150),
        "border": (180, 200, 230),
    },
    "orange": {
        "bg": (255, 248, 245),
        "card_bg": (250, 235, 225),
        "primary": (242, 101, 34),
        "dark": (51, 51, 51),
        "text_dark": (51, 51, 51),
        "text_mid": (102, 102, 102),
        "text_light": (153, 153, 153),
        "border": (220, 200, 190),
    },
    "purple": {
        "bg": (253, 247, 255),
        "card_bg": (240, 230, 250),
        "primary": (106, 27, 154),
        "dark": (38, 20, 55),
        "text_dark": (38, 20, 55),
        "text_mid": (85, 65, 100),
        "text_light": (130, 115, 140),
        "border": (210, 195, 225),
    },
    "green": {
        "bg": (248, 255, 248),
        "card_bg": (232, 245, 233),
        "primary": (46, 125, 50),
        "dark": (27, 50, 30),
        "text_dark": (27, 50, 30),
        "text_mid": (60, 85, 65),
        "text_light": (100, 120, 105),
        "border": (195, 215, 200),
    },
}

W, H = 900, 383


def find_font():
    """查找可用的中文字体（支持 macOS 和 Linux）"""
    candidates = [
        # macOS 字体
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        # Linux 字体
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansSC-Regular.otf",
        "/usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf",
    ]
    for fp in candidates:
        if os.path.exists(fp):
            return fp

    # macOS 兜底搜索
    result = subprocess.run(
        ["find", "/System/Library/Fonts", "/Library/Fonts", "-name", "*PingFang*", "-o", "-name", "*Heiti*", "-o", "-name", "*Hiragino*"],
        capture_output=True, text=True
    )
    lines = result.stdout.strip().split("\n")
    if lines and lines[0]:
        return lines[0]

    # Linux 兜底搜索
    result = subprocess.run(
        ["find", "/usr/share/fonts", "-name", "*Noto*CJK*", "-o", "-name", "*NotoSans*SC*"],
        capture_output=True, text=True
    )
    lines = result.stdout.strip().split("\n")
    if lines and lines[0]:
        return lines[0]

    print("警告：未找到中文字体，使用默认字体（中文可能无法显示）")
    return None


def generate_cover(title, subtitle, tags, output_path, theme_name="warm", brand="他晓 · AI观察", date_str=""):
    """生成封面图（暖色极简编辑卡片风格）"""
    theme = THEMES.get(theme_name, THEMES["warm"])
    font_path = find_font()

    # 创建画布（RGB），纯色背景
    img = Image.new("RGB", (W, H), theme["bg"])
    draw = ImageDraw.Draw(img)

    # === 1. 顶部暗色条（4px，与技能 dark_bar 一致） ===
    draw.rectangle([0, 0, W, 4], fill=theme["dark"])

    # === 2. 左侧橙色竖条（6px，强调色，与技能 accent 一致） ===
    accent_x = 0
    draw.rectangle([accent_x, 4, accent_x + 6, H - 4], fill=theme["primary"])

    # === 3. 内容区域（左对齐，留白 60px） ===
    content_x = 60
    content_right = W - 60

    # --- 3.1 顶部信息栏（品牌 + 日期） ---
    info_y = 36
    info_font_size = 13
    info_font = ImageFont.truetype(font_path, info_font_size) if font_path else ImageFont.load_default()

    # 品牌圆点 + 品牌名
    dot_r = 4
    dot_cx = content_x + dot_r
    dot_cy = info_y + info_font_size // 2
    draw.ellipse([dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r], fill=theme["dark"])

    brand_text_x = dot_cx + dot_r + 8
    draw.text((brand_text_x, info_y), brand, fill=theme["text_mid"], font=info_font)

    # 分隔线
    if date_str:
        date_bbox = draw.textbbox((0, 0), date_str, font=info_font)
        date_w = date_bbox[2] - date_bbox[0]
        line_start_x = brand_text_x + draw.textbbox((0, 0), brand, font=info_font)[2] + 16
        line_end_x = content_right - date_w - 8
        if line_end_x > line_start_x + 20:
            line_y = info_y + info_font_size // 2
            draw.rectangle([line_start_x, line_y, line_end_x, line_y + 1], fill=theme["border"])
        draw.text((content_right - date_w, info_y), date_str, fill=theme["text_light"], font=info_font)

    # --- 3.2 主标题 ---
    title_size = 52
    title_font = ImageFont.truetype(font_path, title_size) if font_path else ImageFont.load_default()
    title_y = 100
    draw.text((content_x, title_y), title, fill=theme["text_dark"], font=title_font)

    # --- 3.3 橙色强调线（主标题下方） ---
    line_y = title_y + title_size + 14
    line_w = 64
    draw.rounded_rectangle([content_x, line_y, content_x + line_w, line_y + 4], radius=2, fill=theme["primary"])
    # 短暖灰线
    draw.rounded_rectangle([content_x + line_w + 6, line_y, content_x + line_w + 6 + 20, line_y + 4], radius=2, fill=theme["border"])

    # --- 3.4 副标题 ---
    sub_size = 22
    sub_font = ImageFont.truetype(font_path, sub_size) if font_path else ImageFont.load_default()
    sub_y = line_y + 22
    draw.text((content_x, sub_y), subtitle, fill=theme["text_mid"], font=sub_font)

    # --- 3.5 标签行 ---
    if tags:
        tag_size = 15
        tag_font = ImageFont.truetype(font_path, tag_size) if font_path else ImageFont.load_default()
        tag_y = sub_y + sub_size + 16
        draw.text((content_x, tag_y), tags, fill=theme["text_light"], font=tag_font)

    # === 4. 底部暗色条（4px） ===
    draw.rectangle([0, H - 4, W, H], fill=theme["dark"])

    # === 5. 保存 ===
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.save(output_path, "PNG")
    print(f"封面图已生成: {output_path}")
    print(f"  尺寸: {img.size}")
    print(f"  主题: {theme_name}")
    print(f"  标题: {title}")


def main():
    parser = argparse.ArgumentParser(description="生成微信公众号封面图（他晓 v4 暖色极简版）")
    parser.add_argument("--title", required=True, help="主标题")
    parser.add_argument("--subtitle", default="", help="副标题")
    parser.add_argument("--tags", default="", help="标签行（用 · 分隔）")
    parser.add_argument("--brand", default="他晓 · AI观察", help="底部品牌文字")
    parser.add_argument("--date", default="", help="日期文字（如 2026.08）")
    parser.add_argument("--output", required=True, help="输出路径（PNG）")
    parser.add_argument("--theme", default="warm", choices=["warm", "blue", "orange", "purple", "green"], help="配色主题（默认 warm）")
    args = parser.parse_args()

    generate_cover(
        title=args.title,
        subtitle=args.subtitle,
        tags=args.tags,
        output_path=args.output,
        theme_name=args.theme,
        brand=args.brand,
        date_str=args.date,
    )


if __name__ == "__main__":
    main()
