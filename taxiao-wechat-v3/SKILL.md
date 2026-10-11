---
name: taxiao-wechat-v3
description: |
  为「他晓」公众号生成完整的推文 HTML（V3 版本：全内联样式，微信公众号/135编辑器完美兼容）。
  基于已发布的文章风格提炼，包含完整的写作规范、排版规范和模板。
  
  TRIGGER: 当用户要求生成公众号推文、写公众号文章、创建推文模板时使用。
  关键词：公众号、推文、文章、WeChat、公众号模板、他晓
---

# 他晓公众号推文 Skill V3

## 概述

V3 版本是从已发布的文章（AI订阅套餐全景扫描、Demo Day 会议纪要/创意延伸）中提炼的完整写作规范。核心改进：**全内联样式 + HTML align 属性**，确保粘贴到 135 编辑器 → 微信公众号后格式完美保留。

## 一、写作风格规范

### 1.1 语气与风格
- **定位**：专业但不枯燥，适合科技/AI 爱好者阅读
- **语气**：客观、有洞察力，避免过度营销感
- **人称**：第三人称叙述为主，适当使用「你」拉近距离
- **句式**：中短句为主，每段 2-4 句，避免大段文字

### 1.2 标题规范
- 主标题格式：`主题名：核心观点（上/下）`
- 副标题：补充说明，用 `·` 分隔关键信息
- 示例：
  - 主标题：`Demo Day：我如何与 Agents 共事（上）`
  - 副标题：`2026年4月24日 · 线上分享会 · 近3小时干货 · 14位嘉宾实战分享`

### 1.3 正文规范
- **段落**：每段 1 个核心观点，2-4 句话
- **强调**：关键概念用 `<strong style="color:#1565C0; font-weight:600;">` 包裹
- **引用**：用「」包裹中文引用，不用""
- **连接词**：适当使用破折号（——）和箭头（→）
- **数字**：使用阿拉伯数字（14位、50个、3小时）

### 1.4 结构模式

根据文章类型选择：

**A. 会议/活动纪要型**
```
开头引入（活动背景 + 信息卡片）
→ 嘉宾/主题分段（每人/每主题一段）
  → 标题：序号 + 姓名 + 身份
  → 1-2 段核心观点
  → 金句 callout 框（可选）
  → 产品/链接卡片（可选）
→ 分隔线（每 3-4 个嘉宾后）
→ 共性洞察总结
→ 下期预告（如有续篇）
```

**B. 创意延伸/观点型**
```
开头引入（承接上篇 + 引出主题）
→ 创意点/观点分段
  → 标题：序号 + 「概念名」—— 副标题
  → 灵感来源
  → 延伸思考（2-3 段）
  → 核心观点 callout 框
→ 总结与行动建议
→ 上篇回顾（如有上篇）
```

**C. 数据对比/科普型**
```
开头引入（为什么写这篇文章）
→ 数据表格/对比卡片
→ 关键发现/洞察
→ 选购/使用指南
→ 链接汇总
```

## 二、排版规范（微信公众号兼容）

### 2.1 核心原则
- **所有样式必须内联**，不使用 `<style>` 标签（会被微信过滤）
- **正文段落必须加 `align="left"`**（微信忽略 CSS text-align，但识别 HTML align 属性）
- **居中元素用 `style="text-align:center"`**（header、footer、分隔线等）
- **不使用 `display:flex` / `display:grid`**（微信支持不稳定）
- **布局用 `<table>` 替代 flex/grid**（如双二维码并排）
- **标题只用 `<h2>`**，禁止使用 `<h3>`/`<h4>`/`<h5>`（微信对 h3+ 支持不稳定，会导致格式错乱）
- **表格禁止 `border-radius` 和 `overflow:hidden`**（微信对 table 上的这些属性支持不稳定）
- **表格允许的样式属性**：`width`、`border-collapse`、`border`、`margin`、`padding`、`font-size`、`text-align`、`vertical-align`
- **`border-radius` 和 `overflow:hidden` 只能用在 `<div>` 上**（微信对 div 上的这些属性支持良好）

### 2.2 配色方案

