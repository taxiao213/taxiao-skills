#!/usr/bin/env python3
"""
HTML 转 WeChat 内联样式转换器（v3 精确匹配版）

微信公众号编辑器会剥离 <style> 标签中的所有 CSS，只保留元素上的内联 style 属性。
本脚本将 taxiao-wechat-v3 模板的 CSS 类样式转换为内联样式，确保推送到草稿箱后格式一致。

核心设计原则：
1. 解析 <style> 中的全部 CSS 规则（而非硬编码映射）
2. 自动解析 CSS 变量（:root var()）
3. 精确支持嵌套/组合选择器（.parent .child），只匹配目标元素
4. 支持伪类（:last-child 等）通过内联样式等价替换
5. 移除 WeChat 不支持的标签和属性

用法:
    python3 html_to_wechat.py "input.html" -o "output.html"
"""

import re
import sys
import os
from html.parser import HTMLParser


# ============================================================
# CSS 变量默认值（从模板 :root 提取）
# ============================================================
CSS_VARS = {
    "--blue-primary": "#1976D2",
    "--blue-dark": "#1565C0",
    "--blue-mid": "#2196F3",
    "--blue-light": "#64B5F6",
    "--blue-pale": "#BBDEFB",
    "--blue-bg": "#E3F2FD",
    "--blue-white": "#F5F9FF",
    "--white": "#FFFFFF",
    "--gray-50": "#FAFBFC",
    "--gray-100": "#F0F2F5",
    "--gray-200": "#E4E7EB",
    "--gray-400": "#9CA3AF",
    "--gray-600": "#4B5563",
    "--gray-800": "#1F2937",
    "--text-primary": "#1A2332",
    "--text-secondary": "#4A5568",
    "--text-muted": "#718096",
    "--border": "#E2E8F0",
    "--shadow-sm": "0 1px 3px rgba(25,118,210,0.06)",
    "--shadow-md": "0 4px 16px rgba(25,118,210,0.08)",
    "--shadow-lg": "0 8px 32px rgba(25,118,210,0.1)",
}


def resolve_css_vars(css_str: str) -> str:
    """将 CSS 中的 var(--xxx) 替换为实际值"""
    def var_replacer(m):
        var_name = m.group(1).strip()
        fallback = m.group(2).strip() if m.group(2) else None
        return CSS_VARS.get(var_name, fallback or "")
    return re.sub(r'var\(\s*(--[\w-]+)\s*(?:,\s*([^)]+))?\s*\)', var_replacer, css_str)


# ============================================================
# CSS 规则解析器
# ============================================================
class CSSRule:
    """表示一条 CSS 规则，支持多选择器"""
    def __init__(self, selector: str, declarations: str):
        self.raw_selector = selector.strip()
        self.declarations = resolve_css_vars(declarations.strip())
        # 解析为多个选择器路径（逗号分隔）
        self.selector_paths = self._parse_selectors(self.raw_selector)

    def _parse_selectors(self, selector: str):
        """解析逗号分隔的多个选择器，每个选择器是一个层级列表"""
        paths = []
        for sel in selector.split(','):
            sel = sel.strip()
            if not sel:
                continue
            levels = []
            # 按空格分割，但保留 > + ~ 等组合器（简化：只处理后代选择器）
            for part in sel.split():
                tag = None
                classes = []
                pseudo = None
                # 提取伪类
                if ':' in part:
                    part, pseudo = part.split(':', 1)
                if part.startswith('.'):
                    classes = part[1:].split('.')
                elif '.' in part:
                    tag = part.split('.')[0]
                    classes = part.split('.')[1:]
                else:
                    tag = part
                levels.append({'tag': tag, 'classes': classes, 'pseudo': pseudo})
            paths.append(levels)
        return paths

    def __repr__(self):
        return f"CSSRule({self.raw_selector})"


