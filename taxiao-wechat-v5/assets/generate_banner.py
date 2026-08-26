#!/usr/bin/env python3
"""
「AI速递」固定推文封面图生成器 —— 他晓 v5(dark 版,2x 超采样保证清晰)

900×383 固定封面(thumb_media_id),dark 风格:
近黑底 + 白色粗标题 + 正面机器人(描边轮廓 + 红色发光双眼),边缘锐利不模糊。

用法:
    python3 generate_banner.py --output assets/banner.png
"""

import argparse
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

BG = "#0c0d10"
WHITE = "#f5f5f7"
DIM = "#9a9aa2"
EYE_RED = "#ff3b30"
BODY = "#1d1f24"        # 机器人机身(近黑)
RIM = "#8b929e"         # 轮廓描边(银灰)
PANEL = "#14161a"       # 面板深色

W, H = 900, 383
SS = 2                   # 超采样倍率:内部按 1800×766 绘制,缩小后锐利


def find_font() -> str | None:
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for fp in candidates:
        if os.path.exists(fp):
            return fp
    result = subprocess.run(["find", "/System/Library/Fonts", "-name", "*PingFang*"],
                            capture_output=True, text=True)
    lines = result.stdout.strip().split("\n")
    return lines[0] if lines and lines[0] else None


def load_font(size: int, font_path: str | None) -> ImageFont.FreeTypeFont:
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def draw_robot(draw: ImageDraw.ImageDraw, cx: int, top: int, s: float) -> None:
    """正面机器人:深色机身 + 银灰描边 + 红色双眼,扁平矢量、边缘锐利。"""

    def R(x):
        return cx + int(x * s)

    def Y(y):
        return top + int(y * s)

    ow = max(2, int(3 * s))  # 描边宽

    # 天线
    draw.line([(R(0), Y(6)), (R(0), Y(34))], fill=RIM, width=ow)
    draw.ellipse([R(-8), Y(-2), R(8), Y(14)], fill=EYE_RED, outline=RIM, width=1)
    # 头部:圆角矩形 + 描边
    draw.rounded_rectangle([R(-78), Y(34), R(78), Y(142)], radius=int(34 * s),
                           fill=BODY, outline=RIM, width=ow)
    # 耳朵
    draw.rounded_rectangle([R(-94), Y(66), R(-78), Y(110)], radius=int(8 * s),
                           fill=BODY, outline=RIM, width=ow)
    draw.rounded_rectangle([R(78), Y(66), R(94), Y(110)], radius=int(8 * s),
                           fill=BODY, outline=RIM, width=ow)
    # 面板(脸)
    draw.rounded_rectangle([R(-58), Y(56), R(58), Y(120)], radius=int(20 * s), fill=PANEL)
    # 双眼:红色发光(清晰圆点,无模糊)
    for ex in (-28, 28):
        draw.ellipse([R(ex - 12), Y(76), R(ex + 12), Y(100)], fill=EYE_RED)
        draw.ellipse([R(ex - 5), Y(79), R(ex + 5), Y(89)], fill="#ffd7d5")  # 高光点
    # 嘴部细线
    draw.line([(R(-20), Y(110)), (R(20), Y(110))], fill=RIM, width=max(2, int(2 * s)))
    # 脖子
    draw.rounded_rectangle([R(-20), Y(142), R(20), Y(162)], radius=int(6 * s),
                           fill=BODY, outline=RIM, width=ow)
    # 躯干
    draw.rounded_rectangle([R(-96), Y(162), R(96), Y(316)], radius=int(24 * s),
                           fill=BODY, outline=RIM, width=ow)
    # 胸前面板 + 红色电源点 + 装饰线
    draw.rounded_rectangle([R(-56), Y(184), R(56), Y(258)], radius=int(14 * s), fill=PANEL)
    draw.ellipse([R(-9), Y(196), R(9), Y(214)], fill=EYE_RED)
    draw.line([(R(-38), Y(232)), (R(38), Y(232))], fill=RIM, width=max(2, int(2 * s)))
    draw.line([(R(-26), Y(244)), (R(26), Y(244))], fill=RIM, width=max(2, int(2 * s)))
    # 手臂(胶囊形)
    draw.rounded_rectangle([R(-128), Y(176), R(-100), Y(268)], radius=int(13 * s),
                           fill=BODY, outline=RIM, width=ow)
    draw.rounded_rectangle([R(100), Y(176), R(128), Y(268)], radius=int(13 * s),
                           fill=BODY, outline=RIM, width=ow)


def generate(output: str) -> None:
    w, h = W * SS, H * SS
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)
    font_path = find_font()

    def S(v):
        return v * SS

    # 品牌行
    brand_font = load_font(S(30), font_path)
    draw.text((S(62), S(58)), "他晓", font=brand_font, fill=DIM)

    # 主标题 AI速递(纯白粗体,加重 stroke)
    title_font = load_font(S(118), font_path)
    draw.text((S(56), S(122)), "AI速递", font=title_font, fill=WHITE,
              stroke_width=S(3), stroke_fill=WHITE)

    # 红色小方块强调(替代橙色,呼应机器人双眼)
    draw.rectangle([S(62), S(268), S(140), S(278)], fill=EYE_RED)
    draw.rectangle([S(150), S(268), S(176), S(278)], fill="#3a3d44")

    # 副标题
    sub_font = load_font(S(26), font_path)
    draw.text((S(62), S(300)), "每日精选全球 AI 领域重要动态", font=sub_font, fill=DIM)

    # 右侧正面机器人
    draw_robot(draw, cx=S(690), top=S(38), s=S(0.92))

    # 超采样缩小,边缘锐利
    img = img.resize((W, H), Image.LANCZOS)
    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
    img.save(output, "PNG")
    print(f"封面图已生成: {output} ({W}x{H})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成「AI速递」固定推文封面图(dark 版)")
    parser.add_argument("--output", default=os.path.join(os.path.dirname(__file__), "banner.png"))
    args = parser.parse_args()
    generate(args.output)
