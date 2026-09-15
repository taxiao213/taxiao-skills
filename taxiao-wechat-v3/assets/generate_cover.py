#!/usr/bin/env python3
"""
微信公众号封面图生成器（Pillow）

为「他晓」公众号生成 900×383 Banner 风格封面图。
封面图仅用于微信公众号推送链接的缩略图（thumb_media_id），不嵌入正文 HTML。

用法:
    python3 generate_cover.py \
        --title "DevEco Code 全解析" \
        --subtitle "鸿蒙AI开发工具链实战指南" \
        --tags "DevEco Code · DevEco CLI · Skill · MCP" \
        --output "DevEco_Code_公众号推文_assets/cover.png" \
        --theme blue

主题选项:
    blue    科技蓝（默认，适合AI/技术/开发类文章）
    orange  活力橙（适合产品/创业/增长类文章）
    purple  深空紫（适合深度分析/行业报告类文章）
    green   清新绿（适合生态/开源/教育类文章）
"""

import argparse
import os
import sys
import math
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# 主题配色方案
# ============================================================
THEMES = {
    "blue": {
        "primary": (25, 118, 210),       # #1976D2
        "primary_light": (100, 181, 246), # #64B5F6
        "primary_pale": (187, 222, 251),  # #BBDEFB
        "bg_start": (245, 249, 255),      # #F5F9FF
        "bg_end": (225, 238, 250),        # #E1EEFA
        "text_dark": (26, 35, 50),        # #1A2332
        "text_mid": (74, 85, 104),        # #4A5568
        "text_light": (113, 128, 150),    # #718096
    },
    "orange": {
        "primary": (242, 101, 34),        # #F26522
        "primary_light": (255, 152, 0),   # #FF9800
        "primary_pale": (255, 224, 178),  # #FFE0B2
        "bg_start": (255, 248, 245),      # #FFF8F5
        "bg_end": (250, 235, 225),        # #FAEBE1
        "text_dark": (51, 51, 51),        # #333333
        "text_mid": (102, 102, 102),      # #666666
        "text_light": (153, 153, 153),    # #999999
    },
    "purple": {
        "primary": (106, 27, 154),        # #6A1B9A
        "primary_light": (171, 71, 188),   # #AB47BC
        "primary_pale": (225, 190, 231),  # #E1BEE7
        "bg_start": (253, 247, 255),      # #FDF7FF
        "bg_end": (240, 230, 250),        # #F0E6FA
        "text_dark": (38, 20, 55),        # #261437
        "text_mid": (85, 65, 100),        # #554164
        "text_light": (130, 115, 140),    # #82738C
    },
    "green": {
        "primary": (46, 125, 50),         # #2E7D32
        "primary_light": (102, 187, 106),  # #66BB6A
        "primary_pale": (200, 230, 201),  # #C8E6C9
        "bg_start": (248, 255, 248),      # #F8FFF8
        "bg_end": (232, 245, 233),        # #E8F5E9
        "text_dark": (27, 50, 30),        # #1B321E
        "text_mid": (60, 85, 65),         # #3C5541
        "text_light": (100, 120, 105),    # #647869
    },
}

W, H = 900, 383


def find_font():
    """查找可用的中文字体,返回 (字体路径, ttc face index)。

    注意:.ttc 集合默认 index=0 可能是繁体或细字重,需显式指定:
    - Hiragino Sans GB.ttc:  0=W3(细) 2=W6(粗)
    - STHeiti Medium.ttc:    0=Heiti TC(繁) 1=Heiti SC(简)
    """
    candidates = [
        # macOS 字体(显式取简体粗字重,小尺寸下更清晰)
        ("/System/Library/Fonts/PingFang.ttc", 0),
        ("/System/Library/Fonts/Hiragino Sans GB.ttc", 2),   # W6 粗体
        ("/System/Library/Fonts/STHeiti Medium.ttc", 1),     # Heiti SC 简体
        ("/Library/Fonts/Arial Unicode.ttf", 0),
        # Linux 字体
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 0),
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 0),
        ("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", 0),
        ("/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc", 0),
        ("/usr/share/fonts/truetype/noto/NotoSansSC-Regular.otf", 0),
        ("/usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf", 0),
    ]
    for fp, idx in candidates:
        if os.path.exists(fp):
            try:
                ImageFont.truetype(fp, 20, index=idx)
                return fp, idx
            except Exception:
                continue

    # macOS fallback search
    if sys.platform == "darwin":
        result = subprocess.run(
            ["find", "/System/Library/Fonts", "/Library/Fonts", "-name", "*PingFang*", "-o", "-name", "*Hiragino*", "-o", "-name", "*NotoSans*SC*"],
            capture_output=True, text=True
        )
        lines = result.stdout.strip().split("\n")
        if lines and lines[0]:
            return lines[0], 0

    # Linux fallback search
    result = subprocess.run(
        ["find", "/usr/share/fonts", "-name", "*Noto*CJK*", "-o", "-name", "*NotoSans*SC*"],
        capture_output=True, text=True
    )
    lines = result.stdout.strip().split("\n")
    if lines and lines[0]:
        return lines[0], 0

    print("警告：未找到中文字体，使用默认字体（中文可能无法显示）")
    return None