def parse_css_rules(css_text: str) -> list:
    """从 <style> 标签内容中解析所有 CSS 规则"""
    rules = []
    css_text = re.sub(r'/\*.*?\*/', '', css_text, flags=re.DOTALL)

    # 第一步：移除所有 @media {...} 块（微信公众号不支持响应式）
    # 使用平衡括号匹配
    def remove_media_blocks(text):
        result = []
        i = 0
        while i < len(text):
            if text[i:i+7] == '@media ':
                # 找到 @media 的结束位置（匹配的 }）
                brace_start = text.find('{', i)
                if brace_start == -1:
                    result.append(text[i:])
                    break
                depth = 0
                j = brace_start
                while j < len(text):
                    if text[j] == '{':
                        depth += 1
                    elif text[j] == '}':
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                i = j + 1
            else:
                result.append(text[i])
                i += 1
        return ''.join(result)

    css_text = remove_media_blocks(css_text)

    # 第二步：解析普通规则
    pattern = r'([^{]+)\{([^}]*)\}'
    for match in re.finditer(pattern, css_text):
        selector = match.group(1).strip()
        declarations = match.group(2).strip()
        if selector.startswith('@'):
            # 跳过其他 @ 规则
            continue
        if declarations:
            rules.append(CSSRule(selector, declarations))
    return rules


# ============================================================
# 样式合并工具
# ============================================================
def merge_style(existing: str, new_style: str) -> str:
    """合并两个 style 字符串，新样式优先"""
    if not existing:
        return new_style
    if not new_style:
        return existing
    existing_props = {}
    for prop in existing.split(';'):
        prop = prop.strip()
        if ':' in prop:
            k, v = prop.split(':', 1)
            existing_props[k.strip()] = v.strip()
    for prop in new_style.split(';'):
        prop = prop.strip()
        if ':' in prop:
            k, v = prop.split(':', 1)
            existing_props[k.strip()] = v.strip()
    return ';'.join(f"{k}:{v}" for k, v in existing_props.items()) + ';'


