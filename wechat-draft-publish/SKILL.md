---
name: "wechat-draft-publish"
description: "将本地HTML推文文章发布到微信公众号草稿箱。当用户要求将文章推送到微信公众号、发布到草稿箱、自动发布公众号文章时调用此技能。"
---

# 微信公众号草稿箱发布技能

将本地 taxiao-wechat-v3 模板生成的 HTML 推文文章，自动上传图片素材并发布到微信公众号草稿箱。

## 前置条件

1. **微信公众号**（服务号或订阅号均可）
2. **公众号后台已配置 IP 白名单**（调用API的服务器IP必须在白名单内）
3. **AppID 和 AppSecret**（公众号后台 → 开发 → 基本配置）
4. **Python 3.8+**，安装依赖：`pip install requests beautifulsoup4`
5. **环境变量配置**（任选一种方式）：
   - 创建 `.env` 文件：
     ```
     WECHAT_APP_ID=your_appid
     WECHAT_APP_SECRET=your_secret
     ```
   - 或设置系统环境变量

## 核心流程

```
解析 HTML 文件
    ↓
HTML 转 WeChat 内联样式（关键步骤！）
  - 微信公众号会剥离 <style> 标签中的所有 CSS
  - 必须将 CSS 类样式转为每个元素的内联 style 属性
  - 调用 html_to_wechat.py 转换器完成
    ↓
获取 access_token
    ↓
上传封面图片 → 获取 thumb_media_id（永久素材）
    ↓
逐张上传正文图片 → 获取微信图片 URL
    ↓
替换 HTML 中的图片 src 为微信 URL
    ↓
调用 draft/add 接口 → 文章进入草稿箱
```

### 关键：为什么需要 HTML 转 WeChat 内联样式？

微信公众号 API 路径（`draft/add`）对 HTML 有**严格的三轮清洗**：
1. 移除 `<script>`、`<style>`、`<iframe>` 等危险标签
2. 过滤大部分 CSS 属性，只保留白名单内的 `style` 属性
3. 移动端预览时进一步简化

如果直接推送原始 HTML，所有样式都会丢失，文章变成纯文本。

#### 微信 API 路径支持的样式属性（基于2026年反向解析验证）

| 类别 | 支持的属性 |
|------|-----------|
| 文字 | `color`, `font-size`, `font-weight`, `font-family`, `line-height`, `text-align`, `text-decoration`, `letter-spacing` |
| 盒模型 | `margin`, `padding`, `background`, `background-color`, `width`, `height` |
| 边框 | `border`, `border-left`, `border-radius` |
| **不支持的属性** | `display: flex/grid`, `box-shadow`, `grid-template-columns`, `position`, `float` 等 |

#### 转换器核心策略（v5 table布局版）

`html_to_wechat.py` 转换器自动完成以下转换：

**CSS 解析与匹配：**
- 解析 `<style>` 中的全部 CSS 规则，精确匹配到对应元素
- 将 CSS 变量（`var(--blue-primary)` 等）替换为实际颜色值
- 跳过 `@media` 响应式规则

**标签转换：**
- 使用 `<section>` 代替 `<div>`——微信编辑器原生使用 `<section>` 作为容器
- 移除 `<style>`、`<head>`、`<body>` 等标签
- 修复自闭合标签（`<br />`、`<img ... />`）

**布局转换（核心改进）：**
- **`grid` 布局 → `<table>`**：`card-grid`、`stat-grid` 等网格容器转换为 `<table>`，子元素转换为 `<td>`，自动计算列宽（`width:50%` 或 `width:33%`）
- **`flex` 行布局 → `<table><tr>`**：`tool-item`、`brand-row`、`qr-pair` 等弹性行容器转换为 `<table><tr>`，子元素转换为 `<td>`
- 3列 grid 自动在每3个 `<td>` 后插入 `</tr><tr>` 换行