| 用途 | 颜色 | 说明 |
|------|------|------|
| 主色 | `#1976D2` | 品牌蓝，标题左边框、强调文字 |
| 深蓝 | `#1565C0` | strong 强调色 |
| 浅蓝背景 | `#E3F2FD` | callout 框背景 |
| 极浅蓝 | `#F0F7FF` | 链接卡片背景 |
| 正文色 | `#1A2332` | 标题文字 |
| 辅助文字 | `#4A5568` | 正文段落 |
| 弱化文字 | `#718096` | 副标题、提示 |
| 边框 | `#E2E8F0` | 卡片边框 |
| 分隔线 | `#BBDEFB` | 淡蓝分隔点 |

### 2.3 字体

- 标题：`font-family:Georgia,'Noto Serif SC',serif`
- 正文：系统默认（不设置 font-family，微信会用系统字体）

### 2.4 常用组件（复制即用）

**段落文字**：
```html
<p style="font-size:15px; color:#4A5568; line-height:2; margin:0 0 14px; " align="left">正文内容，<strong style="color:#1565C0; font-weight:600;">重点内容</strong>。</p>
```

**二级标题**：
```html
<h2 style="font-family:Georgia,'Noto Serif SC',serif; font-size:19px; font-weight:700; color:#1A2332; margin:0 0 16px; padding-left:14px; border-left:3px solid #1976D2;">标题文字</h2>
```

**编号标题**：
```html
<h2 style="font-family:Georgia,'Noto Serif SC',serif; font-size:19px; font-weight:700; color:#1A2332; margin:0 0 16px; padding-left:14px; border-left:3px solid #1976D2;">01 &nbsp;姓名 &mdash; 身份</h2>
```

**金句/核心观点 callout**：
```html
<div style="background:#E3F2FD; border-left:4px solid #1976D2; border-radius:0 12px 12px 0; padding:18px 16px; margin:18px 0;">
  <div style="display:inline-block; font-size:11px; font-weight:600; color:#1976D2; background:#FFFFFF; padding:2px 10px; border-radius:8px; margin-bottom:10px; box-shadow:0 1px 3px rgba(25,118,210,0.06);">金句</div>
  <p style="font-size:14px; color:#4A5568; line-height:2; margin:0;" align="left">金句内容</p>
</div>
```

**信息卡片**：
```html
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:18px 16px; margin:16px 0; box-shadow:0 1px 3px rgba(25,118,210,0.06);">
  <div style="font-size:13px; color:#4A5568; line-height:2.2;">
    <span style="font-weight:600; color:#1976D2;">标签：</span>内容<br/>
  </div>
</div>
```

**链接卡片**：
```html
<div style="margin:10px 0; padding:10px 14px; background:#F0F7FF; border-radius:8px; border-left:3px solid #1976D2;">
  <span style="font-size:13px; color:#1976D2;">🔗 产品：</span>
  <a href="https://example.com" target="_blank" style="font-size:13px; color:#1565C0; text-decoration:none; word-break:break-all;">https://example.com</a>
</div>
```

**分隔线**：
```html
<div style="text-align:center; margin:28px 0; color:#BBDEFB; font-size:18px; letter-spacing:8px;">&bull; &bull; &bull;</div>
```

**头像+文字并排（居中，禁止 flex/table，用 vertical-align 内联实现）**：
```html
<div style="text-align:center; margin-bottom:18px;">
  <img src="{文章主题}_公众号推文_assets/avatar.png" alt="他晓" style="width:40px; height:40px; border-radius:10px; box-shadow:0 2px 8px rgba(25,118,210,0.15); vertical-align:middle; margin-right:10px;" />
  <span style="font-family:Georgia,'Noto Serif SC',serif; font-size:17px; font-weight:700; color:#1976D2; letter-spacing:2px; vertical-align:middle;">他晓</span>
</div>
```
> ⚠️ 此组件禁止用 `display:flex`（微信不支持），也禁止用 `<table>` 布局（微信会显示表格结构）。只能用 `vertical-align:middle` 内联方式实现图文垂直居中。

**内容段落容器**：
```html
<div style="margin-bottom:32px;" align="left">
  <!-- 标题 + 段落 + callout -->
</div>
```

**链接列表（垂直布局，支持自动换行）**：
```html
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:14px 18px; box-shadow:0 1px 3px rgba(25,118,210,0.06);">
  <div style="padding:10px 0; border-bottom:1px solid #F0F2F5;">
    <div style="font-size:13px; font-weight:600; color:#1A2332; margin-bottom:4px;">平台名称</div>
    <a href="https://example.com" target="_blank" style="font-size:12px; color:#1976D2; text-decoration:none; word-break:break-all; line-height:1.6;">https://example.com</a>
  </div>
  <!-- 更多链接... -->
</div>
```