# ============================================================
# HTML 转换器
# ============================================================
class WeChatHTMLConverter(HTMLParser):
    """将 HTML 转换为 WeChat 兼容的内联样式 HTML"""

    def __init__(self, css_rules: list = None):
        super().__init__()
        self.css_rules = css_rules or []
        self.output = []
        self.element_stack = []  # 每个元素: {tag, classes, child_count}
        self._in_style = False
        self._in_head = False
        self._in_script = False
        self._capture_body = False

    def _match_selector_against_path(self, selector_levels, element_path):
        """
        后代选择器匹配：selector_levels 对应 element_path 的尾部，
        允许中间有其他元素（后代选择器语义）。
        单层选择器（如 .stat-grid）只匹配当前元素自身。
        多层选择器（如 .stat-grid .stat-card）匹配当前元素及其祖先。
        """
        if len(selector_levels) > len(element_path):
            return False

        # 单层选择器：只检查当前元素（path 最后一个）
        if len(selector_levels) == 1:
            sel = selector_levels[0]
            elem = element_path[-1]
            if sel['tag'] and sel['tag'] != elem['tag']:
                return False
            if sel['classes']:
                elem_classes = set(elem['classes'])
                if not all(c in elem_classes for c in sel['classes']):
                    return False
            if sel['pseudo']:
                if sel['pseudo'] == 'last-child':
                    if not elem.get('is_last_child', False):
                        return False
                elif sel['pseudo'] == 'first-child':
                    if not elem.get('is_first_child', False):
                        return False
            return True

        # 多层选择器：从后向前匹配，允许跳过中间元素
        # 但最后一个选择器必须匹配当前元素（path 最后一个）
        sel_idx = len(selector_levels) - 1
        path_idx = len(element_path) - 1

        # 首先确保最后一个选择器匹配当前元素
        last_sel = selector_levels[-1]
        last_elem = element_path[-1]
        if last_sel['tag'] and last_sel['tag'] != last_elem['tag']:
            return False
        if last_sel['classes']:
            if not all(c in last_elem['classes'] for c in last_sel['classes']):
                return False
        if last_sel['pseudo']:
            if last_sel['pseudo'] == 'last-child':
                if not last_elem.get('is_last_child', False):
                    return False
            elif last_sel['pseudo'] == 'first-child':
                if not last_elem.get('is_first_child', False):
                    return False

        # 然后匹配前面的选择器（祖先）
        sel_idx -= 1
        path_idx -= 1
        while sel_idx >= 0 and path_idx >= 0:
            sel = selector_levels[sel_idx]
            elem = element_path[path_idx]

            matched = True
            if sel['tag'] and sel['tag'] != elem['tag']:
                matched = False
            if sel['classes']:
                elem_classes = set(elem['classes'])
                if not all(c in elem_classes for c in sel['classes']):
                    matched = False
            if sel['pseudo']:
                if sel['pseudo'] == 'last-child':
                    if not elem.get('is_last_child', False):
                        matched = False
                elif sel['pseudo'] == 'first-child':
                    if not elem.get('is_first_child', False):
                        matched = False

            if matched:
                sel_idx -= 1
            path_idx -= 1

        return sel_idx < 0

    def _get_styles_for_current_element(self, tag, classes):
        """获取匹配当前元素的所有 CSS 样式（当前元素是 path 的最后一个）"""
        matched = []
        for rule in self.css_rules:
            for selector_levels in rule.selector_paths:
                if self._match_selector_against_path(selector_levels, self.element_stack):
                    matched.append(rule.declarations)
                    break
        return matched

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        classes = [c for c in attrs_dict.get("class", "").split() if c]
        existing_style = attrs_dict.get("style", "")

        if tag in ("head", "script", "link", "meta", "!doctype", "html"):
            if tag == "head":
                self._in_head = True
            if tag == "script":
                self._in_script = True
            return
        if tag == "style":
            self._in_style = True
            return
        if tag == "body":
            self._capture_body = True
            return
        if not self._capture_body:
            return

        # 计算同级索引
        sibling_idx = 0
        if self.element_stack:
            parent = self.element_stack[-1]
            sibling_idx = parent.get('child_count', 0)
            parent['child_count'] = sibling_idx + 1

        elem_info = {
            'tag': tag,
            'classes': classes,
            'child_count': 0,
            'is_first_child': sibling_idx == 0,
            'is_last_child': False,  # 临时，在 endtag 时可能更新
        }
        self.element_stack.append(elem_info)

        # 获取匹配的样式
        inline_style = existing_style
        matched_styles = self._get_styles_for_current_element(tag, classes)
        for style in matched_styles:
            inline_style = merge_style(inline_style, style)

        # 清理
        inline_style = self._sanitize_for_wechat(inline_style)

        # 构建属性
        new_attrs = []
        for k, v in attrs:
            if k == "class":
                continue
            if k == "style":
                if inline_style:
                    new_attrs.append(('style', inline_style))
                continue
            new_attrs.append((k, v))
        if inline_style and "style" not in attrs_dict:
            new_attrs.append(("style", inline_style))

        attr_str = ""
        for k, v in new_attrs:
            attr_str += f' {k}="{v}"'

        if tag in ("img", "br", "hr", "input", "meta", "link"):
            if tag == "br":
                self.output.append("<br />")
            elif tag == "img":
                self.output.append(f"<img{attr_str} />")
            else:
                self.output.append(f"<{tag}{attr_str} />")
        else:
            self.output.append(f"<{tag}{attr_str}>")

    def _sanitize_for_wechat(self, style: str) -> str:
        if not style:
            return style
        props = {}
        for prop in style.split(';'):
            prop = prop.strip()
            if ':' in prop:
                k, v = prop.split(':', 1)
                k = k.strip()
                v = resolve_css_vars(v.strip())
                if v:
                    props[k] = v
        return ';'.join(f"{k}:{v}" for k, v in props.items()) + ';'

    def handle_endtag(self, tag):
        if tag == "head":
            self._in_head = False
            return
        if tag == "style":
            self._in_style = False
            return
        if tag == "script":
            self._in_script = False
            return
        if tag in ("html", "body", "!doctype", "link", "meta"):
            return
        if not self._capture_body:
            return
        if tag in ("img", "br", "hr", "input"):
            if self.element_stack and self.element_stack[-1]['tag'] == tag:
                self.element_stack.pop()
            return

        self.output.append(f"</{tag}>")
        if self.element_stack:
            self.element_stack.pop()

    def handle_data(self, data):
        if self._in_style or self._in_head or self._in_script:
            return
        if not self._capture_body:
            return
        self.output.append(data)

    def handle_entityref(self, name):
        if self._in_style or self._in_head or self._in_script:
            return
        if not self._capture_body:
            return
        self.output.append(f"&{name};")

    def handle_charref(self, name):
        if self._in_style or self._in_head or self._in_script:
            return
        if not self._capture_body:
            return
        self.output.append(f"&#{name};")

    def get_result(self) -> str:
        result = "".join(self.output)
        # 后处理：修复 tool-item last-child
        result = self._fix_last_tool_items(result)
        # 修复残留的 var()
        result = resolve_css_vars(result)
        # 修复 <br></br>
        result = result.replace("<br></br>", "<br />")
        result = result.replace("</br>", "")
        # 修复 </img>
        result = result.replace("</img>", "")
        return result

    def _fix_last_tool_items(self, html: str) -> str:
        """移除每个 tool-list 中最后一个 tool-item 的底部边框"""
        # 找到所有 tool-list 容器，对其中的最后一个 tool-item 移除 border-bottom
        # 策略：定位 tool-list 的结束位置，向前找到最后一个带 border-bottom 的 div
        import re as re_local
        # 匹配 tool-list 开始和其中的 tool-item
        # 简化方案：找到所有 tool-item div，在每个 tool-list 范围内，最后一个移除 border-bottom
        pattern = r'(<div[^>]*style="[^"]*background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:20px 18px;margin:16px 0;box-shadow:0 1px 3px rgba\(25,118,210,0\.06\);"[^>]*>)((?:(?!</div>\s*</div>).)*?)(<div[^>]*style="[^"]*display:flex;align-items:flex-start;gap:10px;margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid #F0F2F5;[^"]*"[^>]*>.*?</div>)(\s*</div>\s*</div>)'
        # 这个正则太复杂，采用更简单的字符串替换策略
        # 找到每个 tool-list 的闭合，将其前面最后一个 tool-item 的 border-bottom 移除

        # 简单方案：遍历所有 tool-item 样式，对连续出现的 tool-item，最后一个替换 border-bottom
        tool_item_style = 'display:flex;align-items:flex-start;gap:10px;margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid #F0F2F5;'
        tool_item_last_style = 'display:flex;align-items:flex-start;gap:10px;margin-bottom:0px;padding-bottom:0px;border-bottom:none;'

        # 在 tool-list 容器内，找到最后一个 tool-item
        # 用 split 定位 tool-list 的边界
        parts = html.split('<div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:20px 18px;margin:16px 0;box-shadow:0 1px 3px rgba(25,118,210,0.06);">')
        new_parts = [parts[0]]
        for part in parts[1:]:
            # 这个 part 是一个 tool-list 的内容，直到下一个 tool-list 或结束
            # 找到其中最后一个 tool-item-style
            if tool_item_style in part:
                # 从后向前替换第一个出现的 tool_item_style
                last_idx = part.rfind(tool_item_style)
                if last_idx != -1:
                    part = part[:last_idx] + tool_item_last_style + part[last_idx + len(tool_item_style):]
            new_parts.append('<div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:20px 18px;margin:16px 0;box-shadow:0 1px 3px rgba(25,118,210,0.06);">')
            new_parts.append(part)
        return ''.join(new_parts)