**样式过滤：**
- 移除微信 API 路径不支持的属性：`display: flex/grid`、`box-shadow`、`grid-template-columns`、`gap`、`flex-*`、`align-items`、`justify-content` 等
- 只保留白名单属性：`color`、`font-size`、`margin`、`padding`、`background`、`border`、`border-radius`、`width`、`text-align` 等

**为什么用 `<table>` 而不是图片？**
- `<table>` 在微信中完全支持，文字可选中、可搜索
- 图片方案虽然更精确，但文字不可选中、不可复制、加载更慢
- `<table>` 方案在排版精度和可用性之间取得了最佳平衡

## 使用方式

当用户要求发布文章到微信公众号草稿箱时，执行以下步骤：

### Step 1：确认参数

从用户处获取或确认以下信息：
- **HTML 文件路径**：要发布的推文 HTML 文件
- **文章标题**：草稿标题（不超过32字），默认取 HTML 的 `<title>` 标签内容
- **作者**：作者名（不超过16字），默认"他晓"
- **摘要**：文章摘要（不超过128字），默认取正文前54字

### Step 2：运行发布脚本

使用工作目录中的发布脚本：

```bash
python3 /sessions/69e9523781c4767c3eaa9c12/workspace/.trae/skills/wechat-draft-publish/publish_to_draft.py \
  --html "HTML文件路径" \
  --title "文章标题" \
  --author "作者名" \
  --digest "文章摘要"
```

参数说明：
| 参数 | 必填 | 说明 |
|------|------|------|
| `--html` | 是 | HTML推文文件路径 |
| `--title` | 否 | 文章标题，默认取HTML title标签 |
| `--author` | 否 | 作者名，默认"他晓" |
| `--digest` | 否 | 摘要，默认取正文前54字 |
| `--cover` | 否 | 封面图路径，默认取HTML中第一张图片 |
| `--appid` | 否 | 微信公众号AppID，默认读环境变量 |
| `--secret` | 否 | 微信公众号AppSecret，默认读环境变量 |
| `--dry-run` | 否 | 仅模拟运行，不实际调用API |

### Step 3：验证结果

脚本成功后会输出 `media_id`，可在公众号后台 → 草稿箱中查看。
首次发布时会自动生成 `.map.json` 图片映射文件，供后续更新使用。

## 仅更新样式（不上传图片）

当只修改了文章样式或文字内容、图片不变时，使用 `update_draft.py` 快速更新：

```bash
# 自动使用同名 .map.json 映射文件
python3 update_draft.py --html "推文.html"

# 指定映射文件路径
python3 update_draft.py --html "推文.html" --map "其他映射.json"

# 仅模拟运行
python3 update_draft.py --html "推文.html" --dry-run
```

**图片映射文件**（`.map.json`）由 `publish_to_draft.py` 首次发布时自动生成，格式：
```json
{
  "thumb_media_id": "封面图的永久素材media_id",
  "image_map": {
    "cover.jpg": "https://mmbiz.qpic.cn/xxx/640",
    "assets/img_ecosystem.jpg": "https://mmbiz.qpic.cn/yyy/640"
  }
}
```

如果映射文件不存在，可先用 `--gen-map` 生成模板：
```bash
python3 update_draft.py --html "推文.html" --gen-map
```

## 推荐方案：浏览器复制粘贴（排版保真度最高）

微信 API 路径（`draft/add`）对 HTML 有严格的三轮清洗，会过滤大量 CSS 属性。而通过**浏览器渲染后复制粘贴**到微信后台，排版保真度远高于 API 推送——这就是 135 编辑器的核心原理。

### 操作流程（两步转换）

**重要**：不能直接渲染原始 HTML 复制！微信编辑器粘贴时**也会剥离 `<style>` 标签**，必须先将 CSS 转为内联样式。

```
Step 1: html_to_copy.py  — CSS 转内联样式（保留全部 CSS 属性）
Step 2: generate_copy_version.py  — 图片嵌入 base64 + 包裹完整 HTML
Step 3: 浏览器打开 → Ctrl+A 全选 → Ctrl+C 复制 → 微信后台 Ctrl+V 粘贴
```

