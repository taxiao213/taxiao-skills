#!/usr/bin/env python3
"""
微信公众号草稿箱发布工具

将本地 HTML 推文文章自动上传图片素材并发布到微信公众号草稿箱。

用法:
    python3 publish_to_draft.py --html "推文.html" --title "文章标题"
    python3 publish_to_draft.py --html "推文.html" --dry-run  # 仅模拟运行

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
import urllib.parse
from pathlib import Path
from html.parser import HTMLParser

# 导入同目录的 HTML 转 WeChat 转换器
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from html_to_wechat import convert_html_to_wechat


class HTMLContentExtractor(HTMLParser):
    """提取 HTML 中的正文内容和图片列表"""

    def __init__(self, body_required=True):
        super().__init__()
        self.title = ""
        self.images = []  # [(src, local_path_or_url)]
        self.body_content = ""
        self._in_title = False
        self._in_body = False
        self._body_depth = 0
        self._body_required = body_required  # 是否需要 <body> 标签才提取图片

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "body":
            self._in_body = True
            self._body_depth = 1
        elif (self._in_body or not self._body_required) and tag == "img":
            src = attrs_dict.get("src", "")
            if src:
                self.images.append(src)
        elif self._in_body:
            self._body_depth += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "body":
            self._in_body = False
        elif self._in_body:
            self._body_depth = max(0, self._body_depth - 1)

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def extract_html_info(html_path: str) -> dict:
    """解析 HTML 文件，提取标题和图片列表"""
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    parser = HTMLContentExtractor()
    parser.feed(content)

    return {
        "title": parser.title.strip(),
        "images": parser.images,
        "content": content,
    }


def extract_html_info_from_string(content: str) -> dict:
    """从 HTML 字符串中提取标题和图片列表（转换后的 HTML 无 <body> 标签）"""
    parser = HTMLContentExtractor(body_required=False)
    parser.feed(content)
    return {
        "title": parser.title.strip(),
        "images": parser.images,
        "content": content,
    }


def resolve_image_path(html_dir: str, src: str) -> str:
    """将 HTML 中的相对路径图片解析为绝对路径"""
    if src.startswith("http://") or src.startswith("https://"):
        return src
    # 相对路径，基于 HTML 文件所在目录
    return os.path.normpath(os.path.join(html_dir, src))


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


def upload_cover_image(token: str, image_path: str) -> str:
    """上传封面图片，返回永久素材 media_id（用作 thumb_media_id）"""
    url = (
        f"https://api.weixin.qq.com/cgi-bin/material/add_material"
        f"?access_token={token}&type=image"
    )
    mime_type = "image/jpeg" if image_path.endswith(".jpg") or image_path.endswith(".jpeg") else "image/png"
    filename = os.path.basename(image_path)

    with open(image_path, "rb") as f:
        file_data = f.read()

    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="{filename}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "media_id" not in data:
        raise Exception(f"上传封面图失败: {data}")
    return data["media_id"]


def upload_content_image(token: str, image_path: str) -> str:
    """上传正文内图片，返回微信图片 URL"""
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
    mime_type = "image/jpeg" if image_path.endswith(".jpg") or image_path.endswith(".jpeg") else "image/png"
    filename = os.path.basename(image_path)

    with open(image_path, "rb") as f:
        file_data = f.read()

    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="{filename}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "url" not in data:
        raise Exception(f"上传正文图片失败: {data}")
    return data["url"]


def replace_images_in_html(content: str, image_map: dict) -> str:
    """替换 HTML 中的图片 src 为微信 URL"""
    for original_src, wechat_url in image_map.items():
        # 处理相对路径和绝对路径的匹配
        escaped_src = re.escape(original_src)
        content = re.sub(
            rf'(src=["\']){escaped_src}(["\'])',
            rf'\g<1>{wechat_url}\g<2>',
            content,
        )
    return content


def add_draft(
    token: str,
    title: str,
    content: str,
    thumb_media_id: str,
    author: str = "",
    digest: str = "",
    source_url: str = "",
) -> str:
    """新增草稿，返回 media_id"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"

    # 自动生成摘要
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


