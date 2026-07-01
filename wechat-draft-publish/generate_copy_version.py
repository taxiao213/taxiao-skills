#!/usr/bin/env python3
"""
生成图片内嵌版 HTML（用于浏览器复制粘贴到微信公众号）

将 HTML 中的所有本地图片转为 base64 内嵌，生成独立 HTML 文件。
用户只需在浏览器中打开该文件，全选复制，粘贴到微信后台即可。

用法:
    python3 generate_copy_version.py --html "推文.html" --output "推文_复制版.html"
"""

import base64
import io
import os
import re
import argparse
from PIL import Image


def remove_watermark(img: Image.Image) -> Image.Image:
    """去除图片右下角的 AI 水印（裁剪底部35像素）"""
    w, h = img.size
    # 水印位于右下角，高度约30-40像素，裁剪底部35像素可安全去除
    if h > 100:
        return img.crop((0, 0, w, h - 35))
    return img


def embed_images(html_content: str, base_dir: str, max_width: int = 1200, quality: int = 85, remove_wm: bool = True) -> str:
    """将 HTML 中的所有本地图片转为 base64 内嵌（自动去除 AI 水印）"""
    count = 0

    def replace_img(match):
        nonlocal count
        tag = match.group(0)
        src = match.group(1)

        # 跳过已经是 base64 或 http 的图片
        if src.startswith('data:') or src.startswith('http://') or src.startswith('https://'):
            return tag

        full_path = os.path.join(base_dir, src)
        if not os.path.exists(full_path):
            print(f'  跳过（不存在）: {src}')
            return tag

        try:
            img = Image.open(full_path)

            # 去除 AI 水印（裁剪底部35像素）
            if remove_wm:
                img = remove_watermark(img)

            # 转为 RGB
            if img.mode == 'RGBA':
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3])
                img = bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # 限制最大宽度
            if img.width > max_width:
                ratio = max_width / img.width
                img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)

            # 保存为 JPEG
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=quality, optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

            count += 1
            wm_status = "[已去水印] " if remove_wm else ""
            print(f'  [{count}] {wm_status}嵌入: {src} ({len(b64)} chars)')
            return tag.replace(f'src="{src}"', f'src="data:image/jpeg;base64,{b64}"')

        except Exception as e:
            print(f'  错误: {src} - {e}')
            return tag

    html_content = re.sub(r'<img[^>]*?src="([^"]+)"[^>]*?/?>', replace_img, html_content)
    return html_content


def main():
    parser = argparse.ArgumentParser(description='生成图片内嵌版 HTML（用于浏览器复制粘贴到微信）')
    parser.add_argument('--html', required=True, help='原始 HTML 文件路径')
    parser.add_argument('--output', default=None, help='输出文件路径（默认：原文件名_复制版.html）')
    parser.add_argument('--max-width', type=int, default=1200, help='图片最大宽度（默认1200px）')
    parser.add_argument('--quality', type=int, default=85, help='JPEG 质量（默认85）')
    parser.add_argument('--no-watermark-removal', action='store_true', help='禁用自动去水印（默认启用）')
    args = parser.parse_args()

    if not args.output:
        base, ext = os.path.splitext(args.html)
        args.output = f"{base}_复制版{ext}"

    html_path = os.path.abspath(args.html)
    base_dir = os.path.dirname(html_path)

    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    print(f'处理图片中...')
    remove_wm = not args.no_watermark_removal
    if remove_wm:
        print('  自动去水印：已启用（裁剪底部35像素）')
    html = embed_images(html, base_dir, args.max_width, args.quality, remove_wm)

    # 包裹完整 HTML 结构（确保浏览器正确识别 UTF-8 编码）
    full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>公众号推文</title>
<style>
  body {{ margin: 0; padding: 20px 0; background: #f8f9fa; }}
</style>
</head>
<body>
{html}
</body>
</html>"""

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(full_html)

    size_mb = os.path.getsize(args.output) / 1024 / 1024
    print(f'\n生成完成: {args.output}')
    print(f'文件大小: {size_mb:.1f} MB')


if __name__ == '__main__':
    main()
