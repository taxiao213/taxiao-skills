#!/usr/bin/env python3
"""AI速递 封面设计稿 ×8 — 900×383 dark 风,2x 超采样。

输出到 assets/drafts/covers/:
  v1_robot.png    正面机器人(红眼)
  v2_chip.png     AI 芯片 + 电路走线
  v3_network.png  神经网络节点图
  v4_typo.png     纯字体排版 + 速度线
  v5_grid.png     赛博网格透视
  v6_datastream.png 数据流瀑布
  v7_overlay.png  机器人剪影 + 大字叠印
  v8_orbit.png    轨道信号

用法: python3 gen_cover_drafts.py          # 第一批 v1-v4
      python3 gen_cover_drafts.py batch2   # 第二批 v5-v8
"""
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

BG = "#0c0d10"
WHITE = "#f5f5f7"
DIM = "#9a9aa2"
RED = "#ff3b30"
RIM = "#8b929e"
BODY = "#1d1f24"
PANEL = "#14161a"
TRACE = "#3a3d44"

W, H = 900, 383
SS = 2
OUT = os.path.join(os.path.dirname(__file__), "drafts", "covers")


def find_font():
    for fp in ["/System/Library/Fonts/PingFang.ttc",
               "/System/Library/Fonts/STHeiti Medium.ttc",
               "/System/Library/Fonts/Hiragino Sans GB.ttc"]:
        if os.path.exists(fp):
            return fp
    r = subprocess.run(["find", "/System/Library/Fonts", "-name", "*PingFang*"],
                       capture_output=True, text=True)
    lines = r.stdout.strip().split("\n")
    return lines[0] if lines and lines[0] else None


FONT_PATH = find_font()


def font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()


def canvas():
    img = Image.new("RGB", (W * SS, H * SS), BG)
    return img, ImageDraw.Draw(img)


def S(v):
    return v * SS


def draw_text_block(draw, sub="每日精选全球 AI 领域重要动态"):
    draw.text((S(62), S(56)), "他晓", font=font(S(30)), fill=DIM)
    draw.text((S(56), S(120)), "AI速递", font=font(S(118)), fill=WHITE,
              stroke_width=S(3), stroke_fill=WHITE)
    draw.rectangle([S(62), S(268), S(140), S(278)], fill=RED)
    draw.rectangle([S(150), S(268), S(176), S(278)], fill=TRACE)
    draw.text((S(62), S(300)), sub, font=font(S(26)), fill=DIM)


def save(img, name):
    os.makedirs(OUT, exist_ok=True)
    img = img.resize((W, H), Image.LANCZOS)
    path = os.path.join(OUT, name)
    img.save(path, "PNG")
    print(path)


# ---------- V1 正面机器人 ----------
def v1_robot():
    img, d = canvas()
    draw_text_block(d)
    cx, top, s = S(690), S(36), S(0.94)

    def R(x): return cx + int(x * s)
    def Y(y): return top + int(y * s)
    ow = max(2, int(3 * s))

    d.line([(R(0), Y(6)), (R(0), Y(34))], fill=RIM, width=ow)
    d.ellipse([R(-8), Y(-2), R(8), Y(14)], fill=RED, outline=RIM)
    d.rounded_rectangle([R(-78), Y(34), R(78), Y(142)], radius=int(34*s), fill=BODY, outline=RIM, width=ow)
    d.rounded_rectangle([R(-94), Y(66), R(-78), Y(110)], radius=int(8*s), fill=BODY, outline=RIM, width=ow)
    d.rounded_rectangle([R(78), Y(66), R(94), Y(110)], radius=int(8*s), fill=BODY, outline=RIM, width=ow)
    d.rounded_rectangle([R(-58), Y(56), R(58), Y(120)], radius=int(20*s), fill=PANEL)
    for ex in (-28, 28):
        d.ellipse([R(ex-12), Y(76), R(ex+12), Y(100)], fill=RED)
        d.ellipse([R(ex-5), Y(79), R(ex+5), Y(89)], fill="#ffd7d5")
    d.line([(R(-20), Y(110)), (R(20), Y(110))], fill=RIM, width=ow)
    d.rounded_rectangle([R(-20), Y(142), R(20), Y(162)], radius=int(6*s), fill=BODY, outline=RIM, width=ow)
    d.rounded_rectangle([R(-96), Y(162), R(96), Y(316)], radius=int(24*s), fill=BODY, outline=RIM, width=ow)
    d.rounded_rectangle([R(-56), Y(184), R(56), Y(258)], radius=int(14*s), fill=PANEL)
    d.ellipse([R(-9), Y(196), R(9), Y(214)], fill=RED)
    d.line([(R(-38), Y(232)), (R(38), Y(232))], fill=RIM, width=ow)
    d.line([(R(-26), Y(244)), (R(26), Y(244))], fill=RIM, width=ow)
    d.rounded_rectangle([R(-128), Y(176), R(-100), Y(268)], radius=int(13*s), fill=BODY, outline=RIM, width=ow)
    d.rounded_rectangle([R(100), Y(176), R(128), Y(268)], radius=int(13*s), fill=BODY, outline=RIM, width=ow)
    save(img, "v1_robot.png")


