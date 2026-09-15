#!/usr/bin/env python3
"""从微信公众号推文 HTML 中提取正文文字和内嵌图片，输出到 XHS 工作目录。

用法:
    python3 extract_article.py <推文.html> [输出目录]

输出:
    <输出目录>/article.txt      正文纯文本（供 Claude 阅读改写）
    <输出目录>/images/          按出现顺序提取的图片 img_01.jpg ...
    <输出目录>/qr_scan.txt      二维码检测结果（cv2 可用时自动生成）

依赖: 仅标准库。若安装了 opencv-python (cv2)，额外对每张图做二维码检测。
"""
import base64
import html as html_mod
import os
import re
import sys


def extract_text(content: str) -> str:
    content = re.sub(r'data:image/[^"\']+', '[IMG]', content)
    content = re.sub(r'<script[\s\S]*?</script>', '', content)
    content = re.sub(r'<style[\s\S]*?</style>', '', content)
    text = re.sub(r'<[^>]+>', '\n', content)
    text = html_mod.unescape(text)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    return '\n'.join(lines)


def extract_images(content: str, out_dir: str) -> list[str]:
    matches = re.findall(
        r'data:image/(png|jpeg|jpg|gif|webp);base64,([A-Za-z0-9+/=\s]+?)[\'"]',
        content,
    )
    saved = []
    os.makedirs(out_dir, exist_ok=True)
    for i, (ext, b64) in enumerate(matches, 1):
        try:
            data = base64.b64decode(re.sub(r'\s', '', b64))
        except Exception:
            continue
        ext = 'jpg' if ext in ('jpeg', 'jpg') else ext
        path = os.path.join(out_dir, f'img_{i:02d}.{ext}')
        with open(path, 'wb') as f:
            f.write(data)
        saved.append(path)
    return saved


def scan_qrcodes(image_paths: list[str], out_path: str) -> None:
    """cv2 可用时检测二维码，结果写入 qr_scan.txt；不可用时写提示。"""
    try:
        import cv2  # type: ignore
    except ImportError:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write('未安装 opencv-python，未做二维码自动检测。\n'
                    '请 Claude 逐张阅读图片，人工识别二维码/小程序码并隔离。\n')
        return
    detector = cv2.QRCodeDetector()
    with open(out_path, 'w', encoding='utf-8') as f:
        for p in image_paths:
            img = cv2.imread(p)
            if img is None:
                continue
            data, _, _ = detector.detectAndDecode(img)
            status = f'⚠️ 含二维码: {data[:80]}' if data else 'OK'
            f.write(f'{os.path.basename(p)}: {status}\n')


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(src)), 'XHS')

    with open(src, encoding='utf-8') as f:
        content = f.read()

    os.makedirs(out_dir, exist_ok=True)
    images_dir = os.path.join(out_dir, 'images')

    text = extract_text(content)
    with open(os.path.join(out_dir, 'article.txt'), 'w', encoding='utf-8') as f:
        f.write(text)

    saved = extract_images(content, images_dir)
    scan_qrcodes(saved, os.path.join(out_dir, 'qr_scan.txt'))

    print(f'输出目录: {out_dir}')
    print(f'正文: article.txt ({len(text)} 字)')
    print(f'图片: {len(saved)} 张 -> images/')
    print('二维码检测: qr_scan.txt')


if __name__ == '__main__':
    main()