**双二维码并排（table 布局）**：
```html
<table style="margin:0 auto 20px; border-collapse:collapse;">
  <tr>
    <td style="width:50%; text-align:center; padding:0 8px; vertical-align:top;">
      <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:14px; padding:16px 12px; box-shadow:0 1px 3px rgba(25,118,210,0.06);">
        <img src="assets/qrcode_gzh.jpg" alt="公众号二维码" style="width:120px; height:120px; border-radius:10px; margin-bottom:10px;" />
        <div style="font-family:Georgia,'Noto Serif SC',serif; font-size:14px; font-weight:600; color:#1976D2; margin-bottom:4px;">公众号 · 他晓</div>
        <div style="font-size:11px; color:#718096;">关注获取更多内容</div>
      </div>
    </td>
    <td style="width:50%; text-align:center; padding:0 8px; vertical-align:top;">
      <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:14px; padding:16px 12px; box-shadow:0 1px 3px rgba(25,118,210,0.06);">
        <img src="assets/qrcode_xcx.jpg" alt="小程序二维码" style="width:120px; height:120px; border-radius:10px; margin-bottom:10px;" />
        <div style="font-family:Georgia,'Noto Serif SC',serif; font-size:14px; font-weight:600; color:#1976D2; margin-bottom:4px;">小程序 · 人格派对</div>
        <div style="font-size:11px; color:#718096;">开启你的探索之旅</div>
      </div>
    </td>
  </tr>
</table>
```

## 三、使用方法

### 3.1 读取模板
```
Read assets/template.html
```

### 3.2 组装推文
1. 将用户内容写入 `<!-- ===== ARTICLE CONTENT START ===== -->` 和 `<!-- ===== ARTICLE CONTENT END ===== -->` 之间
2. 替换 `{{TITLE}}` 和 `{{SUBTITLE}}`
3. 所有正文 `<p>` 必须加 `align="left"`
4. 所有内容 `<div>` 必须加 `align="left"`
5. 不使用 `<style>` 标签
6. 不使用 `display:flex` / `display:grid`
7. **所有标题只用 `<h2>`**（包括子标题），通过 `font-size` 区分层级，禁止 `<h3>`/`<h4>`
8. **`<table>` 上禁止 `border-radius` 和 `overflow:hidden`**，只能用 `border-collapse`、`border`、`margin`、`padding`、`width` 等

### 3.3 输出与发布流程（重要：必须严格按此流程）

#### 3.3.1 源文件
- 文件名格式：`{文章主题}_公众号推文.html`
- 同时将 `assets/` 复制到输出目录的 `{文章主题}_公众号推文_assets/` 子文件夹
- 图片路径使用相对路径：`{文章主题}_公众号推文_assets/xxx.png`
- 源文件使用 `<div>` 标签和完整 HTML 结构（`<!DOCTYPE>`、`<html>`、`<head>`、`<body>`）

**素材文件检查清单（复制后必须逐项核对，缺一不可）**：
| 文件 | 用途 | 必需 |
|------|------|------|
| `avatar.png` | 开头公众号头像 | ✅ |
| `header_deco.png` | 开头装饰图 | ✅ |
| `footer_deco.png` | 结尾装饰图 | ✅ |
| `qrcode_gzh.jpg` | 结尾公众号二维码 | ✅ |
| `qrcode_xcx.jpg` | 结尾小程序二维码 | ✅ |
| `qrcode_wechat.png` | 结尾社群微信二维码 | ✅ |
| `cover.png` | 微信封面缩略图①：Pillow 浅色四主题 | ✅ |
| `cover-dev.png` | 微信封面缩略图②：深色开发者风（与①二选一上传） | ✅ |

> ⚠️ 复制完成后执行 `ls {文章主题}_公众号推文_assets/` 核对 7 个文件齐全，再进入下一步。漏复制文件会导致图片在微信中无法显示。

#### 3.3.2 生成复制粘贴版（两步流程，缺一不可）

**为什么需要两步？**
- 微信编辑器原生使用 `<section>` 标签，`<div>` 标签粘贴后样式可能丢失
- 微信会过滤 `<style>` 标签和 CSS class，需要全部转为内联样式
- 微信不支持外部图片引用，需要将所有图片转为 base64 内嵌
- 直接在源文件上嵌入 base64 会导致文件过大、难以维护

**Step 1：html_to_copy.py — 结构转换**

