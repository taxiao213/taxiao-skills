#!/usr/bin/env python3
"""
HTML 转 WeChat 兼容格式转换器（v5 table布局版）

核心策略：
1. 使用 <section> 代替 <div>（微信编辑器原生使用 <section>）
2. 将 grid 布局转换为 <table> 布局（微信完全支持 table）
3. 将 flex 行布局转换为 <table> 单行布局
4. 只保留微信API路径支持的内联样式属性
5. 移除 WeChat 不支持的属性（box-shadow, display:flex/grid 等）

微信API路径(draft/add)支持的样式属性（基于2026年反向解析验证）：
- 文字：font-size, color, line-height, text-align, font-weight, font-family
- 盒模型：margin, padding, background, background-color, width, height
- 边框：border, border-left, border-radius
- 布局：table 及相关标签完全支持

用法:
    python3 html_to_wechat.py "input.html" -o "output.html"
"""

import re
import sys
import os
from html.parser import HTMLParser


# ============================================================
# CSS 变量默认值
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

# 微信API路径支持的内联样式属性白名单
WECHAT_SAFE_STYLES = {
    'color', 'font-size', 'font-weight', 'font-family', 'line-height',
    'text-align', 'text-decoration', 'letter-spacing', 'text-indent',
    'margin', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right',
    'padding', 'padding-top', 'padding-bottom', 'padding-left', 'padding-right',
    'background', 'background-color',
    'border', 'border-left', 'border-bottom', 'border-top', 'border-right',
    'border-collapse', 'border-spacing',
    'border-radius',
    'width', 'max-width', 'height', 'max-height',
    'overflow', 'vertical-align',
    'table-layout',
}

# 需要过滤的 display 值
UNSUPPORTED_DISPLAY_VALUES = {'flex', 'grid', 'inline-flex', 'inline-grid'}

# 需要转换为 table 的 grid 容器 class
GRID_CONTAINERS = {'card-grid', 'stat-grid'}

# 需要转换为 table 单行的 flex 容器 class
FLEX_ROW_CONTAINERS = {'brand-row', 'tool-item', 'qr-pair'}


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
    def __init__(self, selector: str, declarations: str):
        self.raw_selector = selector.strip()
        self.declarations = resolve_css_vars(declarations.strip())
        self.selector_paths = self._parse_selectors(self.raw_selector)

    def _parse_selectors(self, selector: str):
        paths = []
        for sel in selector.split(','):
            sel = sel.strip()
            if not sel:
                continue
            levels = []
            for part in sel.split():
                tag = None
                classes = []
                pseudo = None
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


def parse_css_rules(css_text: str) -> list:
    """从 <style> 标签内容中解析所有 CSS 规则"""
    rules = []
    css_text = re.sub(r'/\*.*?\*/', '', css_text, flags=re.DOTALL)

    def remove_media_blocks(text):
        result = []
        i = 0
        while i < len(text):
            if text[i:i+7] == '@media ':
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
    pattern = r'([^{]+)\{([^}]*)\}'
    for match in re.finditer(pattern, css_text):
        selector = match.group(1).strip()
        declarations = match.group(2).strip()
        if selector.startswith('@'):
            continue
        if declarations:
            rules.append(CSSRule(selector, declarations))
    return rules


# ============================================================
# 样式工具
# ============================================================
def filter_wechat_styles(style: str) -> str:
    """只保留微信API路径支持的样式属性"""
    if not style:
        return style
    props = {}
    for prop in style.split(';'):
        prop = prop.strip()
        if ':' in prop:
            k, v = prop.split(':', 1)
            k = k.strip()
            v = resolve_css_vars(v.strip())
            if k == 'box-shadow':
                continue
            if k == 'display' and v in UNSUPPORTED_DISPLAY_VALUES:
                continue
            if k == 'grid-template-columns':
                continue
            if k == 'gap':
                continue
            if k.startswith('flex-'):
                continue
            if k.startswith('align-') and k != 'text-align':
                continue
            if k == 'justify-content':
                continue
            if any(k == safe or k.startswith(safe + '-') for safe in WECHAT_SAFE_STYLES):
                if v:
                    props[k] = v
    return ';'.join(f"{k}:{v}" for k, v in props.items()) + ';' if props else ''


def merge_style(existing: str, new_style: str) -> str:
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


def extract_style_value(style: str, prop_name: str) -> str:
    """从 style 字符串中提取指定属性的值"""
    if not style:
        return ""
    for prop in style.split(';'):
        prop = prop.strip()
        if ':' in prop:
            k, v = prop.split(':', 1)
            if k.strip() == prop_name:
                return v.strip()
    return ""


def remove_style_prop(style: str, *prop_names: str) -> str:
    """从 style 字符串中移除指定属性"""
    if not style:
        return style
    props = []
    for prop in style.split(';'):
        prop = prop.strip()
        if ':' in prop:
            k, v = prop.split(':', 1)
            if k.strip() not in prop_names:
                props.append(prop)
    return ';'.join(props) + ';' if props else ''


