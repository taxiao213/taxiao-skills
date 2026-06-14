#!/usr/bin/env python3
"""
微信公众号草稿箱更新工具（仅更新样式/内容，不重新上传图片）

适用场景：文章样式调整、文字修改、排版优化，图片不变。

用法:
    # 基本用法：指定 HTML 和图片映射文件
    python3 update_draft.py --html "推文.html" --media-id "草稿media_id"

    # 图片映射文件格式（JSON）：
    # {
    #   "thumb_media_id": "封面图的永久素材media_id",
    #   "image_map": {
    #     "本地相对路径或文件名": "微信图片URL",
    #     "cover.jpg": "https://mmbiz.qpic.cn/xxx/640",
    #     "assets/img_ecosystem.jpg": "https://mmbiz.qpic.cn/yyy/640"
    #   }
    # }

    # 首次使用时自动生成图片映射模板
    python3 update_draft.py --html "推文.html" --gen-map

环境变量:
    WECHAT_APP_ID      微信公众号 AppID
    WECHAT_APP_SECRET  微信公众号 AppSecret
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from html.parser import HTMLParser

# 导入同目录的 HTML 转 WeChat 转换器
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from html_to_wechat import convert_html_to_wechat


# ============================================================
# 复用 publish_to_draft.py 中的工具函数
# ============================================================

class HTMLContentExtractor(HTMLParser):
    """提取 HTML 中的标题和图片列表"""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.images = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "img":
            src = attrs_dict.get("src", "")
            if src:
                self.images.append(src)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def get_access_token(appid: str, secret: str) -> str:
    """获取微信公众号 access_token"""
    url = (
        f"https://api.weixin.qq.com/cgi-bin/token"
        f"?grant_type=client_credential&appid={appid}&secret={secret}"
    )
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "access_token" not in data:
        raise Exception(f"获取 access_token 失败: {data}")
    return data["access_token"]


def add_draft(token, title, content, thumb_media_id, author="", digest="", source_url=""):
    """新增草稿，返回 media_id"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"

    if not digest:
        text_only = re.sub(r"<[^>]+>", "", content)
        digest = text_only[:54].strip()

    payload = {
        "articles": [
            {
                "article_type": "news",
                "title": title[:32],
                "author": author[:16] if author else "",
                "digest": digest[:128],
                "content": content,
                "content_source_url": source_url,
                "thumb_media_id": thumb_media_id,
                "need_open_comment": 0,
                "only_fans_can_comment": 0,
            }
        ]
    }

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "media_id" not in data:
        raise Exception(f"新增草稿失败: {data}")
    return data["media_id"]


def replace_images_in_html(content: str, image_map: dict) -> str:
    """替换 HTML 中的图片 src 为微信 URL"""
    for original_src, wechat_url in image_map.items():
        escaped_src = re.escape(original_src)
        content = re.sub(
            rf'(src=["\']){escaped_src}(["\'])',
            rf'\g<1>{wechat_url}\g<2>',
            content,
        )
    return content


def generate_image_map(html_path: str, output_path: str):
    """从 HTML 中提取图片列表，生成映射模板文件"""
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    parser = HTMLContentExtractor()
    parser.feed(content)

    template = {
        "_说明": "将每张图片的本地路径映射到微信图片URL（首次发布时由publish_to_draft.py生成）",
        "thumb_media_id": "在这里填入封面图的永久素材media_id",
        "image_map": {}
    }

    for img_src in parser.images:
        if not img_src.startswith("http"):
            template["image_map"][img_src] = f"https://mmbiz.qpic.cn/...（填入微信URL）"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(template, f, ensure_ascii=False, indent=2)

    print(f"图片映射模板已生成: {output_path}")
    print(f"  共 {len(parser.images)} 张图片需要映射")
    print(f"  请填写每张图片对应的微信URL后再次运行")