将源 HTML 转换为微信兼容的 `<section>` 结构：

```bash
python3 .trae/skills/wechat-draft-publish/html_to_copy.py \
  "{文章主题}_公众号推文.html" \
  -o "{文章主题}_公众号推文_转换版.html"
```

此脚本执行以下操作：
1. `<div>` → `<section>`（微信编辑器原生标签）
2. `<style>` 中的 CSS class 转为内联 `style` 属性
3. 解析 CSS 变量 `var(--xxx)` 为实际值
4. 移除 `<!DOCTYPE>`、`<html>`、`<head>`、`<body>` 等无关标签
5. 输出纯净的 HTML 片段（无外层文档结构）

**Step 2：generate_copy_version.py — 图片内嵌**

将转换后的 HTML 中的所有本地图片转为 base64 内嵌：

```bash
python3 .trae/skills/wechat-draft-publish/generate_copy_version.py \
  --html "{文章主题}_公众号推文_转换版.html" \
  --output "{文章主题}_公众号推文_复制粘贴版.html"
```

此脚本执行以下操作：
1. 所有本地图片转为 base64 内嵌（自动去 AI 水印）
2. 素材图片（avatar、qrcode、header_deco 等）跳过去水印
3. 包裹单一 HTML 文档结构（`<!DOCTYPE>` + `<html>` + `<body>`）
4. 输出自包含的 HTML 文件，浏览器打开即可全选复制

**Step 3：清理中间文件**

删除 Step 1 生成的转换版文件：
```bash
rm "{文章主题}_公众号推文_转换版.html"
```

#### 3.3.3 最终交付文件

| 文件 | 用途 |
|------|------|
| `{文章主题}_公众号推文.html` | 源文件（用于编辑维护） |
| `{文章主题}_公众号推文_复制粘贴版.html` | 浏览器打开 → 全选复制 → 粘贴到微信公众号 |
| `{文章主题}_公众号推文_assets/` | 图片资源目录 |
| `{文章主题}_公众号推文_assets/cover.png` | 微信封面缩略图（单独上传） |

#### 3.3.4 验证清单

生成复制粘贴版后，必须验证以下内容：

```
✅ 使用 <section> 标签（非 <div>）
✅ 无 <!DOCTYPE> 双重嵌套（只能有 1 个）
✅ 无 <style> 标签、无 CSS class
✅ 无 display:flex / display:grid
✅ 无 <h3> / <h4> / <h5>（只用 <h2>）
✅ <table> 上无 border-radius / overflow:hidden
✅ 开头头像+文字用 vertical-align 内联（非 table/flex 布局）
✅ 所有图片为 base64 内嵌（src="data:image/..."）
✅ 无外部图片引用（src="assets/..." 或 src="http..."）
✅ base64 图片数量与素材目录文件数一致（7 个素材 + 正文配图）
```

#### 3.3.5 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| 粘贴后格式错乱 | 跳过 Step 1，`<div>` 未转为 `<section>` | 必须先运行 html_to_copy.py |
| 双重 HTML 结构 | Step 2 直接作用于源文件（含完整 HTML 文档） | 必须先运行 Step 1 去除 HTML 外层 |
| 图片无法显示 | 图片未内嵌为 base64 | 必须运行 Step 2 的 generate_copy_version.py |
| 标题样式丢失 | 使用了 `<h3>` 等非 `<h2>` 标签 | 所有标题统一用 `<h2>`，通过 font-size 区分层级 |
| 表格圆角消失 | `<table>` 上使用了 `border-radius` | 表格禁用 border-radius，改用 `<div>` 包裹实现圆角 |
| 开头头像「他晓」显示在表格结构内 | brand-row 用了 `<table>` 布局（flex 失效后的错误替代） | 用 vertical-align:middle 内联方式实现图文并排（见 2.4 组件） |
| 结尾微信二维码不显示 | `qrcode_wechat.png` 未复制到素材目录 | 按 3.3.1 素材检查清单逐项核对 7 个文件 |

### 3.4 封面图（重要：必须严格按此流程）

**核心规则**：
- 封面图**仅用于微信公众号推送链接的缩略图**（通过 thumb_media_id 上传），**不嵌入正文 HTML**
- **必须使用 Pillow 脚本生成**，**禁止使用 AI 图片生成**（AI 生成的图片有水印、风格不可控）
- 尺寸固定 **900×383**（微信公众号文章封面比例 2.35:1）
- 文件名：`cover.png`，放在 `{文章主题}_公众号推文_assets/` 目录下

