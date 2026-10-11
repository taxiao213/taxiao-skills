#!/usr/bin/env python3
# excalidraw-board-gen.py — 「他晓」板书 .excalidraw 生成器模板
#
# 用法：复制本文件到一边改一边跑（one-off 生成器，产出入库，脚本本身可不留）。
#   python3 excalidraw-board-gen.py
# 内置：① 元素 helper（text/rect/arrow/line）② 文本宽度估算 ③ 矩形溢出自检
#       ④ 近似布局预览（生成 HTML，用 fresh-cover/scripts/render.sh 截图肉眼核对）
#
# 样式约定（勿改，与 EP1~EP3 板书一致）：
#   红 #DF6B4F=问题/反例  绿 #3E9E5F=做法  灰 #6B7B6F/#7A8B7D=结构  深绿灰 #25372B=正文
#   填充 #FBEBE4/#E4F2E4/#EDEBE2  底 #F6F4EC
#   fontFamily 5（Excalifont） roughness 1  strokeWidth 2
import json
import os

E = []
_counter = [0]

# ── 样式常量 ──────────────────────────────────────────────
DARK, RED, GREEN = "#25372B", "#DF6B4F", "#3E9E5F"
GRAY, GRAY2 = "#6B7B6F", "#7A8B7D"
RED_BG, GREEN_BG, GRAY_BG = "#FBEBE4", "#E4F2E4", "#EDEBE2"
BG = "#F6F4EC"

OUT_PATH = "板书.excalidraw"  # ← 改成目标路径，如 docs/2026/MMDD/excalidraw/<主题>-板书.excalidraw


# ── 元素 helper ───────────────────────────────────────────
def base(eid, etype, x, y, w, h, stroke, bg="transparent", sw=2, ss="solid",
         rough=1, opacity=100, roundness=None):
    _counter[0] += 1
    n = _counter[0]
    return {
        "id": eid, "type": etype, "x": x, "y": y, "width": w, "height": h,
        "angle": 0, "strokeColor": stroke, "backgroundColor": bg,
        "fillStyle": "solid", "strokeWidth": sw, "strokeStyle": ss,
        "roughness": rough, "opacity": opacity, "groupIds": [], "frameId": None,
        "roundness": roundness, "seed": 1000 + n, "version": 1,
        "versionNonce": 202600000 + n, "isDeleted": False, "boundElements": [],
        "updated": 1789632000000, "link": None, "locked": False,
        "index": "a%X" % n,
    }


def text_w(t, fs):
    """宽度估算：CJK ≈ fs，ASCII ≈ 0.58fs（Excalifont 近似，autoResize 会兜底）"""
    return round(sum(fs if ord(c) > 0x2E80 else fs * 0.58 for c in t))


def text(eid, t, x, y, fs, color, align="left"):
    lines = t.split("\n")
    w = max(text_w(l, fs) for l in lines)
    h = round(fs * 1.25 * len(lines))
    e = base(eid, "text", x, y, w, h, color)
    e.update({
        "text": t, "originalText": t, "fontSize": fs, "fontFamily": 5,
        "textAlign": align, "verticalAlign": "top", "containerId": None,
        "baseline": round(fs * 0.9), "lineHeight": 1.25, "autoResize": True,
    })
    E.append(e)
    return e


def rect(eid, x, y, w, h, stroke, bg, ss="solid", sw=2):
    e = base(eid, "rectangle", x, y, w, h, stroke, bg, sw=sw, ss=ss,
             roundness={"type": 3})
    E.append(e)
    return e


def _pts_elem(eid, etype, x1, y1, x2, y2, color, ss, sw):
    e = base(eid, etype, x1, y1, abs(x2 - x1), abs(y2 - y1), color, ss=ss, sw=sw,
             roundness={"type": 2})
    e.update({
        "points": [[0, 0], [x2 - x1, y2 - y1]],
        "lastCommittedPoint": None, "startBinding": None, "endBinding": None,
        "startArrowhead": None,
        "endArrowhead": "arrow" if etype == "arrow" else None,
        "polygon": False,
    })
    E.append(e)
    return e