# ---------- V2 AI 芯片 ----------
def v2_chip():
    img, d = canvas()
    draw_text_block(d)
    cx, cy, half = S(700), S(192), S(86)
    ow = S(3)

    # 四周电路走线(折线 + 端点)
    traces = [
        [(cx - half - S(60), cy - S(50)), (cx - half - S(20), cy - S(50)), (cx - half, cy - S(30))],
        [(cx - half - S(70), cy + S(10)), (cx - half - S(30), cy + S(10)), (cx - half, cy + S(10))],
        [(cx - half - S(56), cy + S(60)), (cx - half - S(24), cy + S(60)), (cx - half, cy + S(40))],
        [(cx + half, cy - S(40)), (cx + half + S(30), cy - S(40)), (cx + half + S(58), cy - S(66))],
        [(cx + half, cy + S(20)), (cx + half + S(36), cy + S(20)), (cx + half + S(64), cy + S(48))],
        [(cx - S(30), cy - half), (cx - S(30), cy - half - S(40)), (cx - S(58), cy - half - S(62))],
        [(cx + S(34), cy - half), (cx + S(34), cy - half - S(34))],
        [(cx + S(10), cy + half), (cx + S(10), cy + half + S(36)), (cx + S(42), cy + half + S(60))],
        [(cx - S(44), cy + half), (cx - S(44), cy + half + S(30))],
    ]
    for pts in traces:
        d.line(pts, fill=TRACE, width=ow)
        ex, ey = pts[0] if pts[0][0] < pts[-1][0] or pts[0][1] < pts[-1][1] else pts[-1]
        r = S(5)
        d.ellipse([ex - r, ey - r, ex + r, ey + r], outline=RIM, width=max(2, ow - 1))

    # 芯片本体:外框 + 引脚 + 内核
    d.rounded_rectangle([cx - half, cy - half, cx + half, cy + half],
                        radius=S(14), fill=BODY, outline=RIM, width=ow)
    pin = S(10)
    for i in range(-2, 3):
        off = int(i * half * 0.36)
        d.rectangle([cx + off - pin//2, cy - half - pin, cx + off + pin//2, cy - half], fill=RIM)
        d.rectangle([cx + off - pin//2, cy + half, cx + off + pin//2, cy + half + pin], fill=RIM)
        d.rectangle([cx - half - pin, cy + off - pin//2, cx - half, cy + off + pin//2], fill=RIM)
        d.rectangle([cx + half, cy + off - pin//2, cx + half + pin, cy + off + pin//2], fill=RIM)
    inner = S(56)
    d.rounded_rectangle([cx - inner, cy - inner, cx + inner, cy + inner],
                        radius=S(10), fill=PANEL, outline=RED, width=S(2))
    d.text((cx - S(31), cy - S(27)), "AI", font=font(S(56)), fill=WHITE,
           stroke_width=S(1), stroke_fill=WHITE)
    save(img, "v2_chip.png")


# ---------- V3 神经网络 ----------
def v3_network():
    img, d = canvas()
    draw_text_block(d)
    nodes = [  # (x, y, r, 是否红色) 固定布局
        (560, 70, 7, 0), (560, 190, 9, 1), (560, 310, 7, 0),
        (680, 40, 6, 0), (680, 130, 8, 0), (680, 250, 8, 1), (680, 340, 6, 0),
        (800, 80, 8, 1), (800, 190, 10, 0), (800, 300, 7, 0),
        (870, 140, 5, 0), (870, 250, 5, 0),
    ]
    links = [(0,3),(0,4),(1,3),(1,4),(1,5),(2,5),(2,6),
             (3,7),(4,7),(4,8),(5,8),(5,9),(6,9),
             (7,10),(8,10),(8,11),(9,11),(7,8),(4,5)]
    for a, b in links:
        x1, y1, _, _ = nodes[a]
        x2, y2, _, _ = nodes[b]
        d.line([(S(x1), S(y1)), (S(x2), S(y2))], fill=TRACE, width=S(2))
    for x, y, r, red in nodes:
        c = RED if red else RIM
        d.ellipse([S(x)-S(r), S(y)-S(r), S(x)+S(r), S(y)+S(r)], fill=c)
        if red:
            rr = S(r + 6)
            d.ellipse([S(x)-rr, S(y)-rr, S(x)+rr, S(y)+rr], outline=c, width=S(1))
    save(img, "v3_network.png")


# ---------- V4 纯字体 + 速度线 ----------
def v4_typo():
    img, d = canvas()
    # 右侧三行速度线:分段短横线,间距干净,红白灰交替
    rows = {
        120: [(560, 660, TRACE, 5), (684, 790, RED, 7), (814, 880, RIM, 5)],
        200: [(600, 726, RED, 7), (750, 880, TRACE, 5)],
        290: [(560, 640, RIM, 5), (664, 800, RED, 7), (824, 880, TRACE, 5)],
    }
    for y, segs in rows.items():
        for x1, x2, color, w in segs:
            d.line([(S(x1), S(y)), (S(x2), S(y))], fill=color, width=S(w))
    # 超大标题
    d.text((S(56), S(84)), "AI速递", font=font(S(150)), fill=WHITE,
           stroke_width=S(4), stroke_fill=WHITE)
    d.text((S(62), S(50)), "他晓 · 每日精选全球 AI 领域重要动态", font=font(S(24)), fill=DIM)
    d.rectangle([S(64), S(272), S(64 + 380), S(278)], fill=RED)
    d.text((S(62), S(300)), "AI NEWS DAILY", font=font(S(26)), fill=DIM)
    save(img, "v4_typo.png")


# ---------- V5 赛博网格透视 ----------
def v5_grid():
    img, d = canvas()
    draw_text_block(d)
    vx, vy = S(710), S(150)  # 灭点
    # 红色地平线光带
    d.line([(S(470), vy), (S(890), vy)], fill=RED, width=S(3))
    # 纵向汇聚线
    for bx in range(430, 940, 60):
        d.line([(vx, vy), (S(bx), S(392))], fill=TRACE, width=S(2))
    # 横向线(间距递增,透视感)
    y = vy
    gap = S(10)
    while y < S(390):
        y += gap
        gap = int(gap * 1.55)
        d.line([(S(430), y), (S(900), y)], fill=TRACE, width=S(2))
    # 灭点红点
    r = S(6)
    d.ellipse([vx - r, vy - r, vx + r, vy + r], fill=RED)
    save(img, "v5_grid.png")


# ---------- V6 数据流瀑布 ----------
def v6_datastream():
    img, d = canvas()
    draw_text_block(d)
    cols = [(556, [40, 96, 150, 220, 300], RED), (596, [70, 130, 260, 330], TRACE),
            (636, [30, 110, 190, 250, 340], RIM), (676, [60, 170, 230, 310], TRACE),
            (716, [44, 140, 200, 280], RED), (756, [90, 150, 240, 320], TRACE),
            (796, [36, 120, 210, 300, 350], RIM), (836, [70, 180, 270], TRACE),
            (872, [50, 130, 230, 330], RED)]
    for x, ys, color in cols:
        for i, y in enumerate(ys):
            ln = S(14 + (i % 3) * 8)
            d.line([(S(x), S(y)), (S(x), S(y) + ln)], fill=color, width=S(3))
            d.ellipse([S(x) - S(3), S(y) + ln + S(6), S(x) + S(3), S(y) + ln + S(12)], fill=color)
    save(img, "v6_datastream.png")


# ---------- V7 机器人剪影 + 大字叠印 ----------
def v7_overlay():
    img, d = canvas()
    # 先画大号机器人剪影(深色,仅描边)
    cx, top, s = S(660), S(10), S(1.25)

    def R(x): return cx + int(x * s)
    def Y(y): return top + int(y * s)
    ow = max(2, int(2 * s))

    d.line([(R(0), Y(6)), (R(0), Y(34))], fill=RIM, width=ow)
    d.ellipse([R(-8), Y(-2), R(8), Y(14)], outline=RIM, width=ow)
    d.rounded_rectangle([R(-78), Y(34), R(78), Y(142)], radius=int(34*s), outline=RIM, width=ow)
    d.rounded_rectangle([R(-58), Y(56), R(58), Y(120)], radius=int(20*s), outline=TRACE, width=ow)
    for ex in (-28, 28):
        d.ellipse([R(ex-10), Y(78), R(ex+10), Y(98)], fill=RED)
    d.rounded_rectangle([R(-96), Y(162), R(96), Y(316)], radius=int(24*s), outline=RIM, width=ow)
    d.rounded_rectangle([R(-56), Y(184), R(56), Y(258)], radius=int(14*s), outline=TRACE, width=ow)
    # 文字叠印在剪影之上
    d.text((S(56), S(100)), "AI速递", font=font(S(160)), fill=WHITE,
           stroke_width=S(4), stroke_fill=WHITE)
    d.text((S(62), S(58)), "他晓", font=font(S(30)), fill=DIM)
    d.rectangle([S(64), S(300), S(64 + 300), S(306)], fill=RED)
    d.text((S(62), S(322)), "每日精选全球 AI 领域重要动态", font=font(S(24)), fill=DIM)
    save(img, "v7_overlay.png")


# ---------- V8 轨道信号 ----------
def v8_orbit():
    img, d = canvas()
    draw_text_block(d)
    cx, cy, r = S(700), S(195), S(105)
    # 球体:外圆 + 经纬线
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=RIM, width=S(3))
    for ry in (0.25, 0.55, 0.85):
        rr = int(r * ry)
        d.ellipse([cx - r, cy - rr, cx + r, cy + rr], outline=TRACE, width=S(2))
    d.ellipse([cx - int(r * 0.42), cy - r, cx + int(r * 0.42), cy + r], outline=TRACE, width=S(2))
    # 两条倾斜轨道环
    for rr, tilt in ((S(150), S(46)), (S(185), S(60))):
        d.ellipse([cx - rr, cy - tilt, cx + rr, cy + tilt], outline=TRACE, width=S(2))
    # 红色信号点(轨道上)
    for px, py in ((cx + S(138), cy - S(34)), (cx - S(168), cy + S(48))):
        pr = S(7)
        d.ellipse([px - pr, cy * 0 + py - pr, px + pr, py + pr], fill=RED)
        pr2 = S(13)
        d.ellipse([px - pr2, py - pr2, px + pr2, py + pr2], outline=RED, width=S(1))
    save(img, "v8_orbit.png")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "batch2":
        v5_grid(); v6_datastream(); v7_overlay(); v8_orbit()
    else:
        v1_robot()
        v2_chip()
        v3_network()
        v4_typo()