**生成命令**：
```bash
python3 taxiao-wechat-v3/assets/generate_cover.py \
  --title "文章主标题" \
  --subtitle "文章副标题" \
  --tags "关键词1 · 关键词2 · 关键词3" \
  --output "{文章主题}_公众号推文_assets/cover.png" \
  --theme blue
```

**主题选项**：
| 主题 | 适用场景 | 主色 |
|------|----------|------|
| `blue` | AI/技术/开发类（默认） | 科技蓝 #1976D2 |
| `orange` | 产品/创业/增长类 | 活力橙 #F26522 |
| `purple` | 深度分析/行业报告类 | 深空紫 #6A1B9A |
| `green` | 生态/开源/教育类 | 清新绿 #2E7D32 |

**深色开发者风（与 pip-cover 视频封面同款视觉，2026-10-11 新增）**：

**规则：每期同时生成两个封面，发布时二选一上传 thumb**：
1. `cover.png` — Pillow 浅色四主题（上方命令）
2. `cover-dev.png` — 深色开发者风 HTML 模板（下方命令），与 pip-cover 视频封面同款视觉

```bash
# 1. 复制模板到本期 cards/ 并填 {{TOKEN}}（KICKER / TITLE_HTML 用 <br> 断行 / SUBTITLE / GHOST / BRAND）
cp taxiao-wechat-v3/assets/cover-dev-template.html <期目录>/cards/cover-wechat-dev.html
# 2. render.sh 出图（绝对路径；900×383）
<repo>/fresh-cover/scripts/render.sh "$PWD/<期目录>/cards/cover-wechat-dev.html" \
  "$PWD/<期目录>/<主题>_公众号推文_assets/cover-dev.png" 900 383
```

- 版式：#0B120D 深绿黑底 + 淡绿网格 + 顶部 glow（pip-cover 同源色板），**无人物头像**
- 信息层级只有 4 层：kicker 描边胶囊 → 主标题（≤2 行，accent 词绿色）→ 副标题 → 底部署名「他晓 Taxiao」
- 主标题压字注意：右侧幽灵装饰字（.ghost）放右下、避开标题区；换标题后需 Read 校验无重叠
- 两版封面都不嵌正文 HTML，换封面/换版本**无需**重跑 3.3.2 两步流程
- 仍然禁止 AI 生图；两个封面都是「脚本/模板渲染」，AI 图一律不准上封面

**封面图设计规范**：
- 浅色渐变背景（135°）
- 3-4 个装饰圆形（部分溢出画面边缘，营造空间感）
- 主标题：大号，主题色，居中偏上
- 装饰横线：主标题下方，80px 宽，3px 高，圆角
- 副标题：中号，深色，横线下方
- 标签行：小号，灰色，圆点分隔
- 底部品牌：「他晓 · 科技前沿」，最浅灰色

**禁止事项**：
- 禁止在正文 HTML 中放置封面图（`<img src="cover.png">`）
- 禁止使用 GenerateImage 生成封面图
- 禁止使用 AI 生成的图片作为封面（有水印问题）

## 四、资源文件

### 4.1 本技能资源（taxiao-wechat-v3/assets/）

| 文件 | 用途 |
|------|------|
| `avatar.png` | 公众号头像 |
| `qrcode_gzh.jpg` | 公众号二维码 |
| `qrcode_xcx.jpg` | 小程序二维码 |
| `qrcode_wechat.png` | 微信二维码（社群邀请） |
| `header_deco.png` | 开头装饰图 |
| `footer_deco.png` | 结尾装饰图 |
| `generate_cover.py` | 封面图生成脚本（Pillow，浅色四主题，见 3.4 节） |
| `cover-dev-template.html` | 深色开发者风公众号封面模板（900×383，HTML + render.sh，见 3.4 节） |
| `template.html` | 完整 HTML 模板（全内联样式） |

### 4.2 外部依赖脚本（wechat-draft-publish/）

| 文件 | 用途 |
|------|------|
| `html_to_copy.py` | Step 1：`<div>`→`<section>` 转换、CSS 内联化、去除 HTML 外层结构（见 3.3.2 节） |
| `generate_copy_version.py` | Step 2：图片 base64 内嵌、自动去水印、包裹单一 HTML 文档（见 3.3.2 节） |

**脚本路径**：`.trae/skills/wechat-draft-publish/`