def arrow(eid, x1, y1, x2, y2, color=GRAY2, ss="solid", sw=2):
    return _pts_elem(eid, "arrow", x1, y1, x2, y2, color, ss, sw)


def line(eid, x1, y1, x2, y2, color=RED, sw=4):
    """手绘删除线：斜压标题否定词"""
    return _pts_elem(eid, "line", x1, y1, x2, y2, color, "solid", sw)


# ── 板书内容（按板书大纲排坐标，y 向下增长）────────────────
def build():
    # 示例骨架，照 EP3 改：
    text("t1", "主题 ≠", 80, 60, 56, DARK)
    text("t2", "误区", 330, 60, 56, RED)
    line("strike", 324, 100, 448, 92, RED)          # 删除线压「误区」
    text("t3", "，是正解", 462, 60, 56, DARK)
    text("t4", "一句钩子", 80, 152, 30, RED)
    # ... 按段落继续：rect + text + arrow ...
    raise SystemExit("把 build() 换成本期内容再跑")


# ── 自检与输出 ────────────────────────────────────────────
def selfcheck(pairs):
    byid = {e["id"]: e for e in E}
    ok = True
    for tid, rid in pairs:
        t, r = byid[tid], byid[rid]
        if not (t["x"] >= r["x"] - 8 and t["y"] >= r["y"] - 8
                and t["x"] + t["width"] <= r["x"] + r["width"] + 8
                and t["y"] + t["height"] <= r["y"] + r["height"] + 8):
            print("OVERFLOW:", tid, "in", rid)
            ok = False
    print("self-check:", "OK" if ok else "FAILED")
    return ok


def write_doc():
    doc = {
        "type": "excalidraw", "version": 2, "source": "http://localhost:3001",
        "elements": E,
        "appState": {
            "gridSize": None, "gridStep": 5, "gridModeEnabled": False,
            "viewBackgroundColor": BG, "lockedMultiSelections": {},
        },
        "files": {},
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    json.dump(doc, open(OUT_PATH, "w"), ensure_ascii=False, indent=1)
    print("written:", OUT_PATH, "elements:", len(E))


def preview_html(path="/tmp/board-preview.html"):
    """近似布局预览（非手绘风格，仅核对位置/遮挡）：
    fresh-cover/scripts/render.sh /tmp/board-preview.html /tmp/board-preview.png <W> <H>"""
    import html as h
    maxx = max(e["x"] + e["width"] for e in E) + 80
    maxy = max(e["y"] + e["height"] for e in E) + 80
    parts = []
    for e in E:
        if e["isDeleted"]:
            continue
        x, y, w, hh = e["x"], e["y"], e["width"], e["height"]
        if e["type"] == "rectangle":
            dash = "dashed" if e["strokeStyle"] == "dashed" else "solid"
            parts.append(f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{hh}px;border:2px {dash} {e["strokeColor"]};background:{e["backgroundColor"]};border-radius:14px"></div>')
        elif e["type"] == "text":
            parts.append(f'<div style="position:absolute;left:{x}px;top:{y}px;font-size:{e["fontSize"]}px;color:{e["strokeColor"]};font-weight:600;white-space:pre;line-height:1.25">{h.escape(e["text"])}</div>')
        elif e["type"] in ("arrow", "line"):
            (ax, ay), (bx, by) = (x + e["points"][0][0], y + e["points"][0][1]), (x + e["points"][-1][0], y + e["points"][-1][1])
            dash = 'stroke-dasharray="8"' if e["strokeStyle"] == "dashed" else ""
            parts.append(f'<svg style="position:absolute;left:0;top:0;overflow:visible" width="{maxx}" height="{maxy}"><line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" stroke="{e["strokeColor"]}" stroke-width="{e["strokeWidth"]}" {dash}/></svg>')
    page = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><style>html,body{{width:{maxx}px;height:{maxy}px;margin:0;background:{BG};font-family:-apple-system,"PingFang SC",sans-serif}}</style></head><body>{"".join(parts)}</body></html>'
    open(path, "w").write(page)
    print("preview:", path, f"({maxx}x{maxy})")


if __name__ == "__main__":
    build()
    # selfcheck([("t1 所在框 id", "框 id"), ...])
    write_doc()
    preview_html()
