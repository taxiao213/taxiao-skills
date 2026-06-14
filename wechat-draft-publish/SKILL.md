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

微信公众号编辑器和 API **会直接剥离 `<style>` 标签中的所有 CSS**，只保留元素上的 `style=""` 内联属性。如果直接推送原始 HTML，所有样式都会丢失，文章变成纯文本。

解决方案：使用 `html_to_wechat.py` 转换器，自动完成以下转换：
- **解析 `<style>` 中的全部 CSS 规则**，将类选择器（如 `.section-title`）、组合选择器（如 `.tool-list .tool-name`）、标签选择器（如 `h1`）精确匹配到对应元素
- **将 CSS 变量**（`var(--blue-primary)` 等）替换为实际颜色值
- **跳过 `@media` 响应式规则**——微信公众号不支持响应式，避免移动端样式覆盖桌面端样式
- **处理 `:last-child` 伪类**——如移除最后一个 `.tool-item` 的底部边框
- **移除 `<style>`、`<head>`、`<body>` 等标签**，只保留 `<body>` 内的内容
- **修复自闭合标签**——`img` 和 `br` 转为 WeChat 兼容格式
- **保留 `align="left"` 等 HTML 属性**

**技术实现**：转换器不再使用硬编码的 class→style 映射表，而是实时解析 HTML 中的 `<style>` 标签，构建 CSS 规则树，根据元素在 DOM 中的实际路径进行精确匹配。这确保了无论模板如何变化，转换结果始终与原始样式一致。

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

## 脚本清单

| 脚本 | 用途 |
|------|------|
| `publish_to_draft.py` | 首次发布：上传图片 + 转换样式 + 推送草稿 |
| `update_draft.py` | 样式更新：仅转换样式 + 推送草稿（复用已有图片URL） |
| `html_to_wechat.py` | HTML 转 WeChat 内联样式（被上述两个脚本自动调用） |

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