### Step 1：CSS 转内联样式

```bash
python3 /sessions/69e9523781c4767c3eaa9c12/workspace/.trae/skills/wechat-draft-publish/html_to_copy.py \
  "推文.html" -o "推文_内联版.html"
```

`html_to_copy.py` 与 `html_to_wechat.py`（API版）的关键区别：

| 维度 | html_to_copy.py（复制粘贴版） | html_to_wechat.py（API版） |
|------|---------------------------|--------------------------|
| CSS 属性保留 | **保留全部**（flex, grid, box-shadow 等） | 严格过滤，只保留白名单 |
| 布局转换 | 不转换（保留 flex/grid） | grid→table, flex→table |
| div 处理 | 转为 `<section>` | 转为 `<section>` |
| CSS 变量 | 解析为实际值 | 解析为实际值 |
| 伪类支持 | 支持 `:last-child`, `:first-child`, `:nth-child()` | 不支持（建议用 class 替代） |

### Step 2：图片嵌入 base64

```bash
python3 /sessions/69e9523781c4767c3eaa9c12/workspace/.trae/skills/wechat-draft-publish/generate_copy_version.py \
  --html "推文_内联版.html" \
  --output "推文_复制粘贴版.html"
```

该脚本会：
- 将所有图片压缩到 1200px 宽度（节省体积）
- 转为 JPEG 格式（质量 85%）
- 内嵌为 base64 编码（无需外部图片依赖）
- **自动包裹完整 HTML 结构**（含 `<meta charset="utf-8">`，确保中文正确显示）
- 输出独立 HTML 文件，可直接在浏览器中打开

### 为什么复制粘贴比 API 推送效果好？

| 维度 | API 推送（draft/add） | 浏览器复制粘贴 |
|------|---------------------|---------------|
| CSS 属性保留 | 严格过滤，只保留白名单 | 大部分保留（利用富文本剪贴板） |
| `<section>` 标签 | 保留 | 保留 |
| `<div>` 标签 | 可能被转为 `<p>` | 保留 |
| `display: flex/grid` | 被过滤 | **保留** |
| `box-shadow` | 被过滤 | **保留** |
| `border-radius` | 部分保留 | **保留** |
| 图片 | 必须是微信 CDN URL | base64 或本地图片均可 |
| 自动化程度 | 全自动 | 需手动复制粘贴 |

**重要提醒**：复制粘贴路径虽然保留更多 CSS，但微信编辑器仍会剥离外层容器的 `padding`（如 `.wrapper` 上的左右边距）。因此边距必须直接写在每个正文元素上，参见上方"HTML 模板编写注意事项"第4条。

### HTML 模板编写注意事项

为确保复制粘贴后排版正确，编写 HTML 模板时需注意：

1. **避免依赖 `:last-child` 等伪类**：`html_to_copy.py` 虽然支持伪类匹配，但更可靠的方式是给最后一个元素添加特殊 class（如 `tool-item-last`），同时保留 `:last-child` 选择器作为兼容
2. **层级间距用显式分隔 div**：对于列表类布局（如 tool-list），建议在层级之间插入 `<div style="height:16px;"></div>` 作为间距，比依赖 `margin-bottom` 更可靠
3. **`<style>` 标签中的 CSS 会被剥离**：所有样式必须能通过 CSS 选择器匹配到元素，转换器会自动内联化
4. **边距必须写在元素自身上**：外层容器的 `padding`（如 `.wrapper { padding: 0 32px; }`）在微信编辑器粘贴时可能被剥离。务必将边距直接写在正文元素上：
   - 正文段落 `.content-text`：`padding: 0 16px`
   - 小节标题 `.section-title`：`padding-left: 30px`（配合 `border-left` 使用）
   - 引用框/卡片 `.callout`、`.tool-list`、`.summary-box`、`.quote-box`：`margin: 16px 16px` 或 `padding: 20px 18px 20px 34px`
   - 图片 `.img-placeholder`：保持 `width: 100%; margin: 16px 0;`，不额外加左右 margin，让图片自然撑满容器