def main():
    parser = argparse.ArgumentParser(description="发布推文到微信公众号草稿箱")
    parser.add_argument("--html", required=True, help="HTML推文文件路径")
    parser.add_argument("--title", default="", help="文章标题（默认取HTML title）")
    parser.add_argument("--author", default="他晓", help="作者名")
    parser.add_argument("--digest", default="", help="文章摘要")
    parser.add_argument("--cover", default="", help="封面图路径（默认取HTML中第一张图片）")
    parser.add_argument("--source-url", default="", help="原文链接")
    parser.add_argument("--appid", default="", help="微信公众号AppID")
    parser.add_argument("--secret", default="", help="微信公众号AppSecret")
    parser.add_argument("--dry-run", action="store_true", help="仅模拟运行，不调用API")
    args = parser.parse_args()

    # 读取配置
    appid = args.appid or os.environ.get("WECHAT_APP_ID", "")
    secret = args.secret or os.environ.get("WECHAT_APP_SECRET", "")

    if not args.dry_run and (not appid or not secret):
        # 尝试读取 .env 文件
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
            print("  方式1: --appid 和 --secret 参数")
            print("  方式2: WECHAT_APP_ID 和 WECHAT_APP_SECRET 环境变量")
            print("  方式3: HTML 同目录下的 .env 文件")
            sys.exit(1)

    # Step 1: 解析 HTML
    print(f"[1/6] 解析 HTML 文件: {args.html}")
    html_info = extract_html_info(args.html)
    title = args.title or html_info["title"]
    html_dir = str(Path(args.html).parent)
    images = html_info["images"]
    print(f"  标题: {title}")
    print(f"  发现 {len(images)} 张图片")

    if not images:
        print("  警告：未在 HTML 中发现图片，请确认封面图路径")

    # 确定封面图（跳过装饰性图片：header_deco、footer_deco、avatar、qrcode）
    cover_path = args.cover
    if not cover_path and images:
        skip_patterns = ("header_deco", "footer_deco", "avatar", "qrcode")
        for img_src in images:
            if any(p in img_src for p in skip_patterns):
                continue
            if not img_src.startswith("http"):
                cover_path = resolve_image_path(html_dir, img_src)
                break

    # Step 2: HTML 转 WeChat 内联样式
    print(f"[2/6] 转换 HTML 为 WeChat 内联样式...")
    raw_content = html_info["content"]
    wechat_content = convert_html_to_wechat(raw_content)
    # 重新从转换后的内容中提取图片（转换器保留了 img src）
    wechat_info = extract_html_info_from_string(wechat_content)
    images = wechat_info["images"]
    print(f"  转换完成，输出 {len(wechat_content)} 字符")
    print(f"  转换后图片数: {len(images)}")

    if args.dry_run:
        print("\n=== DRY RUN 模拟 ===")
        print(f"  标题: {title}")
        print(f"  作者: {args.author}")
        print(f"  封面图: {cover_path or '(未指定)'}")
        print(f"  正文图片数: {len(images)}")
        for i, img in enumerate(images):
            local = resolve_image_path(html_dir, img) if not img.startswith("http") else img
            print(f"    [{i+1}] {img} -> {local}")
        print(f"  AppID: {appid[:8]}..." if appid else "  AppID: (未配置)")
        # 输出转换后 HTML 预览（前500字符）
        print(f"\n--- 转换后 HTML 预览（前500字）---")
        print(wechat_content[:500])
        print("--- 预览结束 ---")
        print("======================")
        print("\nDRY RUN 完成，未调用任何API。")
        return

    # Step 3: 获取 access_token
    print(f"[3/6] 获取 access_token...")
    token = get_access_token(appid, secret)
    print(f"  Token 获取成功: {token[:16]}...")

    # Step 3: 上传封面图
    print(f"[4/6] 上传封面图...")
    if cover_path and os.path.exists(cover_path):
        thumb_media_id = upload_cover_image(token, cover_path)
        print(f"  封面图上传成功, media_id: {thumb_media_id[:20]}...")
    else:
        print(f"  错误：封面图不存在: {cover_path}")
        sys.exit(1)

    # Step 4: 上传正文图片并替换 URL
    print(f"[5/6] 上传正文图片...")
    content = wechat_content
    image_map = {}  # original_src -> wechat_url
    for i, img_src in enumerate(images):
        # 跳过外部URL（如header_deco、footer_deco等装饰图可保留）
        if img_src.startswith("http"):
            print(f"  [{i+1}] 跳过外部URL: {img_src[:60]}...")
            continue

        local_path = resolve_image_path(html_dir, img_src)
        if not os.path.exists(local_path):
            print(f"  [{i+1}] 跳过（文件不存在）: {local_path}")
            continue

        try:
            wechat_url = upload_content_image(token, local_path)
            image_map[img_src] = wechat_url
            print(f"  [{i+1}] 上传成功: {os.path.basename(local_path)} -> {wechat_url[:50]}...")
        except Exception as e:
            print(f"  [{i+1}] 上传失败: {local_path} - {e}")

    if image_map:
        content = replace_images_in_html(content, image_map)
        print(f"  共替换 {len(image_map)} 张图片")
    else:
        print("  未替换任何图片（请检查图片路径是否正确）")

    # Step 5: 新增草稿
    print(f"[6/6] 发布到草稿箱...")
    media_id = add_draft(
        token=token,
        title=title,
        content=content,
        thumb_media_id=thumb_media_id,
        author=args.author,
        digest=args.digest,
        source_url=args.source_url,
    )
    print(f"\n发布成功!")
    print(f"  草稿 media_id: {media_id}")
    print(f"  请前往微信公众号后台 → 草稿箱 查看")

    # 自动保存图片映射文件，供后续 update_draft.py 使用
    if image_map or thumb_media_id:
        map_data = {
            "_说明": "此文件由 publish_to_draft.py 自动生成，供 update_draft.py 更新样式时使用",
            "thumb_media_id": thumb_media_id,
            "image_map": image_map,
        }
        map_path = str(Path(args.html)) + ".map.json"
        with open(map_path, "w", encoding="utf-8") as f:
            json.dump(map_data, f, ensure_ascii=False, indent=2)
        print(f"  图片映射已保存: {map_path}")
        print(f"  后续修改样式后，可用 update_draft.py 快速更新（无需重新上传图片）")


if __name__ == "__main__":
    main()