# ============================================================
# HTML 转换器
# ============================================================
class WeChatHTMLConverter(HTMLParser):
    """将 HTML 转换为 WeChat API 兼容格式"""

    def __init__(self, css_rules: list = None):
        super().__init__()
        self.css_rules = css_rules or []
        self.output = []
        self.element_stack = []
        self._in_style = False
        self._in_head = False
        self._in_script = False
        self._capture_body = False
        # 记录 grid 容器的列数
        self._grid_cols = {}

    def _match_selector_against_path(self, selector_levels, element_path):
        if len(selector_levels) > len(element_path):
            return False
        if len(selector_levels) == 1:
            sel = selector_levels[0]
            elem = element_path[-1]
            if sel['tag'] and sel['tag'] != elem['tag']:
                return False
            if sel['classes']:
                elem_classes = set(elem['classes'])
                if not all(c in elem_classes for c in sel['classes']):
                    return False
            return True
        last_sel = selector_levels[-1]
        last_elem = element_path[-1]
        if last_sel['tag'] and last_sel['tag'] != last_elem['tag']:
            return False
        if last_sel['classes']:
            if not all(c in last_elem['classes'] for c in last_sel['classes']):
                return False
        sel_idx = len(selector_levels) - 2
        path_idx = len(element_path) - 2
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
            if matched:
                sel_idx -= 1
            path_idx -= 1
        return sel_idx < 0

    def _get_styles_for_current_element(self, tag, classes):
        matched = []
        for rule in self.css_rules:
            for selector_levels in rule.selector_paths:
                if self._match_selector_against_path(selector_levels, self.element_stack):
                    matched.append(rule.declarations)
                    break
        return matched

    def _should_convert_to_section(self, tag, classes):
        if tag != 'div':
            return tag
        container_classes = {'wrapper', 'header', 'content-area', 'section',
                           'callout', 'summary-box', 'quote-box', 'tool-list',
                           'card-grid', 'stat-grid', 'clean-card', 'stat-card',
                           'footer', 'brand-row', 'qr-pair'}
        if any(c in container_classes for c in classes):
            return 'section'
        return 'div'

    def _is_grid_container(self, classes):
        return bool(GRID_CONTAINERS & set(classes))

    def _is_flex_row(self, classes):
        return bool(FLEX_ROW_CONTAINERS & set(classes))

    def _get_grid_columns(self, classes):
        """获取 grid 容器的列数"""
        for c in classes:
            if c in self._grid_cols:
                return self._grid_cols[c]
        return 2  # 默认2列

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

        sibling_idx = 0
        if self.element_stack:
            parent = self.element_stack[-1]
            sibling_idx = parent.get('child_count', 0)
            parent['child_count'] = sibling_idx + 1

        original_tag = tag
        tag = self._should_convert_to_section(tag, classes)

        elem_info = {
            'tag': original_tag,
            'classes': classes,
            'child_count': 0,
            'is_first_child': sibling_idx == 0,
        }
        self.element_stack.append(elem_info)

        # 获取匹配的样式
        inline_style = existing_style
        matched_styles = self._get_styles_for_current_element(original_tag, classes)
        for style in matched_styles:
            inline_style = merge_style(inline_style, style)

        # === Grid → Table 转换 ===
        if self._is_grid_container(classes):
            cols = self._get_grid_columns(classes)
            table_style = filter_wechat_styles(inline_style)
            table_style = remove_style_prop(table_style, 'display', 'grid-template-columns', 'gap')
            self.output.append(f'<table style="width:100%;border-collapse:separate;border-spacing:12px 0;{table_style}"><tr>')
            return

        # === Grid 子元素 → td 转换 ===
        parent_classes = []
        if len(self.element_stack) >= 2:
            parent_classes = self.element_stack[-2].get('classes', [])
        if self._is_grid_container(parent_classes):
            # grid 的直接子元素，输出 <td>
            td_style = filter_wechat_styles(inline_style)
            td_style = remove_style_prop(td_style, 'display', 'grid-template-columns', 'gap')
            parent_cols = self._get_grid_columns(parent_classes)
            width_pct = int(100 / parent_cols) if parent_cols > 0 else 50
            td_style = merge_style(td_style, f"width:{width_pct}%;vertical-align:top;")
            self.output.append(f'<td style="{td_style}">')
            return

        # === Flex Row → Table Row 转换 ===
        if self._is_flex_row(classes):
                # 独立的 flex 行，输出 <table><tr>
                table_style = filter_wechat_styles(inline_style)
                table_style = remove_style_prop(table_style, 'display', 'flex', 'gap', 'align-items',
                                            'justify-content', 'margin-bottom', 'padding-bottom',
                                            'border-bottom')
                self.output.append(f'<table style="width:100%;border-collapse:collapse;{table_style}"><tr>')
                return

        # === Flex Row 内子元素 → td 转换 ===
        # 检查父元素是否是 flex 行
        parent_classes_check = []
        if len(self.element_stack) >= 2:
            parent_classes_check = self.element_stack[-2].get('classes', [])
        if self._is_flex_row(parent_classes_check):
            td_style = filter_wechat_styles(inline_style)
            self.output.append(f'<td style="{td_style}">')
            return

        # === 普通元素 ===
        inline_style = filter_wechat_styles(inline_style)

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

        if not self.element_stack:
            return

        original_tag = self.element_stack[-1]['tag']
        classes = self.element_stack[-1]['classes']

        # === Grid → Table 关闭 ===
        if self._is_grid_container(classes):
            self.output.append('</tr></table>')
            self.element_stack.pop()
            return

        # === Grid 子元素 → td 关闭 ===
        parent_classes = []
        if len(self.element_stack) >= 2:
            parent_classes = self.element_stack[-2].get('classes', [])
        if self._is_grid_container(parent_classes):
            self.output.append('</td>')
            # 检查是否需要换行（3列 grid，每3个 td 换一行）
            parent_cols = self._get_grid_columns(parent_classes)
            # 计算当前是第几个 td（通过统计之前关闭的兄弟 td 数量）
            # 简化：每次关闭 td 后，检查下一个兄弟是否需要新的 <tr>
            # 这里无法预知，用后处理解决
            self.element_stack.pop()
            return

        # === Flex Row → Table 关闭 ===
        if self._is_flex_row(classes):
            parent_classes = []
            if len(self.element_stack) >= 2:
                parent_classes = self.element_stack[-2].get('classes', [])
            if self._is_grid_container(parent_classes):
                # flex row 在 grid 内，不需要额外处理
                pass
            else:
                self.output.append('</tr></table>')
            self.element_stack.pop()
            return

        # === Flex Row 内子元素 → td 关闭 ===
        parent_classes_check = []
        if len(self.element_stack) >= 2:
            parent_classes_check = self.element_stack[-2].get('classes', [])
        if self._is_flex_row(parent_classes_check):
            self.output.append('</td>')
            self.element_stack.pop()
            return

        tag = self._should_convert_to_section(original_tag, classes)
        self.output.append(f"</{tag}>")
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
        # 后处理：修复 grid table 的换行（3列 grid 需要在每3个 td 后插入 </tr><tr>）
        result = self._fix_grid_table_rows(result)
        result = resolve_css_vars(result)
        result = result.replace("<br></br>", "<br />")
        result = result.replace("</br>", "")
        result = result.replace("</img>", "")
        return result

    def _fix_grid_table_rows(self, html: str) -> str:
        """修复 grid table 的换行：在每 N 个 </td> 后插入 </tr><tr>"""
        # 用正则匹配 grid table，对其中的 td 进行换行处理
        def fix_one_table(m):
            table_content = m.group(0)
            # 统计 td 数量
            td_count = table_content.count('<td style="')
            if td_count <= 1:
                return table_content
            cols = 3 if td_count == 3 else 2
            # 在每 cols 个 </td> 后插入 </tr><tr>
            parts = table_content.split('</td>')
            if len(parts) <= cols + 1:
                return table_content
            new_parts = [parts[0]]  # <table...><tr>
            for i, part in enumerate(parts[1:], 1):
                new_parts.append('</td>')
                new_parts.append(part)
                if i % cols == 0 and i < td_count:
                    new_parts.append('</tr><tr>')
            return ''.join(new_parts)

        # 匹配 grid table（border-collapse:separate 标识）
        pattern = r'<table style="width:100%;border-collapse:separate;border-spacing:12px 0;[^"]*"><tr>.*?</tr></table>'
        return re.sub(pattern, fix_one_table, html, flags=re.DOTALL)


def extract_css_from_html(html_content: str) -> str:
    style_pattern = re.compile(r'<style[^>]*>(.*?)</style>', re.DOTALL | re.IGNORECASE)
    css_text = ""
    for match in style_pattern.finditer(html_content):
        css_text += "\n" + match.group(1)
    return css_text


def _extract_grid_columns(css_rules):
    """从 CSS 规则中提取 grid 容器的列数"""
    grid_cols = {}
    for rule in css_rules:
        for sel_path in rule.selector_paths:
            if len(sel_path) == 1:
                cls = sel_path[0].get('classes', [])
                for c in cls:
                    if c in GRID_CONTAINERS:
                        for prop in rule.declarations.split(';'):
                            if 'grid-template-columns' in prop:
                                val = prop.split(':')[1].strip()
                                cols = [x for x in val.split() if x]
                                grid_cols[c] = len(cols)
    return grid_cols


def convert_html_to_wechat(html_content: str) -> str:
    css_text = extract_css_from_html(html_content)
    css_rules = parse_css_rules(css_text)
    converter = WeChatHTMLConverter(css_rules)
    # 注入 grid 列数信息
    converter._grid_cols = _extract_grid_columns(css_rules)
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