5. **禁止使用 CSS 伪元素（`::before`、`::after`）**：`html_to_copy.py` 会将伪元素的样式（如 `content:''`、`position:absolute`）错误地转换成浮动的 `<section>` 标签，导致页面出现乱码或布局错乱。所有视觉效果必须用实际 HTML 元素实现：
   - ❌ 错误：`.timeline-item::before { content:''; position:absolute; ... }` 用伪元素画圆点/线条
   - ✅ 正确：用 flex 布局 + 实际 `<div>` 元素作为圆点（`border-radius:50%`）和连接线（`width:2px; flex:1`）
   - ❌ 错误：用 `::before` 画装饰性边框、箭头、图标等
   - ✅ 正确：用实际的 `<span>`、`<div>` 或 Unicode 字符（如 ▶、●、→）替代
6. **AI 生成图片必须去除水印**：使用 `GenerateImage` 工具生成的图片默认带有 "TRAE AI 生成" 水印，发布前必须用 Pillow 脚本去除。水印位于图片右下角，可通过裁剪或覆盖方式移除。建议在 `generate_copy_version.py` 中集成水印去除逻辑，或在图片生成后单独处理

## 脚本清单

| 脚本 | 用途 |
|------|------|
| `publish_to_draft.py` | API 推送：上传图片 + 转换样式 + 推送草稿 |
| `update_draft.py` | 样式更新：仅转换样式 + 推送草稿（复用已有图片URL） |
| `html_to_wechat.py` | HTML 转 WeChat 内联样式 — API 版（过滤不支持的 CSS，grid/flex→table） |
| `html_to_copy.py` | HTML 转 WeChat 内联样式 — 复制粘贴版（保留全部 CSS，用于浏览器复制流程） |
| `generate_copy_version.py` | 图片嵌入 base64 + 包裹完整 HTML（复制粘贴流程的第二步） |

## 关键 API 接口

### 1. 获取 access_token
```
GET https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={SECRET}
```

### 2. 上传封面图（永久素材）
```
POST https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={TOKEN}&type=image
```
- 返回 `media_id`，用作 `thumb_media_id`
- 使用 multipart/form-data 格式

### 3. 上传正文图片
```
POST https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={TOKEN}
```
- 返回微信图片 `url`，替换 HTML 中的 src

### 4. 新增草稿
```
POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token={TOKEN}
```
- Body 为 JSON，articles 数组
- content 中的图片必须是微信URL，外部链接会被过滤

## 重要注意事项

1. **图片限制**：content 中的图片 URL 必须来自微信 `media/uploadimg` 接口，外部链接会被过滤
2. **content 大小**：不超过 2 万字符，小于 1MB
3. **Unicode 编码**：title、author 等字段不要使用 `\uXXXX` 转义，直接传中文字符串（`ensure_ascii=False`）
4. **thumb_media_id 必须是永久素材 ID**：通过 `material/add_material` 获取，临时素材 ID 不可用
5. **IP 白名单**：调用 API 的服务器 IP 必须在公众号后台设置的 IP 白名单内
6. **草稿发布后会从草稿箱移除**：草稿一旦通过 freepublish/submit 发布，就会从草稿箱消失

## 错误处理

| 错误码 | 含义 | 处理方式 |
|--------|------|----------|
| 40001 | access_token 无效 | 重新获取 token |
| 40004 | media_id 无效 | 重新上传素材 |
| 45009 | 接口调用频率超限 | 等待后重试 |
| 41001 | 缺少 access_token | 检查 token 获取逻辑 |
| 50002 | 用户受限 | 检查公众号权限 |

## 扩展：发布草稿

如需直接发布（而非仅存草稿），在新增草稿后调用：

```
POST https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={TOKEN}
Body: {"media_id": "草稿的media_id"}
```