def extract_css_from_html(html_content: str) -> str:
    """从 HTML 中提取 <style> 内容"""
    style_pattern = re.compile(r'<style[^>]*>(.*?)</style>', re.DOTALL | re.IGNORECASE)
    css_text = ""
    for match in style_pattern.finditer(html_content):
        css_text += "\n" + match.group(1)
    return css_text


def convert_html_to_wechat(html_content: str) -> str:
    """将 HTML 内容转换为 WeChat 兼容的内联样式 HTML"""
    css_text = extract_css_from_html(html_content)
    css_rules = parse_css_rules(css_text)
    converter = WeChatHTMLConverter(css_rules)
    converter.feed(html_content)
    return converter.get_result()


def main():
    if len(sys.argv) < 2:
        print("用法: python3 html_to_wechat.py <input.html> [-o output.html]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = None
    if "-o" in sys.argv:
        idx = sys.argv.index("-o")
        if idx + 1 < len(sys.argv):
            output_path = sys.argv[idx + 1]
    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_wechat{ext}"

    with open(input_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    result = convert_html_to_wechat(html_content)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)

    css_rules = parse_css_rules(extract_css_from_html(html_content))
    print(f"转换完成: {output_path}")
    print(f"  输入大小: {len(html_content)} 字符")
    print(f"  输出大小: {len(result)} 字符")
    print(f"  解析 CSS 规则数: {len(css_rules)}")


if __name__ == "__main__":
    main()