def load_font(size, font):
    """按 (路径, ttc index) 加载字体,失败回退默认字体"""
    if font:
        try:
            return ImageFont.truetype(font[0], size, index=font[1])
        except Exception:
            pass
    return ImageFont.load_default()


def lerp_color(c1, c2, t):
    """线性插值两个颜色"""
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def draw_circle_alpha(img, cx, cy, radius, color, alpha_max=1.0, feather=0.6):
    """绘制带羽化边缘的圆形"""
    draw = img.load()
    x_min = max(0, int(cx - radius))
    x_max = min(W, int(cx + radius))
    y_min = max(0, int(cy - radius))
    y_max = min(H, int(cy + radius))

    for y in range(y_min, y_max):
        for x in range(x_min, x_max):
            dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            if dist <= radius:
                alpha = max(0, 1 - (dist / radius) ** feather) * alpha_max
                bg = img.getpixel((x, y))
                if len(bg) == 4:
                    bg = bg[:3]
                blended = lerp_color(bg, color, alpha)
                img.putpixel((x, y), blended)


def generate_cover(title, subtitle, tags, output_path, theme_name="blue", brand="他晓 · 科技前沿"):
    """生成封面图"""
    theme = THEMES.get(theme_name, THEMES["blue"])
    font = find_font()

    # 创建画布（RGB）
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # === 1. 背景渐变（135°） ===
    for y in range(H):
        for x in range(W):
            t = (x / W * 0.7 + y / H * 0.3)
            color = lerp_color(theme["bg_start"], theme["bg_end"], t)
            img.putpixel((x, y), color)

    # === 2. 装饰圆形 ===
    # 右上大圆（部分溢出）
    draw_circle_alpha(img, W + 60, -80, 280, theme["primary"], alpha_max=0.85, feather=0.6)

    # 左下中圆（部分溢出）
    draw_circle_alpha(img, -40, H + 30, 200, theme["primary_light"], alpha_max=0.7, feather=0.6)

    # 右下小圆
    draw_circle_alpha(img, W - 60, H - 40, 50, theme["primary_pale"], alpha_max=0.8, feather=0.5)

    # 左上小圆
    draw_circle_alpha(img, 70, 50, 35, theme["primary"], alpha_max=0.7, feather=0.5)

    # === 3. 文字内容 ===
    draw = ImageDraw.Draw(img)

    # 主标题
    title_size = 56
    title_font = load_font(title_size, font)
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    title_x = (W - title_w) // 2
    title_y = int(H * 0.28)
    draw.text((title_x, title_y), title, fill=theme["primary"], font=title_font)

    # 装饰横线
    line_y = title_y + title_size + 16
    line_w = 80
    line_x = (W - line_w) // 2
    draw.rounded_rectangle([line_x, line_y, line_x + line_w, line_y + 3], radius=2, fill=theme["primary"])

    # 副标题
    sub_size = 24
    sub_font = load_font(sub_size, font)
    sub_bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
    sub_w = sub_bbox[2] - sub_bbox[0]
    sub_x = (W - sub_w) // 2
    sub_y = line_y + 20
    draw.text((sub_x, sub_y), subtitle, fill=theme["text_dark"], font=sub_font)

    # 标签行
    if tags:
        tag_size = 16
        tag_font = load_font(tag_size, font)
        tag_bbox = draw.textbbox((0, 0), tags, font=tag_font)
        tag_w = tag_bbox[2] - tag_bbox[0]
        tag_x = (W - tag_w) // 2
        tag_y = sub_y + sub_size + 18
        draw.text((tag_x, tag_y), tags, fill=theme["text_mid"], font=tag_font)

    # 底部品牌
    brand_size = 14
    brand_font = load_font(brand_size, font)
    brand_bbox = draw.textbbox((0, 0), brand, font=brand_font)
    brand_w = brand_bbox[2] - brand_bbox[0]
    brand_x = (W - brand_w) // 2
    brand_y = H - 45
    draw.text((brand_x, brand_y), brand, fill=theme["text_light"], font=brand_font)

    # === 4. 保存 ===
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.save(output_path, "PNG")
    print(f"封面图已生成: {output_path}")
    print(f"  尺寸: {img.size}")
    print(f"  主题: {theme_name}")
    print(f"  标题: {title}")


def main():
    parser = argparse.ArgumentParser(description="生成微信公众号封面图")
    parser.add_argument("--title", required=True, help="主标题（如：DevEco Code 全解析）")
    parser.add_argument("--subtitle", default="", help="副标题")
    parser.add_argument("--tags", default="", help="标签行（用 · 分隔）")
    parser.add_argument("--brand", default="他晓 · 科技前沿", help="底部品牌文字")
    parser.add_argument("--output", required=True, help="输出路径（PNG）")
    parser.add_argument("--theme", default="blue", choices=["blue", "orange", "purple", "green"], help="配色主题")
    args = parser.parse_args()

    generate_cover(
        title=args.title,
        subtitle=args.subtitle,
        tags=args.tags,
        output_path=args.output,
        theme_name=args.theme,
        brand=args.brand,
    )


if __name__ == "__main__":
    main()
