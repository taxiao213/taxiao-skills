#!/bin/bash
# render.sh <input.html> <output.png> [width] [height]
# 用 headless Chrome 把 HTML 渲染成 PNG，并校验输出尺寸。
# 注意：input/output 必须传绝对路径（内部拼 file://$HTML，相对路径会得到错误页截图）。
set -e

HTML="$1"
OUT="$2"
W="${3:-1920}"
H="${4:-1080}"

if [ -z "$HTML" ] || [ -z "$OUT" ]; then
  echo "用法: render.sh <input.html> <output.png> [width=1920] [height=1080]" >&2
  exit 1
fi

CHROME=""
for c in \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium" \
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"; do
  if [ -x "$c" ]; then CHROME="$c"; break; fi
done

if [ -z "$CHROME" ]; then
  echo "错误: 未找到 Chrome / Chromium / Edge" >&2
  exit 1
fi

"$CHROME" --headless=new --disable-gpu --hide-scrollbars \
  --force-device-scale-factor=1 --window-size="$W,$H" \
  --screenshot="$OUT" "file://$HTML" 2>/dev/null

# 校验输出尺寸是否符合预期
ACTUAL=$(sips -g pixelWidth -g pixelHeight "$OUT" | awk '/pixel/{print $2}' | paste -sdx -)
if [ "$ACTUAL" != "${W}x${H}" ]; then
  echo "警告: 输出尺寸 ${ACTUAL} 与预期 ${W}x${H} 不符" >&2
  exit 2
fi

echo "OK: $OUT (${W}x${H})"