def main():
    parser = argparse.ArgumentParser(description="更新草稿（仅样式/内容，不上传图片）")
    parser.add_argument("--html", required=True, help="HTML推文文件路径")
    parser.add_argument("--map", default="", help="图片映射JSON文件路径（默认与HTML同名.map.json）")
    parser.add_argument("--media-id", default="", help="已有草稿的media_id（用于参考，实际会创建新草稿）")
    parser.add_argument("--title", default="", help="文章标题（默认取HTML title）")
    parser.add_argument("--author", default="他晓", help="作者名")
    parser.add_argument("--digest", default="", help="文章摘要")
    parser.add_argument("--source-url", default="", help="原文链接")
    parser.add_argument("--appid", default="", help="微信公众号AppID")
    parser.add_argument("--secret", default="", help="微信公众号AppSecret")
    parser.add_argument("--gen-map", action="store_true", help="仅生成图片映射模板文件")
    parser.add_argument("--dry-run", action="store_true", help="仅模拟运行，不调用API")
    args = parser.parse_args()

    # 读取配置
    appid = args.appid or os.environ.get("WECHAT_APP_ID", "")
    secret = args.secret or os.environ.get("WECHAT_APP_SECRET", "")

    if not args.gen_map and not args.dry_run and (not appid or not secret):
        env_path = Path(args.html).parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().strip().split("\n"):
                if "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == "WECHAT_APP_ID":
                        appid = v.strip()
                    elif k.strip() == "WECHAT_APP_SECRET":
                        secret = v.strip()
        if not appid or not secret:
            print("错误：请提供微信公众号 AppID 和 AppSecret")
            sys.exit(1)

    html_path = Path(args.html)
    html_dir = str(html_path.parent)

    # 确定映射文件路径
    map_path = args.map
    if not map_path:
        map_path = str(html_path) + ".map.json"

    # Step 1: 解析 HTML
    print(f"[1/4] 解析 HTML 文件: {args.html}")
    with open(args.html, "r", encoding="utf-8") as f:
        raw_content = f.read()

    parser = HTMLContentExtractor()
    parser.feed(raw_content)
    title = args.title or parser.title.strip()
    print(f"  标题: {title}")
    print(f"  发现 {len(parser.images)} 张图片")

    # 生成映射模板模式
    if args.gen_map:
        generate_image_map(args.html, map_path)
        return

    # Step 2: 加载图片映射
    print(f"[2/4] 加载图片映射: {map_path}")
    if not os.path.exists(map_path):
        print(f"  错误：图片映射文件不存在: {map_path}")
        print(f"  请先运行 --gen-map 生成模板，或使用 --map 指定路径")
        print(f"\n  提示：首次发布文章时，publish_to_draft.py 会自动生成映射文件")
        sys.exit(1)

    with open(map_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    thumb_media_id = mapping.get("thumb_media_id", "")
    image_map = mapping.get("image_map", {})

    if not thumb_media_id:
        print("  错误：映射文件中缺少 thumb_media_id")
        sys.exit(1)

    print(f"  封面 media_id: {thumb_media_id[:20]}...")
    print(f"  已映射图片: {len(image_map)} 张")

    # 检查是否有未映射的图片
    unmapped = []
    for img_src in parser.images:
        if not img_src.startswith("http") and img_src not in image_map:
            unmapped.append(img_src)
    if unmapped:
        print(f"  警告：{len(unmapped)} 张图片未映射:")
        for src in unmapped:
            print(f"    - {src}")
        print("  这些图片将保留原始路径（可能在微信中无法显示）")

    # Step 3: HTML 转 WeChat 内联样式 + 替换图片 URL
    print(f"[3/4] 转换 HTML 为 WeChat 内联样式...")
    wechat_content = convert_html_to_wechat(raw_content)
    print(f"  转换完成，输出 {len(wechat_content)} 字符")

    # 替换图片 URL
    if image_map:
        wechat_content = replace_images_in_html(wechat_content, image_map)
        print(f"  已替换 {len(image_map)} 张图片为微信URL")

    if args.dry_run:
        print("\n=== DRY RUN 模拟 ===")
        print(f"  标题: {title}")
        print(f"  作者: {args.author}")
        print(f"  封面 media_id: {thumb_media_id[:20]}...")
        print(f"  图片映射: {len(image_map)} 张")
        print(f"  内容大小: {len(wechat_content)} 字符")
        print(f"\n--- 转换后 HTML 预览（前500字）---")
        print(wechat_content[:500])
        print("--- 预览结束 ---")
        print("======================")
        print("\nDRY RUN 完成，未调用任何API。")
        return

    # Step 4: 新增草稿
    print(f"[4/4] 发布到草稿箱...")
    token = get_access_token(appid, secret)
    print(f"  Token 获取成功: {token[:16]}...")

    media_id = add_draft(
        token=token,
        title=title,
        content=wechat_content,
        thumb_media_id=thumb_media_id,
        author=args.author,
        digest=args.digest,
        source_url=args.source_url,
    )
    print(f"\n发布成功!")
    print(f"  草稿 media_id: {media_id}")
    print(f"  请前往微信公众号后台 → 草稿箱 查看")
    print(f"  （旧草稿如需删除，请手动在后台操作）")


if __name__ == "__main__":
    main()
